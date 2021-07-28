import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as om
import maya.api.OpenMaya as om2

import glob
import json


# GENERAL TOOLS

def parent_in_list_order(item_list):
    """
    Parent in list order
    :param item_list:
    :return:
    """
    for z, i in enumerate(item_list):
        mc.parent(item_list[z + 1], i)

        if z+1 >= len(item_list)-1:
            break


# JOINT TOOLS

def joint_on_curve_parameter(curve, parameter, name):
    position = mc.pointOnCurve(curve, parameter=parameter)
    mc.select(clear=True)
    joint = mc.joint(name=name)
    mc.xform(joint, translation=position, worldSpace=True)

    return joint


# FOLLICLE TOOLS

def vertex_position_from_id(vertex_id, geo):
    pass


# def follicle_on_vertex_from_ids(id_list, geo, flc_base_name):
#     # get geo
#     sel = om2.MSelectionList()
#     sel.add(geo)
#
#     # get vertices
#     dag, m_object = sel.getComponent(0)
#     mfn_components = om2.MFnSingleIndexedComponent(m_object)
#     mfn_object = mfn_components.create(om2.MFn.kMeshVertComponent)
#     mfn_components.addElements(id_list)


def follicle_on_vertex(vtx, flc_name):
    """
    Creates follicle based on vertex position, and relative UV coordinate.
    :param vtx:
    :param flc_name:
    :return follicle:
    """
    point = mc.xform(vtx, q=1, t=1)
    geo = vtx.split('.')[0]
    geo_shape = mc.listRelatives(geo, s=True)

    uv_value = get_uv_at_point(point, geo)
    follicle = create_follicle(geo_shape, u_val=uv_value[0], v_val=uv_value[1], name=flc_name)

    return follicle


def get_uv_at_point(point, geo):
    """
    Returns UV value at point on geo surface
    Open Maya 2 function
    :return (U, V):
    """
    m_point = om2.MPoint(point[0], point[1], point[2])

    m_sel_list = om2.MSelectionList()
    m_sel_list.add(geo)

    md_path = m_sel_list.getDagPath(0)
    fn_mesh = om2.MFnMesh(md_path)

    uv_value = fn_mesh.getUVAtPoint(m_point, om2.MSpace.kObject)

    return [uv_value[0], uv_value[1]]


def create_follicle(input_surface, scale_grp='', u_val=0.5, v_val=0.5, hide=0, name='follicle'):
    """
    Creates follicle on nurbs surface or geo
    :param input_surface: shape node
    :param scale_grp:
    :param u_val:
    :param v_val:
    :param hide:
    :param name:
    :return follicle transform:
    """
    # Create a follicle
    follicle_shape = mc.createNode('follicle')
    # Get the transform of the follicle
    follicle = mc.listRelatives(follicle_shape, parent=True)[0]
    # Rename the follicle
    follicle = mc.rename(follicle, name)
    follicle_shape = mc.rename(mc.listRelatives(follicle, c=True)[0], (name + 'Shape'))

    # If the inputSurface is of type 'nurbsSurface', connect the surface to the follicle
    if mc.objectType(input_surface[0]) == 'nurbsSurface':
        mc.connectAttr((input_surface[0] + '.local'), (follicle_shape + '.inputSurface'))
    # If the inputSurface is of type 'mesh', connect the surface to the follicle
    if mc.objectType(input_surface[0]) == 'mesh':
        mc.connectAttr((input_surface[0] + '.outMesh'), (follicle_shape + '.inputMesh'))

    # Connect the worldMatrix of the surface into the follicleShape
    mc.connectAttr((input_surface[0] + '.worldMatrix[0]'), (follicle_shape + '.inputWorldMatrix'))
    # Connect the follicleShape to it's transform
    mc.connectAttr((follicle_shape + '.outRotate'), (follicle + '.rotate'))
    mc.connectAttr((follicle_shape + '.outTranslate'), (follicle + '.translate'))
    # Set the uValue and vValue for the current follicle
    mc.setAttr((follicle_shape + '.parameterU'), u_val)
    mc.setAttr((follicle_shape + '.parameterV'), v_val)
    # Lock the translate/rotate of the follicle
    mc.setAttr((follicle + '.translate'), lock=True)
    mc.setAttr((follicle + '.rotate'), lock=True)

    # If it was set to be hidden, hide the follicle
    if hide:
        mc.setAttr((follicle_shape + '.visibility'), 0)
    # If a scale-group was defined and exists
    if scale_grp and mc.objExists(scale_grp):
        # Connect the scale-group to the follicle
        mc.connectAttr((scale_grp + '.scale'), (follicle + '.scale'))
        # Lock the scale of the follicle
        mc.setAttr((follicle + '.scale'), lock=True)

    return follicle


