from __future__ import division
import maya.cmds as mc
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as OpenMayaUI
import importlib
import json
import struct
import glob
import math
import os


# -------------------------------------------------------------------------------
# Name:        tp_utilityTools v4
# Purpose:     Code snippets, further to be added in a interface
#
# Author:      Thiago Paulino
# Location:    Vancouver, BC
# Contact:     tpaulino.com@gmail.com
#
# Created:     10/23/2019
# Copyright:   (c) Thiago Paulino 2019
# Licence:     MIT
# -------------------------------------------------------------------------------


# FOLLICLE SECTION __________________________________________________________________

def follicle_on_closest_point(surface, locator_list, name=""):

    surface_shape = cmds.listRelatives(surface, type="shape")[0]
    follicle_dict = {}
    closest_point_node_list = []
    set_range_node_list = []

    for n, loc in enumerate(locator_list):
        # Create Point on Curve Info node
        closest_point_node = cmds.createNode("closestPointOnSurface", n="{}_{:02d}_closestPointOnSrf")
        closest_point_node_list.append(closest_point_node)
        # Create follicle on surface
        follicle_data = create_follicle(input_surface=[surface_shape], hide=0, name="{}_{:02d}_Flc".format(name, n))
        follicle_dict.update({follicle_data['transform']: follicle_data['shape']})

        # Connect surface to pci
        cmds.connectAttr(surface_shape + ".local", closest_point_node + ".inputSurface", f=1)
        # Connect locator to pci
        cmds.connectAttr(loc + ".translate", closest_point_node + ".inPosition")

        # Create set range for parameterV
        set_range_node = cmds.shadingNode("setRange", asUtility=1, n="{}_{:02d}_setRange".format(name, n))
        set_range_node_list.append(set_range_node)
        # Get surface max U and V parameters
        cmds.connectAttr(surface_shape + ".maxValueV", set_range_node + ".oldMaxX")
        cmds.connectAttr(surface_shape + ".maxValueU", set_range_node + ".oldMaxY")
        cmds.setAttr(set_range_node + ".maxX", 1)
        cmds.setAttr(set_range_node + ".maxY", 1)
        # Connect pci to follicle
        cmds.connectAttr(closest_point_node + ".parameterV", set_range_node + ".valueX", f=1)
        cmds.connectAttr(closest_point_node + ".parameterU", set_range_node + ".valueY", f=1)
        cmds.connectAttr(set_range_node + ".outValueX", follicle_data['shape'] + ".parameterV")
        cmds.connectAttr(set_range_node + ".outValueY", follicle_data['shape'] + ".parameterU")

    return follicle_dict, closest_point_node_list, set_range_node_list


def connect_locator_to_crv(loc_list, crv):

    for loc in loc_list:
        loc_pos = cmds.xform(loc, q=1, ws=1, t=1)
        loc_u = getUParam(loc_pos, crv)
        pci_node_name = loc.replace("_loc", "_pci")
        pci_node = cmds.createNode("pointOnCurveInfo", n=pci_node_name)
        cmds.connectAttr(crv + ".worldSpace", pci_node + ".inputCurve")
        cmds.setAttr(pci_node + ".parameter", loc_u)
        cmds.connectAttr(pci_node + ".position", loc + ".t")


def locator_on_cv_set(path_crv):
    """
    Locator on CV's - Select curve, run script
    :param path_crv:
    :return:
    """
    cmds.select(cl=1)
    cv_list = cmds.getAttr(path_crv + '.cv[:]')
    locator_list = []

    for i, cv in enumerate(cv_list):
        locator = cmds.spaceLocator(n="{}_{:02d}_Loc".format(path_crv, i))
        cmds.xform(locator, t=cv)
        cmds.select(cl=1)

        locator_list.append(locator)

    return locator_list


def follicle_2d(surface='', rows=3, columns=3, width_percentage=1, height_percentage=1, name=""):
    """
    Distribute follicles in a 2D array of a polygon surface
    Distribute follicles on surface + joints and controls
    :param surface:
    :param rows:
    :param columns:
    :param width_percentage:
    :param height_percentage:
    :param name:
    :return:
    """
    # if columns/rows equals 1, position in center
    surface_u_step = 0.5 if columns == 1.0 else (100 / (columns - 1) / 100) * width_percentage
    surface_v_step = 0.5 if rows == 1.0 else (100 / (rows-1) / 100) * height_percentage
    # get selection - if there is no user input
    surface = surface if surface else cmds.ls(sl=1)[0]
    surface_shape = cmds.listRelatives(surface, type="shape")
    # declare lists
    follicle_list = []
    joint_list = []

    for i in range(int(columns)):
        for y in range(int(rows)):
            u_parameter = surface_u_step if columns == 1.0 else surface_u_step * i
            v_parameter = surface_v_step if rows == 1.0 else surface_v_step * y

            follicle_data = create_follicle(input_surface=surface_shape, u_val=u_parameter, v_val=v_parameter,
                                            name="{}_Flc_C{}_R{}".format(name, i, y), hide=0)
            joint = cmds.joint(n="{}_Jnt_C{}_R{}".format(name, i, y))

            follicle_position = cmds.xform(follicle_data['transform'], q=1, t=1)
            follicle_rotation = cmds.xform(follicle_data['transform'], q=1, ro=1)

            cmds.xform(joint, t=follicle_position, ro=follicle_rotation)
            cmds.parentConstraint(follicle_data['transform'], joint)

            follicle_list.append(follicle_data['transform'])
            joint_list.append(joint)

    joint_group = cmds.group(joint_list, n=name + "_Jnt_Grp")
    follicle_group = cmds.group(follicle_list, n=name + "_Flc_Grp")

    return {'groups': [joint_group, follicle_group],
            'joints': joint_list,
            'follicles': follicle_list}


