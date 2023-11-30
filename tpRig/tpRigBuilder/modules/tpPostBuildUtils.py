import os
import glob
import math

import maya.mel as mel
import maya.cmds as mc
import maya.cmds as cmds

import tpRig.tpRigBuilder.tpModule as tpModule
import tpRig.tpRigUtils as tpUtils
reload(tpUtils)
import tpRig.tpControl.tpControl as tpCtrl
reload(tpCtrl)
import tpRig.tpRigBuilder.tpProject as tpProject


"""
TO BE OR NOT TO BE?

- Should we have a parent class that will hold all project information
- And essentially go back to the previews form or class organization
- But this time a more focused on single modules
- Instead of all modules inherit from each other and make a big spagheti mess?

- What are the downsides of building the module from within?

- How would the inheritance layers look like?
    - Module (how to diferenciate the name?) 
        - Holds data attributes - Data has to be handled by Database Class outside
        - Connection points to other modules
        - Ways to store and retrieve data about modules
        - Action registration methods (Should this be external?)
    - Project
        - Holds information about the project structure
        - File paths
        - Directories in the project
    - Module Builder
        - Holds methods responsible of building and passing on the module to the UI
        
    - Rig Hierarchy
        - Holds information about rig structure hierarchy
        - Methods to parent items to its correct positions in the rig
    - Rig Tags
        - Holds methods for tag creation and tag management - Has to be external as well to handle all
    - Rig Module (Further segmentation)
        - Would hold information about rig parts to be built
        - Top and Bottom FK joints
        - Points of connection
        - No touch null
        

"""


