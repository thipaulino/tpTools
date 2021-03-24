import maya.cmds as mc
import maya.OpenMaya as om
import maya.api.OpenMaya as om2


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