def create_follicle(input_surface, scale_grp='', u_val=0.5, v_val=0.5, hide=1, name='follicle'):
    """
    Creates follicle on nurbs surface or geo
    :param input_surface:
    :param scale_grp:
    :param u_val:
    :param v_val:
    :param hide:
    :param name:
    :return follicle_data:
        dict {'transform': follicle transform,
              'shape': follicle shape}
    """
    # Create a follicle
    follicle_shape = cmds.createNode('follicle')
    # Get the transform of the follicle
    follicle = cmds.listRelatives(follicle_shape, parent=True)[0]
    # Rename the follicle
    follicle = cmds.rename(follicle, name)
    follicle_shape = cmds.rename(cmds.listRelatives(follicle, c=True)[0], (name + 'Shape'))

    # If the inputSurface is of type 'nurbsSurface', connect the surface to the follicle
    if cmds.objectType(input_surface[0]) == 'nurbsSurface':
        cmds.connectAttr((input_surface[0] + '.local'), (follicle_shape + '.inputSurface'))
    # If the inputSurface is of type 'mesh', connect the surface to the follicle
    if cmds.objectType(input_surface[0]) == 'mesh':
        cmds.connectAttr((input_surface[0] + '.outMesh'), (follicle_shape + '.inputMesh'))

    # Connect the worldMatrix of the surface into the follicleShape
    cmds.connectAttr((input_surface[0] + '.worldMatrix[0]'), (follicle_shape + '.inputWorldMatrix'))
    # Connect the follicleShape to it's transform
    cmds.connectAttr((follicle_shape + '.outRotate'), (follicle + '.rotate'))
    cmds.connectAttr((follicle_shape + '.outTranslate'), (follicle + '.translate'))
    # Set the uValue and vValue for the current follicle
    cmds.setAttr((follicle_shape + '.parameterU'), u_val)
    cmds.setAttr((follicle_shape + '.parameterV'), v_val)
    # Lock the translate/rotate of the follicle
    cmds.setAttr((follicle + '.translate'), lock=True)
    cmds.setAttr((follicle + '.rotate'), lock=True)

    # If it was set to be hidden, hide the follicle
    if hide:
        cmds.setAttr((follicle_shape + '.visibility'), 0)
    # If a scale-group was defined and exists
    if scale_grp and cmds.objExists(scale_grp):
        # Connect the scale-group to the follicle
        cmds.connectAttr((scale_grp + '.scale'), (follicle + '.scale'))
        # Lock the scale of the follicle
        cmds.setAttr((follicle + '.scale'), lock=True)

    return {'transform': follicle,
            'shape': follicle_shape}


def find_center():
    """
    Place locator in object center
    :return locator:
    """
    select = cmds.ls(sl=1)
    axis_x = axis_y = axis_z = 0

    for i in select:
        axis_x += cmds.xform(i, q=1, t=1)[0]
        axis_y += cmds.xform(i, q=1, t=1)[1]
        axis_z += cmds.xform(i, q=1, t=1)[2]

    axis_x_avg = axis_x/len(select)
    axis_y_avg = axis_y/len(select)
    axis_z_avg = axis_z/len(select)

    avg = [axis_x_avg, axis_y_avg, axis_z_avg]

    locator = cmds.spaceLocator()
    cmds.xform(locator, ws=1, t=avg)

    return locator


# JOINT SECTION __________________________________________________________________

def joint_on_selection_list():
    """
    Creates and places joints on each selection
    :return List of joints created:
    """

    selection = cmds.ls(sl=1)
    cmds.select(cl=1)
    joint_list = []

    for i in selection:
        translate = cmds.xform(i, q=1, t=1)
        rotate = cmds.xform(i, q=1, ro=1)
        scale = cmds.xform(i, q=1, s=1)

        new_joint = cmds.joint(n=i + "_Jnt")
        cmds.select(cl=1)
        cmds.xform(new_joint, t=translate, ro=rotate, s=scale)

        joint_list.append(new_joint)

    return joint_list


def joints_on_cv_set(path_crv):
    """
    Joints on CV's - Select curve, run script
    :param path_crv:
    :return joint_list:
    """
    cmds.select(cl=1)
    cv_list = cmds.getAttr(path_crv + '.cv[:]')
    joint_list = []

    for i, cv in enumerate(cv_list):
        joint = cmds.joint(n="{}_Jnt{}".format(path_crv, i))
        cmds.xform(joint, t=cv)
        cmds.select(cl=1)

        joint_list.append(joint)

    return joint_list


'''
# Zero/Offset/Space Joints 
jnt_list = cmds.ls(sl=1)

for i in jnt_list:
    point = cmds.xform(i, q=1, t=1)
    jnt_loc = cmds.spaceLocator(n=i + '_Loc')
    cmds.xform(jnt_loc, t=point)
    cmds.parent(i, jnt_loc)
    cmds.group(jnt_loc, n=jnt_loc[0] + '_Grp')
'''


def parent_in_order(sel, reverse=False):
    """
    Parent in selection order
    :param sel:
    :param reverse:
    """
    if reverse:
        sel.reverse()

    for z, i in enumerate(sel):
        cmds.parent(sel[z+1], i)

        if z+1 >= len(sel)-1:
            break


# CONTROL SECTION __________________________________________________________________