def get_geo_vertex_weights(geo_name, skin_cluster, threshold_value=0.001):
    """
    Gets the skin percentage in each vertex of the mesh and
    returns in a dictionary.

    :param geo_name:
    :param skin_cluster:
    :param threshold_value:
    :return:
    """
    # remember to filterExpand list before passing it in
    vertex_dict = {}

    vertex_count = mc.polyEvaluate(geo_name, vertex=True)
    vertex_list = ['{}.vtx[{}]'.format(geo_name, vertex_id) for vertex_id in range(vertex_count)]

    for vertex in vertex_list:
        influence_value_list = mc.skinPercent(
            skin_cluster,
            vertex,
            query=True,
            value=True,
            ignoreBelow=threshold_value
        )

        influence_name_list = mc.skinPercent(
            skin_cluster,
            vertex,
            transform=None,
            query=True,
            ignoreBelow=threshold_value
        )

        vertex_dict[vertex] = zip(influence_name_list, influence_value_list)

    return vertex_dict


class SkinWeightsManager:

    def __init__(self, dir_path, geo_list):
        """
        data structure
        {mesh:
            {skin_cluster_name: 'name',
            influence_list: ['joint1', 'joint2', ...],
            vertex_influence_dict: {influence(joint): weight, ...}

        :param dir_path:
        :param geo_list:
        """
        self.dir_path = dir_path
        self.geo_list = geo_list
        self.file_name = None

        self.file_list_in_path = None

    def import_weights_from_file(self):
        self.file_list_in_path = glob.glob('{dir}/*.json'.format(dir=self.dir_path))

        # iterate through all skin_weights file in directory
        for file in self.file_list_in_path:
            skin_data_dict = read_json_file(file)

            # in the file - go through the data for each mesh
            for mesh_name in skin_data_dict:
                skin_cluster_name = skin_data_dict[mesh_name]['skin_cluster_name']
                influence_list = skin_data_dict[mesh_name]['influence_list']
                vertex_weights = skin_data_dict[mesh_name]['vertex_weights']

                # bind influences to mesh
                if not mc.objExists(skin_cluster_name):
                    mc.skinCluster(influence_list,
                                   mesh_name,
                                   name=skin_cluster_name,
                                   toSelectedBones=True,
                                   bindMethod=0,
                                   skinMethod=0,
                                   normalizeWeights=1)

                set_skin_percentage_from_data(skin_cluster_name, vertex_weights)

    def export_selection_skin_weights(self, file_name):
        self.file_name = file_name

        # declare main dictionary
        output_dictionary = {}

        # enter loop geo
        for geo in self.geo_list:
            # get skin cluster
            skin_cluster = mel.eval('findRelatedSkinCluster "{}"'.format(geo))
            # get all skin cluster influences names
            skin_cluster_influence_list = mc.skinCluster(skin_cluster, query=True, influence=True)
            # run get skin weights function
            geo_weights_dict = get_geo_vertex_weights(geo, skin_cluster)

            # add geo weights to main dictionary
            output_dictionary.update({geo: {}})
            output_dictionary[geo].update({'vertex_weights': geo_weights_dict})
            output_dictionary[geo].update({'influence_list': skin_cluster_influence_list})
            output_dictionary[geo].update({'skin_cluster_name': skin_cluster})

        # do function export
        export_dict_as_json(output_dictionary, self.file_name, self.dir_path)


def export_selected_geo_weights(data_dict, file_path):

    with open(file_path, 'w') as file_for_write:
        json.dump(data_dict, file_for_write, indent=4)


def export_dict_as_json(data_dict, file_name, dir_path):

    full_path = '{dir}{file}.json'.format(dir=dir_path, file=file_name)
    print(full_path)

    with open(full_path, 'w') as file_for_write:
        json.dump(data_dict, file_for_write, indent=4)


def set_skin_percentage_from_data(skin_cluster_name, vertex_influence_weight_dict):
    """
    Import skin_cluster to individual geo pieces.
    skin_cluster must exist already.

    :param skin_cluster_name:
    :param vertex_influence_weight_dict:
    :return:
    """

    for vertex in vertex_influence_weight_dict:

        mc.skinPercent(skin_cluster_name,
                       vertex,
                       transformValue=vertex_influence_weight_dict[vertex],
                       zeroRemainingInfluences=True)

        print('Done with {}'.format(vertex))


def read_json_file(file_path):
    """
    Return dictionary from json file.
    :param file_path: directory path + file name
    :return:
    """
    try:
        with open(file_path, 'r') as jsonFile:
            return json.load(jsonFile)

    except RuntimeError:
        mc.error("Could not read {0}".format(file_path))