class PostBuildUtils(tpProject.Project):

    def __init__(self):
        super(PostBuildUtils, self).__init__()
        # def om_export_model_geo_skin_weights(self):
        #     """
        #     Queries all geometry in 'model_geo_grp'
        #     Exports skin weights file using om_export_skin_weights.
        #     :return:
        #     """
        #     file_name = 'skin_cluster_001'  # hard coded, must be variable
        #     geo_grp = self.group_hierarchy_dict['model_geometry']
        #     all_children = mc.listRelatives(geo_grp, children=True, allDescendents=True, type='transform')
        #     geometry_list = [child for child in all_children if mc.listRelatives(child, type='shape')]
        #     skinned_geo_list = [geo for geo in geometry_list if mel.eval('findRelatedSkinCluster "{}"'.format(geo))]
        #
        #     self.om_export_skin_weights(skinned_geo_list,
        #                                 self.project_dir_dict['skin_clusters_model'],
        #                                 file_name)
        pass

    def om_export_model_geo_skin_weights(self):
        """
        Queries all geometry in 'model_geo_grp'
        Exports skin weights file using om_export_skin_weights.
        :return:
        """
        file_name = self.project_data_file_dict['model_geo_skin_weights']
        geo_grp = self.group_hierarchy_dict['model_geometry']
        all_children = mc.listRelatives(geo_grp, children=True, allDescendents=True, type='transform')
        geometry_list = [child for child in all_children if mc.listRelatives(child, type='shape')]
        skinned_geo_list = [geo for geo in geometry_list if mel.eval('findRelatedSkinCluster "{}"'.format(geo))]

        self.om_export_skin_weights(skinned_geo_list,
                                    self.project_dir_dict['skin_clusters_model'],
                                    file_name)

    def om_export_template_geo_skin_weights(self):
        """
        Queries all geometry in 'template_geo_grp'
        Exports skin weights file using om_export_skin_weights.
        :return:
        """
        file_name = self.project_data_file_dict['template_geo_skin_weights']
        geo_grp = self.group_hierarchy_dict['template_geometry']
        all_children = mc.listRelatives(geo_grp, children=True, allDescendents=True, type='transform')
        geometry_list = [child for child in all_children if mc.listRelatives(child, type='shape')]
        skinned_geo_list = [geo for geo in geometry_list if mel.eval('findRelatedSkinCluster "{}"'.format(geo))]

        self.om_export_skin_weights(skinned_geo_list,
                                    self.project_dir_dict['skin_clusters_template'],
                                    file_name)

    def om_export_system_skin_weights(self):
        """
        Export all skin weights for meshes added to self.system_mesh_weight_dict.
        Exports skin weights file using om_export_skin_weights.
        :return:
        """

        for module in self.system_mesh_weight_dict:
            file_name = '{}_weights'.format(module)
            geometry_list = self.system_mesh_weight_dict[module]
            skinned_geo_list = [geo for geo in geometry_list if mel.eval('findRelatedSkinCluster "{}"'.format(geo))]

            self.om_export_skin_weights(skinned_geo_list,
                                        self.project_dir_dict['skin_clusters_system'],
                                        file_name)

    def rename_skin_cluster_nodes(self):
        """
        Queries all skinclusters in the scene and name it according to the transform node name
        :return:
        """
        skin_cluster_list = mc.ls(type='skinCluster')

        for skin_cluster in skin_cluster_list:
            geo_name = mc.listConnections('{}.outputGeometry'.format(skin_cluster), d=True)[0]
            mc.rename(skin_cluster, '{}_skc'.format(geo_name))

    def export_control_shapes(self):
        """
        Exports controls shapes based on the control objects that have been created
        during the build process.

        Obs. 14.11.2022 - This feature should be inside of the class, or in a control manager
        class - Having it outside of the class just makes the system broken, considering that
        if we had to transfer this function to another project, this feature wouldn't be
        available.

        :return:
        """

        all_controls_data_dict = {}

        for control in self.control_object_dict:
            shape_dict = self.control_object_dict[control].get_position_data()

            control_data = {
                'curve_color': self.control_object_dict[control].get_curve_color(),
                'curve_form': self.control_object_dict[control].get_shape_type(),
                'shape_data': shape_dict
            }

            all_controls_data_dict.update({control: control_data})

        tpUtils.export_dict_as_json(all_controls_data_dict,
                                    self.project_data_file_dict['control_shape'],
                                    self.project_dir_dict['control_shape'])

        print('[File Exported] {}{}.json'.format(self.project_data_file_dict['control_shape'],
                                                 self.project_dir_dict['control_shape']))

    def control_set_form(self):
        control_list = mc.ls(selection=True)

        if not control_list:
            print('Please select controls')
            return

        # get control objects
        control_object_list = [self.control_object_dict[control_name] for control_name in control_list]
        # get type list
        shape_form_list = control_object_list[0].list_available_shapes()
        # print type list
        print(shape_form_list)
        # prompt user
        result = mc.promptDialog(
            title='Choose Shape Form',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if result == 'OK':
            shape_form = mc.promptDialog(query=True, text=True)

            for control_object in control_object_list:
                control_object.set_type(shape_form)

    def control_set_color_preset(self):
        control_list = mc.ls(selection=True)

        if not control_list:
            print('Please select controls')
            return

        # get control objects
        control_object_list = [self.control_object_dict[control_name] for control_name in control_list]
        # get type list
        color_preset_list = control_object_list[0].get_color_preset_list()
        # print type list
        print(color_preset_list)
        # prompt user
        result = mc.promptDialog(
            title='Choose Color Preset',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if result == 'OK':
            color_preset = mc.promptDialog(query=True, text=True)

            for control_object in control_object_list:
                control_object.set_color_preset(color_preset)

    def control_mirror_selected(self):
        control_selection = mc.ls(sl=True)

        for control in control_selection:
            opposite_control = control.replace('l_', 'r_')

            control_object = self.control_object_dict[control]
            opposite_control_object = self.control_object_dict[opposite_control]

            control_data = control_object.get_position_data(world_space=True)
            opposite_control_data = {}

            for shape_name in control_data:
                opposite_shape_name = shape_name.replace('l_', 'r_', 1)
                vertex_mirror_position_list = []

                for vertex_position in control_data[shape_name]:
                    mirror_position = [vertex_position[0] * -1, vertex_position[1], vertex_position[2]]
                    vertex_mirror_position_list.append(mirror_position)
                opposite_control_data.update({opposite_shape_name: vertex_mirror_position_list})

            opposite_control_object.restore_shape_position_from_data(opposite_control_data, world_space=True)

    def store_new_control_shape_preset(self):
        curve_transform = mc.ls(sl=True)

        result = mc.promptDialog(
            title='New Control Form Preset Name',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if result == 'OK':
            control_preset_name = mc.promptDialog(query=True, text=True)

            new_preset_control_obj = tpCtrl.Control(name='temp_control_curve')
            new_preset_control_obj.store_new_shape_form(control_preset_name, curve_transform)

    def assign_arnold_shaders(self):
        mesh_shader_dict = {
            'head_model_geo': 'head_model_geo_aiMat',
            'eye_ball_lens_left_geo': 'eye_cornea_aiMat',
            'eye_ball_lens_right_geo': 'eye_cornea_aiMat',
            'eye_ball_real_time_left_geo': 'eye_iris_aiMat',
            'eye_ball_real_time_right_geo': 'eye_iris_aiMat',
            'teeth_geo': 'teeth_geo_aiMat',
            'tongue_geo': 'tongue_geo_aiMat'
        }
        shader_path = glob.glob('{}*.mb'.format(self.project_dir_dict['shader_arnold']))[0]
        mc.file(shader_path, i=True)

        for geo in mesh_shader_dict:
            mc.select(geo, replace=True)
            mc.hyperShade(assign=mesh_shader_dict[geo])

    def import_arnold_light_set(self):
        pass

    def weights_from_set_b_to_a(self):
        weights_from_list_b_to_a_closest(self.vertex_set_b, self.vertex_set_a)

    def register_set_a(self):
        self.vertex_set_a = mc.ls(sl=True)

    def register_set_b(self):
        self.vertex_set_b = mc.ls(sl=True)

    def add_missing_influences(self):
        add_unexisting_influences_a_to_b(self.vertex_set_b, self.vertex_set_a)


def get_top_hierarchy_node(item_list):
    top_node_list = []

    for node in item_list:
        node_full_path = mc.ls(node, long=True)[0]
        top_parent_node = node_full_path.split('|')[1]

        if top_parent_node not in top_node_list:
            top_node_list.append(top_parent_node)

    return top_node_list


def import_and_return_node_type(file_path, node_type):
    """
    Imports a file and return all nodes of 'type'
    :param file_path:
    :param node_type:
    :return:
    """
    name_space = 'file_import'
    mc.file(file_path, i=True, namespace=name_space)

    node_type_list_namespace = mc.ls('{}:*'.format(name_space), type=node_type)
    node_type_list = [node.replace('{}:'.format(name_space), '') for node in node_type_list_namespace]

    mc.namespace(removeNamespace=name_space, mergeNamespaceWithRoot=True)

    return node_type_list


def find_closest_vertex(reference_vertex, vertex_list):
    """
    Finds closest vertex to reference vertex in provided list

    :reference_vertex: vertex to be compared to all vertex in provided list
    :vertex_list: list to compare with reference_vertex

    :return: vertex with smallest distance from reference_vertex from provided vertex_list
    """

    vertex_distance_dict = {}
    # get reference vertex position
    ref_vert_pos = cmds.xform(reference_vertex, query=True, translation=True, worldSpace=True)

    for vertex in vertex_list:
        # gets the position of correct vertex in list
        position = cmds.xform(vertex, query=True, translation=True, worldSpace=True)
        # finds euclidean distance between the two points
        distance = math.sqrt((ref_vert_pos[0] - position[0]) ** 2 + (ref_vert_pos[1] - position[1]) ** 2 + (
                ref_vert_pos[2] - position[2]) ** 2)

        # updates dictionary with information
        vertex_distance_dict.update({distance: vertex})

    # finds smallest value on listed distances
    closest_distance = min(vertex_distance_dict.keys())

    return vertex_distance_dict[closest_distance]


def weights_from_list_b_to_a_closest(list_a, list_b):
    """
    Loops through all vertices in list A, finds the closest vertex in list B
    and copies the weights from B to A.

    Both vertex list must be in the same mesh.

    :list_a: List of vertices to get new skin weights
    :list_b: List of vertices to provide the skinning information
    """

    for vertex in list_a:
        closest_in_b = find_closest_vertex(vertex, list_b)

        cmds.select(closest_in_b, r=True)
        mel.eval('artAttrSkinWeightCopy')

        cmds.select(vertex, r=True)
        mel.eval('artAttrSkinWeightPaste')

    print("[Copy Skin Weights From List A to B] Process Completed - Success")


# vert_list_a = cmds.ls(selection=True, flatten=True)
# vert_list_b = cmds.ls(selection=True, flatten=True)

# weights_from_list_b_to_a_closest(vert_list_a, vert_list_b)


def add_unexisting_influences_a_to_b(vert_list_a, vert_list_b):
    influence_list_b = []
    for vertex in vert_list_b:
        skincluster = mel.eval('findRelatedSkinCluster {};'.format(vertex.split('.')[0]))
        influence_query_list = cmds.skinPercent(skincluster, vertex, query=True, transform=None)

        for influence in influence_query_list:
            if influence not in influence_list_b:
                influence_list_b.append(influence)

    influence_list_a = []
    for vertex in vert_list_a:
        skincluster = mel.eval('findRelatedSkinCluster {};'.format(vertex.split('.')[0]))
        influence_query_list = cmds.skinPercent(skincluster, vertex, query=True, transform=None)

        for influence in influence_query_list:
            if influence not in influence_list_a:
                influence_list_a.append(influence)

    unexisting_influences = [influence for influence in influence_list_a if influence not in influence_list_b]

    print(
        "[add_unexisting_influences_a_to_b] Adding Unexistent Influences to '{}'".format(vert_list_b[0].split('.')[0]))

    b_skin_cluster = mel.eval('findRelatedSkinCluster {};'.format(vert_list_b[0].split('.')[0]))
    for influence in unexisting_influences:
        cmds.skinCluster(
            b_skin_cluster,
            edit=True,
            useGeometry=True,
            dropoffRate=4,
            polySmoothness=0,
            nurbsSamples=10,
            lockWeights=True,
            weight=0,
            addInfluence=influence)

    print("[add_unexisting_influences_a_to_b] Process Successful")

    return unexisting_influences


def build_module_object(module_name='Post-Build Utilities', parent_action_name='root', background_color=None):
    post_utils_obj = PostBuildUtils()

    post_utils_mod_obj = tpModule.Module(module_name, parent_action_name, background_color=background_color)

    action_list = [
        tpModule.Action('Control Tools', 'Post-Build Utilities'),
        tpModule.Action('Export Control Shapes', 'Control Tools', post_utils_obj.export_control_shapes),
        tpModule.Action('Control Set Shape Form', 'Control Tools', post_utils_obj.control_set_form),
        tpModule.Action('Control Set Color Preset', 'Control Tools', post_utils_obj.control_set_color_preset),
        tpModule.Action('Control Mirror Selected', 'Control Tools', post_utils_obj.control_mirror_selected),
        tpModule.Action('Control Store New Preset Form', 'Control Tools',
                        post_utils_obj.store_new_control_shape_preset),

        tpModule.Action('Skin Tools', 'Post-Build Utilities'),
        tpModule.Action('Rename All SkinCluster Nodes', 'Skin Tools', post_utils_obj.rename_skin_cluster_nodes),
        # tpModule.Action('OM Export Skin Weights', 'Skin Tools', post_utils_obj.om_export_skin_weights),
        # tpModule.Action('OM Import Skin Weights', 'Skin Tools', post_utils_obj.om_import_skin_weights),
        tpModule.Action('OM Export Model Geo Weights', 'Skin Tools',
                        post_utils_obj.om_export_model_geo_skin_weights),
        tpModule.Action('OM Export Template Geo Weights', 'Skin Tools',
                        post_utils_obj.om_export_template_geo_skin_weights),
        tpModule.Action('OM Export System Weights', 'Skin Tools',
                        post_utils_obj.om_export_system_skin_weights),

        tpModule.Action('Import And Assign Arnold Shaders', 'Post-Build Utilities',
                        post_utils_obj.assign_arnold_shaders),

        tpModule.Action('Transfer Weights Set B to A', 'Skin Tools', post_utils_obj.weights_from_set_b_to_a),
        tpModule.Action('Register Set A', 'Transfer Weights Set B to A', post_utils_obj.register_set_a),
        tpModule.Action('Register Set B', 'Transfer Weights Set B to A', post_utils_obj.register_set_b),
        tpModule.Action('Transfer Missing Weights', 'Transfer Weights Set B to A',
                        post_utils_obj.add_missing_influences)
    ]

    post_utils_mod_obj.add_action_list(action_list)

    return post_utils_mod_obj