def build_ctrl(ctrl_type="circle", name="", suffix="_ctrl", scale=1, spaced=1, offset=0, normal=(1, 0, 0)):
    """
    ctrl_type - Cube, Sphere, Circle (add - square, pointer, arrow, spherev2)
    :param ctrl_type:
    :param name:
    :param suffix:
    :param scale:
    :param spaced:
    :param offset:
    :param normal:
    :return [ctrl, ctrl_grp, offset_ctrl_grp]:
    """
    control_data = {'control': '',
                    'group': '',
                    'offset_group': ''}

    if ctrl_type == "cube":
        control_data['control'] = cmds.curve(
            n=name + suffix,
            p=[(-1.0, 1.0, 1.0), (-1.0, 1.0, -1.0), (1.0, 1.0, -1.0),
               (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, -1.0, 1.0),
               (1.0, -1.0, 1.0), (1.0, -1.0, -1.0), (-1.0, -1.0, -1.0),
               (-1.0, -1.0, 1.0), (-1.0, -1.0, -1.0), (-1.0, 1.0, -1.0),
               (1.0, 1.0, -1.0), (1.0, -1.0, -1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0)],
            k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], d=1)

    elif ctrl_type == "sphere":
        control_data['control'] = cmds.circle(n=name + suffix, nr=(1, 0, 0), r=scale, ch=0)[0]
        c2 = cmds.circle(nr=(0, 1, 0), r=scale, ch=0)[0]
        c3 = cmds.circle(nr=(0, 0, 1), r=scale, ch=0)[0]

        cmds.parent(cmds.listRelatives(c2, s=True), cmds.listRelatives(c3, s=True),
                    control_data['control'], r=True, s=True)
        cmds.delete(c2, c3)

    elif ctrl_type == "circle":
        control_data['control'] = cmds.circle(n=name + suffix, nr=normal, r=scale, ch=0)[0]

    shapes = cmds.listRelatives(control_data['control'], f=True, s=True)
    for n, shape in enumerate(shapes):
        cmds.rename(shape, "{}Shape{:02d}".format(control_data['control'], n+1))

    if spaced == 1:
        control_data['group'] = cmds.group(control_data['control'], n=name + suffix + "_Grp")

    # Creates offset group for static control
    if offset == 1:
        control_data['offset_group'] = cmds.group(control_data['control'], n=name + suffix + "_Offset_Grp")
        multiply_divide_node = cmds.createNode('multiplyDivide')

        cmds.connectAttr(control_data['control'] + '.translate', multiply_divide_node + '.input1')
        cmds.connectAttr(multiply_divide_node + '.output', control_data['offset_group'] + '.translate')
        cmds.setAttr(multiply_divide_node + '.input2X', -1)
        cmds.setAttr(multiply_divide_node + '.input2Y', -1)
        cmds.setAttr(multiply_divide_node + '.input2Z', -1)

    return control_data


def place_on_selection(ctrl_type="circle", scale=1, spaced=1):
    """
    Control on each selection
    :param ctrl_type:
    :param scale:
    :param spaced:
    :return:
    """
    sel = cmds.ls(sl=1)

    for n, item in enumerate(sel):
        position = cmds.xform(item, q=1, t=1, ws=1)
        rotation = cmds.xform(item, q=1, ro=1, ws=1)

        control = build_ctrl(ctrl_type=ctrl_type, name=item, scale=scale, spaced=spaced)

        if spaced == 1:
            cmds.xform(control['group'], t=position, ro=rotation)
        else:
            cmds.xform(control['control'], t=position, ro=rotation)


def add_offset_grp_list(user_list):
    """
    Zero/Offset/Space controls
    """
    item_list = user_list if user_list else cmds.ls(sl=1)
    grp_dict = {}

    for item in item_list:
        grp = cmds.group(em=1, n="{}_grp".format(item))

        sel_t = cmds.xform(item, q=1, t=1)
        sel_ro = cmds.xform(item, q=1, ro=1)

        cmds.xform(grp, t=sel_t, ro=sel_ro)
        cmds.parent(item, grp)

        grp_dict.update({item: grp})

    return grp_dict


def add_offset_grp(user_item):
    """
    Zero/Offset/Space controls
    """
    item = user_item if user_item else cmds.ls(sl=1)

    grp = cmds.group(em=1, n="{}_grp".format(item))

    sel_t = cmds.xform(item, q=1, t=1, ws=1)
    sel_ro = cmds.xform(item, q=1, ro=1, ws=1)

    cmds.xform(grp, t=sel_t, ro=sel_ro)
    cmds.parent(item, grp)

    return grp


# def control_on_cv_list():
#     """
#     Controls on CV's
#     """
#     path_crv = cmds.ls(sl=1)[0]
#     cv_list = cmds.getAttr(path_crv + '.cv[:]')
#
#     for i, cv in enumerate(cv_list):
#         ctrl = tp_staticCtrl('ctrl_cv' + str(i))
#         cmds.xform(ctrl[1], t= cv)


def ctrl_on_cluster_set(ctrl_type="circle", scale=1, color=(1, 1, 1), parent_constraint=0):
    """
    Control on each Cluster selection
    :param ctrl_type:
    :param scale:
    :param color:
    :param parent_constraint:
    :return control_data{cluster_name: ctrl_data}:
    """
    sel = cmds.ls(sl=1)
    control_data = {}

    for n, cluster in enumerate(sel):
        # get cluster position
        cls_shape = cmds.listRelatives(cluster, type="shape")
        cls_tr = cmds.getAttr(cls_shape[0] + ".origin")[0]

        # create control
        ctrl_data = build_ctrl(ctrl_type=ctrl_type, name=cluster, suffix="{:02d}_ctrl".format(n),
                               scale=scale, spaced=True)
        set_ctrl_color(ctrl_data['control'], color=color)
        cmds.xform(ctrl_data['group'], t=cls_tr)
        control_data[cluster] = ctrl_data

        # constraint cluster to control
        if parent_constraint == 1:
            cmds.parentConstraint(ctrl_data['control'], cluster, mo=1)

    return control_data


def ctrl_on_joint_set(name, scale=1, color=(1, 1, 1), parent_constraint=0):
    """
    Control on each Joint selection
    :param name:
    :param scale:
    :param color:
    :param parent_constraint:
    :return:
    """
    sel = cmds.ls(sl=1)
    control_data = {}

    for n, joint in enumerate(sel):
        position = cmds.xform(joint, q=1, t=1, ws=1)
        rotation = cmds.joint(joint, q=1, o=1)

        new_ctrl = build_ctrl(ctrl_type="circle", name=name, suffix="_Ctrl{}".format(n),
                              scale=scale, spaced=1, offset=0)
        set_ctrl_color(new_ctrl['control'], color=color)
        cmds.xform(new_ctrl['group'], t=position, ro=rotation)
        control_data[joint] = new_ctrl

        if parent_constraint == 1:
            cmds.parentConstraint(new_ctrl['control'], joint, mo=1)

    return control_data


def parent_fk_order():
    """
    Parents in FK Order - Select Ctrl Group, Last to First
    """
    groups = cmds.ls(sl=1)
    ctrls = []

    for i in groups:
        ctrl = cmds.listRelatives(i)
        ctrls.append(ctrl)

    for y, z in enumerate(groups):
        cmds.parent(z, ctrls[y+1])
        if y+1 >= len(groups-1):
            break


def multi_set_color(color=(1, 1, 1)):
    """
    Set Control Color in Multiple Controls
    :param color:
    """
    sel = cmds.ls(sl=1)

    for i in sel:
        set_ctrl_color(ctrl=i, color=color)


def set_ctrl_color(ctrl, color=(1, 1, 1)):
    """
    Set control color
    :param ctrl:
    :param color:
    """
    rgb = ("R", "G", "B")

    cmds.setAttr(ctrl + ".overrideEnabled", 1)
    cmds.setAttr(ctrl + ".overrideRGBColors", 1)

    for channel, color in zip(rgb, color):

        cmds.setAttr("{}.overrideColor{}".format(ctrl, channel), color)


def place_ctrls_on_crv(name, amount):
    """
    place controls on curve
    :param name:
    :param amount:
    """
    crv = cmds.ls(sl=1)
    crv_step = 100 / (amount-1) / 100

    for i in range(int(amount)):
        parameter = crv_step * i
        position = get_point_on_curve(crv, parameter, 1)
        build_ctrl(name + str(i), position[0], position[1])


# GENERAL SECTION __________________________________________________________________
def get_point_on_curve(crv, parameter, inverse=0):
    """
    Gets position and rotation of point on curve using motion path
    :param crv:
    :param parameter:
    :param inverse:
    :return translation and rotation list:
    """
    poc_loc = cmds.spaceLocator(name='Poc_Temp_Loc')
    m_path_crv = cmds.duplicate(crv, name='mPath_Temp_Crv')[0]
    cmds.delete(m_path_crv, ch=1)

    m_path = cmds.pathAnimation(poc_loc, m_path_crv, n='mPath_Temp', fractionMode=1, followAxis='x', upAxis='y',
                                worldUpType='vector', inverseUp=inverse, inverseFront=inverse)
    cmds.disconnectAttr(m_path + '_uValue.output', m_path + '.uValue')
    cmds.setAttr(m_path + '.uValue', parameter)

    tr = cmds.xform(poc_loc, q=1, t=1)
    rt = cmds.xform(poc_loc, q=1, ro=1)
    point = [tr, rt]

    cmds.delete(m_path + '_uValue', m_path, poc_loc, m_path_crv)

    # point = [[t.x, t.y, t.z], [r.x, r.y, r.z]]
    return point


def multi_motion_path(name, amount, inverse=0):
    """
    Gets position and rotation of point on curve using motion path
    :param name:
    :param amount:
    :param inverse:
    """
    crv_step = 100 / (amount-1) / 100
    m_path_crv = cmds.ls(sl=1)
    cmds.select(cl=1)
    loc_list = []

    for i in range(int(amount)):
        parameter = crv_step * i
        loc = cmds.spaceLocator(n=name + '_loc' + str(i))
        m_path = cmds.pathAnimation(loc, m_path_crv, n=name + '_mPath' + str(i), fractionMode=1, followAxis='x',
                                    upAxis='y', worldUpType="vector", inverseUp=inverse, inverseFront=inverse)
        cmds.disconnectAttr(m_path + '_uValue.output', m_path + '.uValue')
        cmds.setAttr(m_path + '.uValue', parameter)

        loc_list.append(loc)

    cmds.group(loc_list)


def param_from_length(curve, count, curve_type="open", space="uv", normalized=True):
    """
    By Orkhan Ashrofov - Ribonizer
    :param curve:
    :param count:
    :param curve_type:
    :param space:
    :param normalized:
    :return:
    """
    if curve_type == "periodic":
        divider = count
    else:
        divider = count - 1

    if divider == 0:
        divider = 1

    dag = om.MDagPath()
    obj = om.MObject()
    crv = om.MSelectionList()
    crv.add(curve)
    crv.getDagPath(0, dag, obj)

    curve_fn = om.MFnNurbsCurve(dag)
    length = curve_fn.length()

    param = [curve_fn.findParamFromLength(i * ((1 / float(divider)) * length)) for i in range(count)]

    if space == "world":
        data = []
        space = om.MSpace.kWorld
        point = om.MPoint()
        for p in param:
            curve_fn.getPointAtParam(p, point, space)
            data.append([point[0], point[1], point[2]])  # world space points

    elif normalized is True:

        def normalizer(value, old_range, new_range):
            return (value - old_range[0]) * (new_range[1] - new_range[0]) / (old_range[1] - old_range[0]) + new_range[0]

        max_v = mc.getAttr(curve + ".minMaxValue.maxValue")
        min_v = mc.getAttr(curve + ".minMaxValue.minValue")

        # Normalized parameters (before i was just dividing p to max_v. but with weird ranges
        # (ie. 1.4281 to 6.98214) the result is of is not as expected.
        # this also could have been fixed by just rebuilding the surface uniformly)
        data = [normalizer(p, [min_v, max_v], [0, 1]) for p in param]
    else:
        data = param

    return data


def cube_over_geo():
    object_sel = cmds.ls(sl=1)[0]
    bbox = cmds.getAttr(object_sel + ".boundingBox.boundingBoxSize")[0]

    obj_copy = cmds.duplicate(object_sel, n="pivot_obj")

    cmds.xform(obj_copy, cp=1)
    obj_copy_tr = cmds.xform(obj_copy, q=1, piv=1)[:3]
    cmds.delete(obj_copy)
    bbox_cube = cmds.polyCube(w=bbox[0], h=bbox[1], d=bbox[2], sx=1, sy=1, sz=1, ch=0)
    cmds.xform(bbox_cube, t=obj_copy_tr)


def list_top_level():
    """
    List Top level nodes on Outliner
    :return:
    """
    nodes = mc.ls(assemblies=True)

    return nodes


def resize_image(source_image, output_image, width, height):
    """
    Image resize function
    resizeImage('<sourceImage.png>','<outputImage.png>', 800, 600)
    :param source_image:
    :param output_image:
    :param width:
    :param height:
    :return:
    """
    image = om.MImage()
    image.readFromFile(source_image)

    image.resize(width, height)
    image.writeToFile(output_image, 'png')


class UnknownImageFormat(Exception):
    pass


def get_image_size(file_path):
    """
    extract image dimensions given a file path using just core modules
    :author Paulo Scardine (based on code from Emmanuel VAISSE):
    :return (width, height):
    """
    size = os.path.getsize(file_path)

    with open(file_path) as input_img:
        height = -1
        width = -1
        data = input_img.read(25)

        if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
            # GIFs
            w, h = struct.unpack("<HH", data[6:10])
            width = int(w)
            height = int(h)
        elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
              and (data[12:16] == 'IHDR')):
            # PNGs
            w, h = struct.unpack(">LL", data[16:24])
            width = int(w)
            height = int(h)
        elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
            # older PNGs?
            w, h = struct.unpack(">LL", data[8:16])
            width = int(w)
            height = int(h)
        elif (size >= 2) and data.startswith('\377\330'):
            # JPEG
            msg = " raised while trying to decode as JPEG."
            input_img.seek(0)
            input_img.read(2)
            b = input_img.read(1)
            try:
                while b and ord(b) != 0xDA:
                    while ord(b) != 0xFF:
                        b = input_img.read(1)
                    while ord(b) == 0xFF:
                        b = input_img.read(1)
                    if ord(b) >= 0xC0 and ord(b) <= 0xC3:
                        input_img.read(3)
                        h, w = struct.unpack(">HH", input_img.read(4))
                        break
                    else:
                        input_img.read(int(struct.unpack(">H", input_img.read(2))[0])-2)
                    b = input_img.read(1)
                width = int(w)
                height = int(h)
            except struct.error:
                raise UnknownImageFormat("StructError" + msg)
            except ValueError:
                raise UnknownImageFormat("ValueError" + msg)
            except Exception as e:
                raise UnknownImageFormat(e.__class__.__name__ + msg)
        else:
            raise UnknownImageFormat(
                "Sorry, don't know how to get information from this file."
            )

    return width, height


# Add/Remove stuff from lattice
# cmds.sets("pSphere1", e=1, remove="ffd1Set")
# cmds.lattice("ffd1Lattice", e=1, rm=1, g="pSphere1")


def mirror_vertex_selection(vert_list, mesh):
    """
    Mirror selection translation values and feeds to getClosest function
    """
    vert_list = cmds.filterExpand(vert_list, sm=31)
    mirror_vert_list = []

    for vert in vert_list:
        vert_pos = cmds.xform(vert, q=1, t=1)
        mirror_pos = [(vert_pos[0] * -1), vert_pos[1], vert_pos[2]]
        mirror_vert_list.append(get_closest_vertex_v2(mesh, mirror_pos))

    # cmds.select(mirror_vert_list, r=1)

    return mirror_vert_list


def get_closest_vertex_v2(maya_mesh, pos=(0, 0, 0)):
    """
    Returns the closest vertex given a mesh and a position [x,y,z] in world space.
    Uses om2.MfnMesh.getClosestPoint() returned face ID and iterates through face's vertices
    """

    # Using MVector type to represent position
    m_vector = om2.MVector(pos)
    selection_list = om2.MSelectionList()
    selection_list.add(maya_mesh)
    d_path = selection_list.getDagPath(0)
    m_mesh = om2.MFnMesh(d_path)
    # Getting closest face ID
    face_id = m_mesh.getClosestPoint(om2.MPoint(m_vector), space=om2.MSpace.kWorld)[1]
    # Face's vertices list
    vert_list = cmds.ls(cmds.polyListComponentConversion('{}.f[{}]'.format(maya_mesh, face_id), ff=True, tv=True),
                        flatten=True)

    # Setting vertex [0] as the closest one
    dist_01 = om2.MVector(cmds.xform(vert_list[0], t=True, ws=True, q=True))
    smallest_dist = math.sqrt((dist_01.x - pos[0])**2 + (dist_01.y - pos[1])**2 + (dist_01.z - pos[2])**2)
    # Using distance squared to compare distance
    closest = vert_list[0]

    # Iterating from vertex [1]
    for i in range(1, len(vert_list)):
        dist_02 = om2.MVector(cmds.xform(vert_list[i], t=True, ws=True, q=True))
        euc_dist = math.sqrt((dist_02.x - pos[0])**2 + (dist_02.y - pos[1])**2 + (dist_02.z - pos[2])**2)

        if euc_dist <= smallest_dist:
            smallest_dist = euc_dist
            closest = vert_list[i]

    return closest


# Not in use
def get_closest_vertex(maya_mesh, pos=(0, 0, 0)):
    """
    Returns the closest vertex given a mesh and a position [x,y,z] in world space.
    Uses om2.MfnMesh.getClosestPoint() returned face ID and iterates through face's vertices
    """

    # Using MVector type to represent position
    m_vector = om2.MVector(pos)
    selection_list = om2.MSelectionList()
    selection_list.add(maya_mesh)
    d_path = selection_list.getDagPath(0)
    m_mesh = om2.MFnMesh(d_path)
    # Getting closest face ID
    face_id = m_mesh.getClosestPoint(om2.MPoint(m_vector), space=om2.MSpace.kWorld)[1]
    # Face's vertices list
    vert_list = cmds.ls(cmds.polyListComponentConversion('{}.f[{}]'.format(maya_mesh, face_id), ff=True, tv=True),
                        flatten=True)

    # Setting vertex [0] as the closest one
    d = m_vector - om2.MVector(cmds.xform(vert_list[0], t=True, ws=True, q=True))
    # Using distance squared to compare distance
    smallest_dist_02 = d.x * d.x + d.y * d.y + d.z * d.z
    closest = vert_list[0]

    # Iterating from vertex [1]
    for i in range(1, len(vert_list)):
        d = m_vector - om2.MVector(cmds.xform(vert_list[i], t=True, ws=True, q=True))
        d2 = d.x * d.x + d.y * d.y + d.z * d.z

        if d2 < smallest_dist_02:
            smallest_dist_02 = d2
            closest = vert_list[i]

    return closest


def x_direction_positive(curve):
    """
    True if curve X direction is positive,
    False if curve X direction is negative
    """
    # Get degrees and spans to calculte CV's
    curve_shape = cmds.listRelatives(curve, s=1)[0]
    curve_deg = cmds.getAttr(curve_shape + ".degree")
    curve_spa = cmds.getAttr(curve_shape + ".spans")
    # CV's = degrees + spans
    cv_count = (curve_deg + curve_spa) - 1

    start_x_position = cmds.pointPosition(curve + '.cv[0]')[0]
    end_x_position = cmds.pointPosition(curve + '.cv[{}]'.format(cv_count))[0]

    x_direction = True if start_x_position <= end_x_position else False

    return x_direction


def swap_hierarchy():
    # This must be out of the function
    all_group = cmds.listRelatives(cmds.ls(sl=1), ad=1)
    swap_geo = cmds.listRelatives(cmds.ls(sl=1), c=1)
    # ============

    geo_parent_dict = {}

    for i in all_group:
        name_split = i.split('_')

        if name_split[-1] == 'CH':
            geo_parent_dict.update({i: cmds.listRelatives(i, p=1)[0]})

    for i in swap_geo:
        name_split = i.split('_')
        del name_split[-1]
        name_join = '_'.join(name_split)

        cmds.parent(i, geo_parent_dict[name_join])
        cmds.parent(name_join, w=1)
        cmds.rename(name_join, name_join + '_Del')
        cmds.rename(i, name_join)


def mirror_selection(selection):
    """
    Mirror vertex selection using closest point on mesh
    :param selection:
    :return mirror vertex list:
    """
    selection = cmds.filterExpand(selection, sm=31)
    geo = selection[0].split('.')[0]
    geo_shape = cmds.listRelatives(geo, type='shape')[0]
    closest_point_node = cmds.createNode("closestPointOnMesh")
    locator = cmds.spaceLocator(n='pointer_loc')[0]

    cmds.connectAttr(geo_shape + ".worldMesh[0]", closest_point_node + ".inMesh")
    cmds.connectAttr(locator + '.translate', closest_point_node + '.inPosition')

    mirror_vert_list = []

    for vert in selection:
        position = cmds.xform(vert, q=1, t=1)
        mirror_position = [position[0] * -1, position[1], position[2]]
        cmds.xform(locator, t=mirror_position)

        mirror_vert_index = cmds.getAttr(closest_point_node + ".closestVertexIndex")
        mirror_vert = "{}.vtx[{}]".format(geo, mirror_vert_index)
        mirror_vert_list.append(mirror_vert)

    cmds.delete(locator, closest_point_node)
    cmds.select(mirror_vert_list)

    return mirror_vert_list


def remote_loc_all_joints(selection):
    """
    Creates and places joints on each selection
    :param selection:
    :return List of joints created:
    """
    parent_dict = {}

    # Store hierarchy position for every joint
    for i in selection:
        try:
            parent_dict.update({i: cmds.listRelatives(i, parent=1)[0]})
        except:
            print('Object has no relatives')
            continue

    # Un-parent all joints - parent to world
    cmds.parent(selection, w=1)
    cmds.select(cl=1)
    remote_ctrl_list = []

    for joint in selection:
        # Get joint data
        translate = cmds.xform(joint, q=1, t=1, ws=1)
        rotate = cmds.joint(joint, q=1, o=1)
        scale = cmds.xform(joint, q=1, s=1)

        # Set name for loc based on joint
        new_name = joint.replace("_Jnt", "_RemoteCtrl_Loc")
        # Create locator and space grp
        remote_loc = cmds.spaceLocator(n=new_name)[0]
        remote_ctrl_grp = cmds.group(remote_loc, n=remote_loc + "_Grp")
        # Place locator grp on joint position
        cmds.xform(remote_ctrl_grp, t=translate, ro=[rotate[2], rotate[1]*-1+180, rotate[0]], s=scale)
        # Append new locator to list
        remote_ctrl_list.append(remote_loc)

    for joint in parent_dict:
        cmds.parent(joint, parent_dict[joint])
        cmds.parent(joint.replace("_Jnt", "_RemoteCtrl_Loc_Grp"), parent_dict[joint].replace("_Jnt", "_RemoteCtrl_Loc"))
        cmds.parentConstraint(joint.replace("_Jnt", "_RemoteCtrl_Loc"), joint)

    return remote_ctrl_list, parent_dict


def rename_replace(old, new):
    sel = mc.ls(sl=1)

    for item in sel:
        name = item.replace(old, new)
        mc.rename(item, name)


def rename_add_suffix(suffix):
    sel = mc.ls(sl=1)

    for item in sel:
        name = '{}_{}'.format(item, suffix)
        mc.rename(item, name)


def list_unique(item_list):
    """
    Find unique items in a list
    :param item_list:
    :return unique items list:
    """
    unique_list = []

    # traverse for all elements
    for x in item_list:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)

    return unique_list


def pole_vector_math(dist=0.5):
    """
    Calculates the projected vector of a triangle based on
    3 objects selections and places a locator on the position.
    :param dist:
    tags: polevector, pole vector, polevector math
    """
    sel = mc.ls(sl=1)

    start = mc.xform(sel[0], q=1, ws=1, t=1)
    mid = mc.xform(sel[1], q=1, ws=1, t=1)
    end = mc.xform(sel[2], q=1, ws=1, t=1)

    start_vec = om.MVector(start[0], start[1], start[2])
    mid_vec = om.MVector(mid[0], mid[1], mid[2])
    end_vec = om.MVector(end[0], end[1], end[2])

    start_end = end_vec - start_vec
    start_mid = mid_vec - start_vec

    dot_prod = start_mid * start_end
    projection = float(dot_prod) / float(start_end.length())
    start_end_normal = start_end.normal()
    proj_vector = start_end_normal * projection

    arrow_vec = start_mid - proj_vector
    arrow_vec *= dist
    result_vec = arrow_vec + mid_vec

    cross_01 = start_end ^ start_mid
    cross_01.normalize()

    cross_02 = cross_01 ^ arrow_vec
    cross_02.normalize()

    arrow_vec.normalize()

    matrix_vec = [arrow_vec.x, arrow_vec.y, arrow_vec.z, 0,
                  cross_01.x, cross_01.y, cross_01.z, 0,
                  cross_02.x, cross_02.y, cross_02.z, 0,
                  0, 0, 0, 1]

    matrix_m = om.MMatrix()
    om.MScriptUtil.createMatrixFromList(matrix_vec, matrix_m)

    matrix_fn = om.MTransformationMatrix(matrix_m)
    ro = matrix_fn.eulerRotation()

    loc = mc.spaceLocator()[0]
    mc.xform(loc, ws=1, t=(result_vec.x, result_vec.y, result_vec.z))
    mc.xform(loc, ws=1, ro=((ro.x/math.pi*180.0),
                            (ro.y/math.pi*180.0),
                            (ro.z/math.pi*180.0)))


def get_next_index(item_list):
    """
    Given a list of strings with sequential indexes, check for the next in sequence
    :param item_list:
    :return next int index:
    """
    index_list = []

    for loc in item_list:
        name_split = loc.split('_')
        for item in name_split:
            if item.isdigit():
                index_list.append(int(item))

    new_index = max(index_list) + 1
    return new_index


def get_latest_index(item_list):
    """
    Given a list of strings with sequential indexes, check for the latest
    :param item_list:
    :return next int index:
    """
    index_list = []

    for loc in item_list:
        name_split = loc.split('_')
        for item in name_split:
            if item.isdigit():
                index_list.append(int(item))

    latest_index = max(index_list)
    return latest_index


def orbi_oris_expand_surfaces(surface='', prefix=''):
    surface = surface if surface else mc.ls(sl=1)[0]
    surface_list = []

    mod_list = ['boccinator_srf',
                'depressor_anguli_srf',
                'risorius_srf',
                'zMajor_srf',
                'zMinor_srf',
                'depressor_labii_srf',
                'mentalis_srf',
                'levator_labii_sup_srf',
                'levator_labii_SAN_srf',
                'orbi_oris_output_srf',
                'levator_anguli_srf',
                'mouth_slide_srf1',
                'mouth_slide_srf2',
                'jaw_srf_grp',
                'slider_srf']

    for srf in mod_list:
        mod_srf = mc.duplicate(surface, n='{}_{}'.format(prefix, srf))
        surface_list.append(mod_srf)

    mc.group(surface_list, n='mouth_mod_srf_grp')

    return surface_list


def curves_from_surface(surface, u_or_v="v", crv_amount=10, name=""):
    """
    This function extracts curves from a NURBS Surface
    :param surface:
    :param u_or_v:
    :param crv_amount:
    :param name:
    :return: curve list
    """

    # cet max U V values
    max_value_u = cmds.getAttr(surface + ".maxValueU")
    max_value_v = cmds.getAttr(surface + ".maxValueV")

    # calculate space between each curve
    u_step = max_value_u / (crv_amount - 1)
    v_step = max_value_v / (crv_amount - 1)

    # Select U or V value based on user input
    step = u_step if u_or_v == "u" else v_step
    crv_list = []

    for n in range(crv_amount):
        # calculate current crv position
        crv_parameter = n * step
        crv = cmds.duplicateCurve("{}.{}[{}]".format(surface, u_or_v, crv_parameter),
                                  local=True, ch=0, n="{}_{:02d}_Crv".format(name, n))
        # un-parent from surface
        cmds.parent(crv, w=1)
        # Add curve list
        crv_list.append(crv[0])

    return crv_list


def surface_from_alternate_point(sel_list, name=''):
    """
    Creates surface from alternate point selection
    :param sel_list:
    :param name:
    :return:
    """
    # create interpolated selection list
    start_list = sel_list[::2]
    end_list = sel_list[1::2]
    curve_list = []

    for n, (start, end) in enumerate(zip(start_list, end_list)):
        # create curve from a to b
        curve = curve_from_a_to_b(start, end, name='{}_{:02d}'.format(name, n))
        # rebuild curve to new cv count
        mc.rebuildCurve(curve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=3, d=3, tol=0.01)
        curve_list.append(curve)

    # loft curves to create surface
    surface = mc.loft(curve_list, name='{}_srf'.format(name),
                      ch=0, u=1, c=0, ar=1, d=3, ss=1, rn=0, po=1, rsn=True)[0]

    # group created nodes
    curve_grp = mc.group(curve_list, name='{}_crv_grp'.format(name))
    main_grp = mc.group(surface, curve_grp, name='{}_srf_grp'.format(name))

    return {'curves': curve_list,
            'surface': surface,
            'container': main_grp}


def curve_from_a_to_b(start, end, proxy=False, bind=False, name=''):
    """
    Creates 1 linear curve from selection A to selection B
    :param start:
    :param end:
    :param proxy:
    :param bind:
    :param name:
    :return curve:
    """
    # get positions
    end_tr = mc.xform(end, q=True, t=True, ws=True)
    start_tr = mc.xform(start, q=True, t=True, ws=True)
    # create curve
    bridge_curve = mc.curve(d=True, p=[start_tr, end_tr], name='{}_crv'.format(name))
    cmds.delete(bridge_curve, ch=1)

    if proxy:
        mc.setAttr("{}.overrideEnabled".format(bridge_curve), 1)
        mc.setAttr("{}.overrideDisplayType".format(bridge_curve), 1)

    if bind:
        mc.skinCluster(start, end, bridge_curve,
                       toSelectedBones=True,
                       bindMethod=0,
                       skinMethod=0,
                       normalizeWeights=1)

    return bridge_curve


def build_mouth_blend(surface, rows=22, columns=5, name=''):
    surface_a = mc.duplicate(surface)[0]
    surface_b = mc.duplicate(surface)[0]
    surfaces_data = {}

    for surface in [surface_a, surface_b]:
        follicle_data = follicle_2d(surface, rows=rows, columns=columns, name=name)
        surfaces_data.update({surface: follicle_data})


def multi_constraint_blend(item_list_a, item_list_b, item_list_c):
    main_float = mc.createNode('floatConstant')

    for item_a, item_b, item_c in zip(item_list_a, item_list_b, item_list_c):
        control_float = constraint_blend(item_a, item_b, item_c)
        mc.connectAttr('{}.outFloat'.format(main_float), '{}.inFloat'.format(control_float))

    return main_float


def constraint_blend(item_a, item_b, item_c):
    pc_node = mc.parentConstraint(item_a, item_b, item_c)[0]
    pc_weight_attr = mc.parentConstraint(pc_node, q=1, weightAliasList=1)

    reverse_node = mc.createNode('reverse', n='{}_reverse'.format(item_c))
    float_node = mc.createNode('floatConstant', n='{}_float'.format(item_c))

    mc.connectAttr('{}.outFloat'.format(float_node), '{}.inputX'.format(reverse_node))

    mc.connectAttr('{}.outFloat'.format(float_node), '{}.{}'.format(pc_node, pc_weight_attr[0]))
    mc.connectAttr('{}.outputX'.format(reverse_node), '{}.{}'.format(pc_node, pc_weight_attr[1]))

    return float_node


# def group_items_in_index_order(group):
#     children = mc.listRelatives(group, children=1)
#     pass

def import_all_in_folder(path, file_type):
    """
    Import all files of type from path
    :param path:
    :param file_type:
    :return imported files:
    """
    files = mc.getFileList(folder=path, filespec='*.{}'.format(file_type))

    if len(files) == 0:
        cmds.warning("No files found")
    else:
        for file in files:
            mc.file(path + file, i=True)

    return files


def surface_from_pointers(pointer_list, scale=1, reverse=False, normal=(1, 0, 0), name=''):
    """
    Given a pointer list, creates a curve, and form that creates a surface on the chosen normal direction
    :param pointer_list:
    :param scale:
    :param reverse:
    :param normal:
    :param name:
    :return surface data:
    """
    # if flagged, reverse list order
    if reverse:
        pointer_list.reverse()

    # query positions
    position_list = [mc.xform(pointer, q=True, t=True, ws=True) for pointer in pointer_list]
    # draw curve from pointers
    loft_base_crv = mc.curve(point=position_list, degree=3, ws=True, name='surface_loft_base_crv')
    # del history
    mc.delete(loft_base_crv, ch=True)

    # duplicate curve
    loft_start_crv = mc.duplicate(loft_base_crv, name='loft_01_crv')
    loft_end_crv = mc.duplicate(loft_base_crv, name='loft_02_crv')
    # define offset based on normal and scale
    offset_value = [normal_axis * value for normal_axis, value in zip(normal, (scale, scale, scale))]
    offset_flip_value = [(normal_axis * -1) * value for normal_axis, value in zip(normal, (scale, scale, scale))]
    # offset curves position
    mc.xform(loft_start_crv, t=offset_value, ws=True)
    mc.xform(loft_end_crv, t=offset_flip_value, ws=True)
    # loft curves
    loft_surface = mc.loft(loft_start_crv, loft_end_crv, ch=False,
                           u=0, c=0, ar=1, d=3, ss=1, rn=0, po=0, rsn=True,
                           name='{}_srf'.format(name))
    # delete guide curves
    mc.delete(loft_base_crv, loft_start_crv, loft_end_crv)

    return loft_surface


def surface_from_pointers_2d(pointer_list, pointers_per_crv=2,
                             delete_curves=True, reverse=False, name=''):
    """
    Given a point list, creates a surface on the chosen normal direction
    :param pointer_list:
    :param pointers_per_crv:
    :param delete_curves:
    :param reverse:
    :param name:
    :return loft surface:
    """

    curve_pointers = split_list_in_n_chunks(pointer_list, pointers_per_crv)
    curve_list = []

    for n, curve in enumerate(curve_pointers):
        pointers_t = []

        for pointer in curve_pointers[n]:
            t = mc.xform(pointer, q=True, t=True, ws=True)
            pointers_t.append(t)

        curve = mc.curve(point=pointers_t, degree=3, ws=True,
                         name='{}_loft_{:02d}_crv'.format(name, n))
        curve_list.append(curve)

    # if flagged, reverse list order
    if reverse:
        curve_list.reverse()

    # loft curves
    loft_surface = mc.loft(curve_list, ch=False, u=1, c=0, ar=0,
                           d=3, ss=10, rn=0, po=1, rsn=True,
                           name='{}_srf'.format(name))
    # delete guide curves
    if delete_curves:
        mc.delete(curve_list)

    return loft_surface


def split_list_in_n_chunks(item_list, amount):
    """
    Splits a list in equal N chunks. List length must be divisible by N.
    :param item_list:
    :param amount:
    :return chunks dictionary:
    """
    # declare use variables
    item_counter = 1
    list_counter = 1
    list_dict = {}
    chunks_list = []

    # define amount of lists
    list_amount = len(item_list) / amount

    # create dictionary for lists based on amount
    for n in range(1, int(list_amount) + 1):
        list_dict['list_{:02d}'.format(n)] = []

    # append list items evenly in order
    for item in item_list:
        list_dict['list_{:02d}'.format(list_counter)].append(item)

        if item_counter == amount:
            item_counter = 1
            list_counter += 1
        else:
            item_counter += 1

    # append chunks to list in order
    for n in range(1, len(list_dict.keys())+1):
        chunks_list.append(list_dict['list_{:02d}'.format(n)])

    return chunks_list


# import maya.cmds as cmds
# import maya.OpenMaya as om
# import csv
# import os
#
# filepath =  "E:/tpaulino_projects/015_Itsme_Aakash/Female_Shapes/assets/BlendshapeTracks/blendshape_data_1.txt"
# meshName = 'blendShape4'
# meshName1 = 'blendShape1'
# meshName2 = 'blendShape2'
# prefix = 'exp_'
#
# with open(filepath, 'rt') as csvfile:
#     reader = csv.reader(csvfile, delimiter=',')
#     header = next(reader)
#     rowIndex = 0
#     for row in reader:
#         cmds.currentTime(int(rowIndex), update=True)
#         for x in range(0,51):
#             value = float(row[x])
#             blendShapeName = header[x]
#             cmds.setKeyframe(meshName, at=prefix + blendShapeName + "_Mesh", value=value, time=rowIndex)
#         rowIndex += 1


def export_each_selection(folder='', file_name='', extension='obj'):
    file_type = {
        'obj': 'OBJexport',
        'ma': 'Maya ASCII',
        'mb': 'Maya Binary',
        'fbx': 'FBX export'
    }

    selection_list = mc.ls(sl=1)
    project_path = mc.workspace(q=1, rd=1)

    for item in selection_list:
        mc.select(item, r=1)
        file = '{}_{}.{}'.format(file_name, item, extension)
        mc.file('{}{}/{}'.format(project_path, folder, file),
                type=file_type[extension], es=1,
                op="groups=0; ptgroups=0; materials=0; smoothing=1; normals=0")