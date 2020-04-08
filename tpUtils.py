from __future__ import division
import maya.cmds as mc
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as OpenMayaUI
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

def sys_from_edge_loop(egde, surface, name=""):
    # Extract curve from edge
    # Build Anchor Curve from Slc Edges-> Get Name -> Del History
    cmds.select(edge_slct)
    anchor_curve = cmds.polyToCurve(name=sys_side + sys_purpose + '_Anchor_Crv', form=2,
                                    degree=1, conformToSmoothMeshPreview=0)[0]

    reverse_crv = xDirection_positive(anchor_curve)
    if reverse_crv is False: cmds.reverseCurve(anchor_curve, ch=0, rpo=1)
    cmds.delete(anchor_curve, ch=1)

    # Duplicate -> Rebuild to low res

    # Creat locators on each CV
    locator_list = locatorOnCVs(anchor_curve)
    # Connect locators to CVs
    connectLocatorToCrv(locator_list, anchor_curve)

    # Wire high res to low res curve
    # Create joints on each low res CV
    # bind low res curve to joints
    # Create controls for each joint
    # Connect control/joint transforms

    # Create system on surface
    surface_sys_data = follicle_on_closest_point(surface, locator_list, name)
    # Group and organize system on Outliner


def follicle_on_closest_point(surface, locator_list, name=""):

    surface_shape = cmds.listRelatives(surface, type="shape")[0]
    follicle_dict = {}
    closesPoint_node_list = []
    setRange_node_list = []

    for n, loc in enumerate(locator_list):
        # Create Point on Curve Info node
        closesPoint_node = cmds.createNode("closestPointOnSurface", n="{}_{:02d}_closestPointOnSrf")
        closesPoint_node_list.append(closesPoint_node)
        # Create follicle on surface
        follice_data = createFollicle(inputSurface=[surface_shape], hide=0, name="{}_{:02d}_Flc".format(name, n))
        follicle_dict.update({follice_data[0]:follice_data[1]})

        # Connect surface to pci
        cmds.connectAttr(surface_shape + ".local", closesPoint_node + ".inputSurface", f=1)
        # Connect locator to pci
        cmds.connectAttr(loc + ".translate", closesPoint_node + ".inPosition")

        # Create set range for parameterV
        setRage_node = cmds.shadingNode("setRange", asUtility=1, n="{}_{:02d}_setRange".format(name, n))
        setRange_node_list.append(setRage_node)
        # Get surface max U and V parameters
        cmds.connectAttr(surface_shape + ".maxValueV", setRage_node + ".oldMaxX")
        cmds.connectAttr(surface_shape + ".maxValueU", setRage_node + ".oldMaxY")
        cmds.setAttr(setRage_node + ".maxX", 1)
        cmds.setAttr(setRage_node + ".maxY", 1)
        # Connect pci to follicle
        cmds.connectAttr(closesPoint_node + ".parameterV", setRage_node + ".valueX", f=1)
        cmds.connectAttr(closesPoint_node + ".parameterU", setRage_node + ".valueY", f=1)
        cmds.connectAttr(setRage_node + ".outValueX", follice_data[1] + ".parameterV")
        cmds.connectAttr(setRage_node + ".outValueY", follice_data[1] + ".parameterU")

    return follicle_dict, closesPoint_node_list, setRange_node_list


def connectLocatorToCrv(loc_list, crv):

    for loc in loc_list:
        loc_pos = cmds.xform(loc, q=1, ws=1, t=1)
        loc_u = getUParam(loc_pos, anchor_curve)
        pciNode_name = loc.replace("_loc", "_pci")
        pciNode = cmds.createNode("pointOnCurveInfo", n=pciNode_name)
        cmds.connectAttr(anchor_curve + ".worldSpace", pciNode + ".inputCurve")
        cmds.setAttr(pciNode + ".parameter", loc_u)
        cmds.connectAttr(pciNode + ".position" , loc + ".t")


def locatorOnCVs(path_crv):
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


def follicle_2d(name="", rows=3, colums=3, widthPercentage=1, hightPercentage=1):
    """
    Distribute follicles in a 2D array of a polygon surface
    Distribute follicles on surface + joints and controls
    """

    # If columns/rows equals 1, position in center
    if colums == 1.0: surface_uStep = 0.5
    else: surface_uStep = (100 / (colums-1) / 100) * widthPercentage
    if rows == 1.0: surface_vStep = 0.5
    else: surface_vStep = (100 / (rows-1) / 100) * hightPercentage

    surface = cmds.ls(sl=1)[0]
    surface_shape = cmds.listRelatives(surface, type="shape")

    follicle_list = []
    joint_list = []

    for i in range(int(colums)):
        for y in range(int(rows)):
            if colums == 1.0: uParameter = surface_uStep
            else: uParameter = surface_uStep * i
            if rows == 1.0: vParameter = surface_vStep
            else: vParameter = surface_vStep * y

            follicle_data = createFollicle(inputSurface=surface_shape, uVal=uParameter, vVal=vParameter,
                                            name="{}_Flc_C{}_R{}".format(name, i, y), hide=0)
            joint = cmds.joint(n="{}_Jnt_C{}_R{}".format(name, i, y))

            follicle_position = cmds.xform(follicle_data[0], q=1, t=1)
            follicle_rotation = cmds.xform(follicle_data[0], q=1, ro=1)

            cmds.xform(joint, t=follicle_position, ro=follicle_rotation)
            cmds.parentConstraint(follicle_data[0], joint)

            follicle_list.append(follicle_data[0])
            joint_list.append(joint)

    joint_group = cmds.group(joint_list, n=name + "_Jnt_Grp")
    follicle_group = cmds.group(follicle_list, n=name + "_Flc_Grp")


def createFollicle(inputSurface=[], scaleGrp='', uVal=0.5, vVal=0.5, hide=1, name='follicle'):
    # Create a follicle
    follicleShape = cmds.createNode('follicle')
    # Get the transform of the follicle
    follicleTrans = cmds.listRelatives(follicleShape, parent=True)[0]
    # Rename the follicle
    follicleTrans = cmds.rename(follicleTrans, name)
    follicleShape = cmds.rename(cmds.listRelatives(follicleTrans, c=True)[0], (name + 'Shape'))

    # If the inputSurface is of type 'nurbsSurface', connect the surface to the follicle
    if cmds.objectType(inputSurface[0]) == 'nurbsSurface':
        cmds.connectAttr((inputSurface[0] + '.local'), (follicleShape + '.inputSurface'))
    # If the inputSurface is of type 'mesh', connect the surface to the follicle
    if cmds.objectType(inputSurface[0]) == 'mesh':
        cmds.connectAttr((inputSurface[0] + '.outMesh'), (follicleShape + '.inputMesh'))

    # Connect the worldMatrix of the surface into the follicleShape
    cmds.connectAttr((inputSurface[0] + '.worldMatrix[0]'), (follicleShape + '.inputWorldMatrix'))
    # Connect the follicleShape to it's transform
    cmds.connectAttr((follicleShape + '.outRotate'), (follicleTrans + '.rotate'))
    cmds.connectAttr((follicleShape + '.outTranslate'), (follicleTrans + '.translate'))
    # Set the uValue and vValue for the current follicle
    cmds.setAttr((follicleShape + '.parameterU'), uVal)
    cmds.setAttr((follicleShape + '.parameterV'), vVal)
    # Lock the translate/rotate of the follicle
    cmds.setAttr((follicleTrans + '.translate'), lock=True)
    cmds.setAttr((follicleTrans + '.rotate'), lock=True)

    # If it was set to be hidden, hide the follicle
    if hide:
        cmds.setAttr((follicleShape + '.visibility'), 0)
    # If a scale-group was defined and exists
    if scaleGrp and cmds.objExists(scaleGrp):
        # Connect the scale-group to the follicle
        cmds.connectAttr((scaleGrp + '.scale'), (follicleTrans + '.scale'))
        # Lock the scale of the follicle
        cmds.setAttr((follicleTrans + '.scale'), lock=True)
    # Return the follicle and it's shape
    return follicleTrans, follicleShape


def find_center():
    """
    Place locator in object center
    :return:
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


# JOINT SECTION __________________________________________________________________

def jointChainMultiCrv(addIk=0, bind=0, loft=0, cluster=0, name=""):
    """
    ikSpline Loft System
    :param addIk:
    :param bind:
    :param loft:
    :param cluster:
    :param name:
    :return:
    """
    raw_curves = cmds.ls(sl=1)
    curves = []
    ikHandle_list = []
    ikSpline_crv_list = []
    joint_list = []
    grp_list = []

    # Creating brand new, clean curves out of selection
    for j, i in enumerate(raw_curves, 1):
        new_curve = cmds.duplicate(i, n="{}_Loft_Crv{}".format(name, j))
        cmds.parent(new_curve, w=1)
        cmds.makeIdentity(new_curve, apply=True, t=1, r=1, s=1, n=0)
        cmds.delete(new_curve, ch=1)
        cmds.xform(new_curve, cp=1)
        curves.append(new_curve[0])

    # Joint chain and ikSpline section
    for n, i in enumerate(curves):
        crv_joint_list = jointsOnCVs(path_crv=i)
        parentInOrder(sel=crv_joint_list)
        joint_list.append(crv_joint_list[0])
        cmds.select(cl=1)

        if addIk == 1:
            # Creating ikSpline - rename curve - append to grouping lists
            ikHandle_data = cmds.ikHandle(sj=crv_joint_list[0], ee=crv_joint_list[-1], sol="ikSplineSolver",
                                          n=i + "_ikHandle")
            ik_crv = cmds.rename(ikHandle_data[2], "{}_ikSpline_Crv{}".format(name, n+1))
            ikHandle_list.append(ikHandle_data[0])
            ikSpline_crv_list.append(ik_crv)

            if n == 0:
                # If it is the first loop - create groups - else - parent new items
                ik_grp = cmds.group(ikHandle_data[0], n=name + "_ikHandle_Grp")
                spline_grp = cmds.group(ik_crv, n=name + "_ikSpline_Crv_Grp")
                grp_list.append(ik_grp)
                grp_list.append(spline_grp)
            else:
                cmds.parent(ikHandle_data[0], ik_grp)
                cmds.parent(ik_crv, spline_grp)

        if bind == 1: cmds.skinCluster(crv_joint_list, i)

    if loft == 1:
        loft_data = cmds.loft(curves, ch=1, u=1, c=0, ar=0, d=3, ss=10, rn=0, po=1, rsn=1)
        loft_srf = cmds.rename(loft_data[0], name + "_LoftSrf_Geo")
        loft_grp = cmds.group(loft_srf, n=name + "_LoftSrf_Geo_Grp")
        grp_list.append(loft_grp)

    if cluster == 1 and addIk == 1:
        # Creates clusters honlding the same cv on each ikSpline curve
        # Calculating the number of Cv's for loop
        curveDeg = cmds.getAttr(ikSpline_crv_list[0] + ".degree")
        curveSpa = cmds.getAttr(ikSpline_crv_list[0] + ".spans")
        # CV's = degrees + spans
        cvCount = curveDeg + curveSpa
        cls_list = []

        for i in range(cvCount):
            cmds.select(cl=1)
            for j in ikSpline_crv_list: cmds.select("{}.cv[{}]".format(j, i), add=1)
            cluster = cmds.cluster(n="{}_Csl{}".format(name, i))
            cls_list.append(cluster[1])

        cluster_grp = cmds.group(cls_list, n=name + "_Cls_Grp")
        grp_list.append(cluster_grp)

    else:
        cmds.warning("addIk is off")

    curves_grp = cmds.group(curves, n="{}_Loft_Crv_Grp".format(name))
    joint_grp = cmds.group(joint_list, n=name + "_Jnt_Grp")
    grp_list.append(curves_grp)
    grp_list.append(joint_grp)
    sys_grp = cmds.group(grp_list, n=name + "_Sys_Grp")

    return sys_grp


def jointsOnSelection():
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

        newJoint = cmds.joint(n=i + "_Jnt")
        cmds.select(cl=1)
        cmds.xform(newJoint, t=translate, ro=rotate, s=scale)

        joint_list.append(newJoint)

    return joint_list


def jointsOnCVs(path_crv):
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


def parentInOrder(sel):
    """
    Parent in selection order
    :param sel:
    """
    for z, i in enumerate(sel):
        cmds.parent(sel[z+1], i)
        if z+1 >= len(sel)-1: break


# CONTROL SECTION __________________________________________________________________

def build_ctrl(ctrl_type="circle", name="", sufix="_Ctrl", scale=1, spaced=1, offset=0):
    """
    ctrl_type - Cube, Sphere, Circle (add - square, pointer, arrow, spherev2)
    :param ctrl_type:
    :param name:
    :param sufix:
    :param scale:
    :param spaced:
    :param offset:
    :return [ctrl, ctrl_grp, offset_ctrl_grp]:
    """
    pack = []
    c1 = ''

    if ctrl_type == "cube":
        c1 = cmds.curve(n=name + sufix,
                        p=[(-1.0, 1.0, 1.0), (-1.0, 1.0, -1.0), (1.0, 1.0, -1.0),
                           (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, -1.0, 1.0),
                           (1.0, -1.0, 1.0), (1.0, -1.0, -1.0), (-1.0, -1.0, -1.0),
                           (-1.0, -1.0, 1.0), (-1.0, -1.0, -1.0), (-1.0, 1.0, -1.0),
                           (1.0, 1.0, -1.0), (1.0, -1.0, -1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0)],
                        k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], d=1)

        pack.append(c1)

    elif ctrl_type == "sphere":
        c1 = cmds.circle(n=name + sufix, nr=(1, 0, 0), r=scale, ch=0)[0]
        c2 = cmds.circle(nr=(0, 1, 0), r=scale, ch=0)[0]
        c3 = cmds.circle(nr=(0, 0, 1), r=scale, ch=0)[0]

        cmds.parent(cmds.listRelatives(c2, s=True), cmds.listRelatives(c3, s=True), c1, r=True, s=True)
        cmds.delete(c2, c3)
        pack.append(c1)

    elif ctrl_type == "circle":
        c1 = cmds.circle(n=name + sufix, nr=(1, 0, 0), r=scale, ch=0)[0]
        pack.append(c1)

    shapes = cmds.listRelatives(c1, f=True, s=True)
    for y, shape in enumerate(shapes):
        cmds.rename(shape, "{}Shape{:02d}".format(c1, y+1))

    if spaced == 1:
        ctrl_grp = cmds.group(c1, n=name + sufix + "_Grp")
        pack.append(ctrl_grp)

    # Creates offset group for static control
    if offset == 1:
        offset_grp = cmds.group(c1, n=name + sufix + "_Offset_Grp")
        mpDivide_node = cmds.shadingNode('multiplyDivide', au=1)

        cmds.connectAttr(c1 + '.translate', mpDivide_node + '.input1')
        cmds.connectAttr(mpDivide_node + '.output', offset_grp + '.translate')
        cmds.setAttr(mpDivide_node + '.input2X', -1)
        cmds.setAttr(mpDivide_node + '.input2Y', -1)
        cmds.setAttr(mpDivide_node + '.input2Z', -1)
        pack.append(offset_grp)

    return pack


def place_on_selection(type="circle", scale=1, spaced=1):
    """
    Control on each selection
    :param type:
    :param scale:
    :param spaced:
    :return:
    """
    sel = cmds.ls(sl=1)

    for n, i in enumerate(sel):
        position = cmds.xform(i, q=1, t=1, ws=1)
        rotation = cmds.xform(i, q=1, ro=1, ws=1)

        control = build_ctrl(ctrl_type=type, name=i, scale=scale, spaced=spaced)

        if spaced == 1:
            cmds.xform(control[1], t=position, ro=rotation)
        else:
            cmds.xform(control[0], t=position, ro=rotation)


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


def control_on_cv_list():
    """
    Controls on CV's
    """
    path_crv = cmds.ls(sl=1)[0]
    cv_list = cmds.getAttr(path_crv + '.cv[:]')

    for i, cv in enumerate(cv_list):
        ctrl = tp_staticCtrl('ctrl_cv' + str(i))
        cmds.xform(ctrl[1], t= cv)


def place_on_clusters(name="", type="circle", scale=1, color=(1, 1, 1), parent_constraint=0):
    """
    Control on each Cluster selection
    :param name:
    :param type:
    :param scale:
    :param color:
    :param parent_constraint:
    :return:
    """
    sel = cmds.ls(sl=1)

    for n, i in enumerate(sel):
        cls_shape = cmds.listRelatives(i, type="shape")
        cls_tr = cmds.getAttr(cls_shape[0] + ".origin")[0]

        new_ctrl = build_ctrl(ctrl_type=type, name=i, sufix="_Ctrl".format(n),
                              scale=scale, spaced=1, offset=0)
        setCtrlColor(new_ctrl[0], color = color)
        cmds.xform(new_ctrl[1], t=cls_tr)
        if parent_constraint == 1:
            cmds.parentConstraint(new_ctrl[0], i, mo=1)


def place_on_joints(name, scale=1, color=(1,1,1), parent_constraint=0):
    """
    Control on each Joint selection
    :param name:
    :param scale:
    :param color:
    :param parent_constraint:
    :return:
    """
    sel = cmds.ls(sl=1)

    for n, i in enumerate(sel):
        position = cmds.xform(i, q=1, t=1, ws=1)
        rotation = cmds.joint(i, q=1, o=1)
        new_ctrl = build_ctrl(ctrl_type="circle", name=name, sufix="_Ctrl{}".format(n),
                              scale=scale, spaced=1, offset=0)
        setCtrlColor(new_ctrl[0], color = color)
        cmds.xform(new_ctrl[1], t=position, ro=rotation)
        if parent_constraint == 1:
            cmds.parentConstraint(new_ctrl[0], i, mo=1)


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
        if y+1 >= len(groups-1): break


def multi_setColor(color=(1,1,1)):
    """
    Set Control Color in Multiple Controls
    :param color:
    """
    sel = cmds.ls(sl=1)

    for i in sel:
        setCtrlColor(ctrl=i, color=color)


def setCtrlColor(ctrl, color = (1,1,1)):
    """
    Set control color
    :param ctrl:
    :param color:
    """
    rgb = ("R","G","B")

    cmds.setAttr(ctrl + ".overrideEnabled", 1)
    cmds.setAttr(ctrl + ".overrideRGBColors", 1)

    for channel, color in zip(rgb, color):

        cmds.setAttr("{}.overrideColor{}".format(ctrl, channel), color)

def placeCtrlsOnCrv(name, amount):
    """
    place controls on curve
    :param name:
    :param amount:
    """
    crv = cmds.ls(sl=1)
    crvStep = 100 / (amount-1) / 100

    for i in range(int(amount)):
        parameter = crvStep * i
        position = getPointOnCurve(crv, parameter, 1)
        createCtrl(name + str(i), position[0], position[1])

# GENERAL SECTION __________________________________________________________________

def getPointOnCurve(crv, parameter, inverse=0):
    """
    Gets position and rotation of point on curve using motion path
    :param crv:
    :param parameter:
    :param inverse:
    :return translation and rotation list:
    """
    poc_loc = cmds.spaceLocator(name='Poc_Temp_Loc')
    mPath_Crv = cmds.duplicate(crv, name='mPath_Temp_Crv')[0]
    cmds.delete(mPath_Crv, ch=1)

    mPath = cmds.pathAnimation(poc_loc, mPath_Crv, n= 'mPath_Temp', fractionMode=1, followAxis= 'x', upAxis= 'y',
                               worldUpType= "vector", inverseUp= inverse, inverseFront= inverse)
    cmds.disconnectAttr(mPath + '_uValue.output', mPath + '.uValue')
    cmds.setAttr(mPath + '.uValue', parameter)

    tr = cmds.xform(poc_loc, q=1, t=1)
    rt = cmds.xform(poc_loc, q=1, ro=1)
    point = [tr, rt]

    cmds.delete(mPath + '_uValue', mPath, poc_loc, mPath_Crv)

    # point = [[t.x, t.y, t.z], [r.x, r.y, r.z]]
    return point


def multi_motionpath(name, amount, inverse=0):
    """
    Gets position and rotation of point on curve using motion path
    :param name:
    :param amount:
    :param inverse:
    """
    crvStep = 100 / (amount-1) / 100
    mPath_Crv = cmds.ls(sl=1)
    cmds.select(cl=1)
    loc_list = []

    for i in range(int(amount)):
        parameter = crvStep * i
        loc = cmds.spaceLocator(n=name + '_loc' + str(i))
        mPath = cmds.pathAnimation(loc, mPath_Crv, n=name + '_mPath' + str(i), fractionMode=1, followAxis='x',
                                   upAxis='y', worldUpType="vector", inverseUp=inverse, inverseFront=inverse)
        cmds.disconnectAttr(mPath + '_uValue.output', mPath + '.uValue')
        cmds.setAttr(mPath + '.uValue', parameter)

        loc_list.append(loc)

    cmds.group(loc_list)


def param_from_length(curve, count, curve_type = "open", space = "uv", normalized=True):
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

    if divider==0:
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
        data=[]
        space = om.MSpace.kWorld
        point = om.MPoint()
        for p in param:
            curve_fn.getPointAtParam(p, point, space)
            data.append([point[0], point[1], point[2]]) #world space points
    elif normalized == True:

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
    object = cmds.ls(sl=1)[0]
    bbox = cmds.getAttr(object + ".boundingBox.boundingBoxSize")[0]

    obj_copy = cmds.duplicate(object, n="pivot_obj")

    cmds.xform(obj_copy, cp=1)
    obj_copy_tr = cmds.xform(obj_copy, q=1, piv=1)[:3]
    cmds.delete(obj_copy)
    bbox_cube = cmds.polyCube(w=bbox[0], h=bbox[1], d=bbox[2], sx=1, sy=1, sz=1, ch=0)
    cmds.xform(bbox_cube, t=obj_copy_tr)


# List Top level nodes on Outliner
# cmds.ls(assemblies=True)


# Image resize function
# resizeImage('<sourceImage.png>','<outputImage.png>', 800, 600)
def resizeImage(sourceImage, outputImage, width, height):

    image = om.MImage()
    image.readFromFile(sourceImage)

    image.resize( width, height )
    image.writeToFile( outputImage, 'png')


# -------------------------------------------------------------------------------
# Name:        get_image_size
# Purpose:     extract image dimensions given a file path using just
#              core modules
#
# Author:      Paulo Scardine (based on code from Emmanuel VAISSE)
#
# Created:     26/09/2013
# Copyright:   (c) Paulo Scardine 2013
# Licence:     MIT
# -------------------------------------------------------------------------------
class UnknownImageFormat(Exception):
    pass


def get_image_size(file_path):
    """
    Return (width, height) for a given img file content - no external
    dependencies except the os and struct modules from core
    """
    size = os.path.getsize(file_path)

    with open(file_path) as input:
        height = -1
        width = -1
        data = input.read(25)

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
            input.seek(0)
            input.read(2)
            b = input.read(1)
            try:
                while (b and ord(b) != 0xDA):
                    while (ord(b) != 0xFF): b = input.read(1)
                    while (ord(b) == 0xFF): b = input.read(1)
                    if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                        input.read(3)
                        h, w = struct.unpack(">HH", input.read(4))
                        break
                    else:
                        input.read(int(struct.unpack(">H", input.read(2))[0])-2)
                    b = input.read(1)
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
        vertPos = cmds.xform(vert, q=1, t=1)
        mirror_pos = [(vertPos[0] * -1), vertPos[1], vertPos[2]]
        mirror_vert_list.append(getClosestVertex_v2(mesh, mirror_pos))

    # cmds.select(mirror_vert_list, r=1)

    return mirror_vert_list


def getClosestVertex_v2(mayaMesh, pos=(0, 0, 0)):
    """
    Returns the closest vertex given a mesh and a position [x,y,z] in world space.
    Uses om2.MfnMesh.getClosestPoint() returned face ID and iterates through face's vertices
    """

    # Using MVector type to represent position
    mVector = om2.MVector(pos)
    selectionList = om2.MSelectionList()
    selectionList.add(mayaMesh)
    dPath = selectionList.getDagPath(0)
    mMesh = om2.MFnMesh(dPath)
    # Getting closest face ID
    face_ID = mMesh.getClosestPoint(om2.MPoint(mVector), space=om2.MSpace.kWorld)[1]
    # Face's vertices list
    vert_list = cmds.ls(cmds.polyListComponentConversion('{}.f[{}]'.format(mayaMesh, face_ID), ff=True, tv=True),
                        flatten=True)

    # Setting vertex [0] as the closest one
    dist_01 = om2.MVector(cmds.xform(vert_list[0], t=True, ws=True, q=True))
    smallestDist = math.sqrt((dist_01.x - pos[0])**2 + (dist_01.y - pos[1])**2 + (dist_01.z - pos[2])**2)
    # Using distance squared to compare distance
    closest = vert_list[0]

    # Iterating from vertex [1]
    for i in range(1, len(vert_list)) :
        dist_02 = om2.MVector(cmds.xform(vert_list[i], t=True, ws=True, q=True))
        eucDist = math.sqrt((dist_02.x - pos[0])**2 + (dist_02.y - pos[1])**2 + (dist_02.z - pos[2])**2)

        if eucDist <= smallestDist:
            smallestDist = eucDist
            closest = vert_list[i]

    return closest

# Not in use
def getClosestVertex(mayaMesh, pos=(0, 0, 0)):
    """
    Returns the closest vertex given a mesh and a position [x,y,z] in world space.
    Uses om2.MfnMesh.getClosestPoint() returned face ID and iterates through face's vertices
    """

    # Using MVector type to represent position
    mVector = om2.MVector(pos)
    selectionList = om2.MSelectionList()
    selectionList.add(mayaMesh)
    dPath = selectionList.getDagPath(0)
    mMesh = om2.MFnMesh(dPath)
    # Getting closest face ID
    face_ID = mMesh.getClosestPoint(om2.MPoint(mVector), space=om2.MSpace.kWorld)[1]
    # Face's vertices list
    vert_list = cmds.ls(cmds.polyListComponentConversion('{}.f[{}]'.format(mayaMesh, face_ID), ff=True, tv=True),
                        flatten=True)

    # Setting vertex [0] as the closest one
    d = mVector - om2.MVector(cmds.xform(vert_list[0], t=True, ws=True, q=True))
    # Using distance squared to compare distance
    smallestDist2 = d.x * d.x + d.y * d.y + d.z * d.z
    closest = vert_list[0]

    # Iterating from vertex [1]
    for i in range(1, len(vert_list)) :
        d = mVector - om2.MVector(cmds.xform(vert_list[i], t=True, ws=True, q=True))
        d2 = d.x * d.x + d.y * d.y + d.z * d.z

        if d2 < smallestDist2:
            smallestDist2 = d2
            closest = vert_list[i]

    return closest


def xDirection_positive(curve):
    """
    True if curve X direction is positive,
    False if curve X direction is negative
    """
    x_direction = True
    # Get degrees and spans to calculte CV's
    curve_shape = cmds.listRelatives(curve, s=1)[0]
    curveDeg = cmds.getAttr(curve_shape + ".degree")
    curveSpa = cmds.getAttr(curve_shape + ".spans")
    # CV's = degrees + spans
    cvCount = (curveDeg + curveSpa) -1

    start_x_position = cmds.pointPosition(curve + '.cv[0]')[0]
    end_x_position = cmds.pointPosition(curve + '.cv[{}]'.format(cvCount))[0]

    if start_x_position <= end_x_position: x_direction = True
    else: x_direction = False

    return x_direction


def swapHierarchy():
    # This must be out of the function
    all_group = cmds.listRelatives(cmds.ls(sl=1), ad=1)
    swap_geo = cmds.listRelatives(cmds.ls(sl=1), c=1)
    # ============

    geo_parent_dict = {}

    for i in all_group:
        name_split = i.split('_')

        if name_split[-1] == 'CH':
            geo_parent_dict.update({i:cmds.listRelatives(i, p=1)[0]})

    for i in swap_geo:
        name_split = i.split('_')
        del name_split[-1]
        name_join = '_'.join(name_split)

        cmds.parent(i, geo_parent_dict[name_join])
        cmds.parent(name_join, w=1)
        cmds.rename(name_join, name_join + '_Del')
        cmds.rename(i, name_join)


def mirrorSelection(selection):
    """
    Mirror vertex selection using closest point on mesh
    :param selection:
    :return mirror vertex list:
    """
    selection = cmds.filterExpand(selection, sm=31)
    geo = selection[0].split('.')[0]
    geo_shape = cmds.listRelatives(geo, type='shape')[0]
    closestPoint_node = cmds.createNode("closestPointOnMesh")
    locator = cmds.spaceLocator(n='pointer_loc')[0]

    cmds.connectAttr(geo_shape + ".worldMesh[0]", closestPoint_node + ".inMesh")
    cmds.connectAttr(locator + '.translate', closestPoint_node + '.inPosition')

    mirror_vert_list = []

    for vert in selection:
        position = cmds.xform(vert, q=1, t=1)
        mirror_position = [position[0] * -1, position[1], position[2]]
        cmds.xform(locator, t=mirror_position)

        mirror_vert_index = cmds.getAttr(closestPoint_node + ".closestVertexIndex")
        mirror_vert = "{}.vtx[{}]".format(geo, mirror_vert_index)
        mirror_vert_list.append(mirror_vert)

    cmds.delete(locator, closestPoint_node)
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


def rename_sel(old, new):
    sel = mc.ls(sl=1)

    for item in sel:
        name = item.replace(old, new)
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


class handle:
    pass


class module:
    pass


class template:
    pass


class RigTemplate:

    """
    Class development:
        export/import system data
        export/import template data
        add cube shape to joint
        add annotation to modules
        add position by vertex average
            switchable mesh name
            manual position override
        add set index by parent order
        add root joint on environment
        add mirror selected joints
        add mirror system
        add nested systems (necessary)
        add vertex stash to store random vertex data
        reset index
            from parent data
            from selection order
        split class into
            handle
            module
            template
        duplicate sys with different name

        fixes
            error when root not assigned - DONE
            error when no locator is not loaded
            set root happening on locator level
            connection lines double transforming

        parent systems - DONE
            add attribute to loc - DONE
            add attribute to sys - DONE
        rebuild template from data - DONE
        set module root - DONE
            update position on rebuild - DONE
        dev update_template_data - DONE
        create template group dict - DONE
        line between locators - DONE
        parent system - DONE
        rebuild system - DONE
    """

    def __init__(self):
        self.tag_node = 'tp_rigSystems_rigTemplate'
        self.environment_grp = ''
        self.sys = ''
        self.loc = ''

        self.environment_data = {}
        self.sys_data = {}
        self.loc_data = {}
        self.tag_data = {}
        self.temp_sys_data = {}
        self.loaded_loc_data = {}

        self.current_data = {}

        self.data_templates = {
            'environment_data': {
                'name': '',
                'group': '',
                'systems': []},

            'sys_data': {
                'name': '',
                'group': '',
                'position': {
                    't': [],
                    'r': [],
                    's': []},
                'locators': {},
                'root': ''},

            'loc_data': {
                'parent': '',
                'unique_name': '',
                'name': '',
                'index': '',
                'position': {
                    't': [],
                    'r': [],
                    's': []},
                'system_grp': '',
                'system_plug': '',  # Used to retrieve loc name
                'ref_vertex': [],
                'joint': '',
                'root': False},

            'tag_data': {
                'creation_date': '',
                'last_modified': '',
                'original_file': '',
                'class_version': '',
                'id': '',
                'credits': 'Create By Thiago Paulino'}}

        self.init_template_sys()

    # CREATE SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def init_template_sys(self):
        """
        Initializes system by searching for tag for tp_rigSystems_rigTemplate tag and getting environment
        if nonexistent, creates tag and environment
        """
        if not mc.objExists(self.tag_node):
            self.tag_node = mc.createNode('controller', name='tp_rigSystems_rigTemplate')
            mc.addAttr(self.tag_node, longName='metadata', dataType='string')
            mc.addAttr(self.tag_node, longName='environment_data', dataType='string', multi=True,
                       indexMatters=False)
            self.commit_data(self.tag_node, self.data_templates['tag_data'])
            self.new_environment()

        self.tag_data = eval(mc.getAttr('{}.metadata'.format(self.tag_node)))
        self.environment_grp = mc.listConnections('{}.environment_data'.format(self.tag_node), s=1, d=0)[0]
        self.environment_data = eval(mc.getAttr('{}.metadata'.format(self.environment_grp)))

    def new_environment(self, name=''):
        """
        Creates new group for all template systems with necessary attributes
        Connects to tag group for easy class access
        """
        self.environment_data = self.data_templates['environment_data']
        self.environment_data['group'] = mc.group(name='rig_template_grp', em=1)

        mc.addAttr(self.environment_data['group'], longName='metadata', dataType='string')
        mc.addAttr(self.environment_data['group'], longName='sys_data', dataType='string', multi=True,
                   indexMatters=False)
        mc.connectAttr('{}.metadata'.format(self.environment_data['group']),
                       '{}.environment_data'.format(self.tag_node),
                       nextAvailable=True)
        self.commit_data(self.environment_data['group'], self.environment_data)

        self.environment_data = eval(mc.getAttr('{}.metadata'.format(self.environment_data['group'])))

    def new_sys(self, name):
        """
        Creates new group for module/system with necessary data attributes and connections
        :param name:
        """
        self.sys_data = self.data_templates['sys_data']
        self.sys_data['name'] = name if name else 'tempName'
        self.sys_data['group'] = mc.group(name='{}_sys_grp'.format(name), empty=True)
        mc.parent(self.sys_data['group'], self.environment_data['group'])
        mc.select(cl=True)

        mc.addAttr(self.sys_data['group'], longName='root', dataType='string')
        mc.addAttr(self.sys_data['group'], longName='parent', attributeType='message')
        mc.addAttr(self.sys_data['group'], longName='child', attributeType='message')
        mc.addAttr(self.sys_data['group'], longName='sys_parent', attributeType='message')
        mc.addAttr(self.sys_data['group'], longName='metadata', dataType='string')
        mc.addAttr(self.sys_data['group'], longName='loc_data', dataType='string',
                   multi=True, indexMatters=False)

        mc.connectAttr('{}.metadata'.format(self.sys_data['group']),
                       '{}.sys_data'.format(self.environment_data['group']),
                       nextAvailable=True)

        self.commit_data(self.sys_data['group'], self.sys_data)

    def new_loc(self, unique_name='', loc_index='', system='', root=False):
        """
        Creates new template locator with metadata attribute
        :param unique_name:
        :param loc_index:
        :param system:
        :param root:
        """
        if system:
            self.load_sys(system)
        if not loc_index:
            loc_list = self.sys_members()  # place outside loc creation - encapsulate
            loc_index = 1 if loc_list is None else get_next_index(loc_list)

        loc_name = '{}_'.format(unique_name) if unique_name else ''
        name = '{}{}_{:02d}_loc'.format(loc_name, self.sys_data['name'], loc_index)

        mc.select(cl=1)
        self.loc = mc.joint(name=name)
        mc.addAttr(self.loc, longName='metadata', dataType='string')
        mc.addAttr(self.loc, longName='parent', attributeType='message')
        mc.addAttr(self.loc, longName='child', attributeType='message')
        mc.addAttr(self.loc, longName='sys_child', attributeType='message')
        mc.connectAttr('{}.metadata'.format(self.loc), '{}.loc_data'.format(self.sys_data['group']),
                       nextAvailable=True)
        if root:
            self.set_root()  # re-evaluate

        self.loc_data = self.data_templates['loc_data']
        self.loc_data.update({
            'unique_name': unique_name,
            'system_grp': self.sys_data['group'],
            'system_plug': mc.listConnections('{}.metadata'.format(self.loc), d=1, s=0, p=1)[0].split('.')[1],
            'name': self.loc,
            'root': True if root else False})
        self.commit_data(self.loc, self.loc_data)

        mc.parent(self.loc, self.sys_data['group'])

    # REBUILD SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def rebuild_template_from_data(self, template_data):
        """
        rebuilds the whole tamplate based on provided data
        :param template_data:
        """
        # rebuild environment
        self.init_template_sys()
        # rebuild all systems
        for sys in template_data['systems']:
            self.rebuild_sys_from_data(template_data['systems'][sys])

        for sys in template_data['systems']:
            self.load_sys(sys)
            if template_data['systems'][sys]['sys_parent']:
                self.set_sys_parent(template_data['systems'][sys]['sys_parent'])

    def rebuild_template(self):
        """
        Queries template data, deletes template and rebuilds from data
        :return:
        """
        self.update_template_data()
        mc.delete(self.environment_data['group'])
        self.rebuild_template_from_data(self.environment_data)

    def rebuild_sys_from_data(self, sys_data):
        """
        Rebuilds single system based on data dictionary
        :param sys_data:
        :return:
        """
        self.new_sys(sys_data['name'])

        # set group position to match root joint
        mc.xform(self.sys_data['group'],
                 t=sys_data['locators'][sys_data['root']]['position']['t'],
                 ro=sys_data['locators'][sys_data['root']]['position']['r'],
                 ws=True)

        for loc in sys_data['locators']:
            # rebuild locator
            self.new_loc(sys_data['locators'][loc]['unique_name'],
                         loc_index=sys_data['locators'][loc]['index'])
            self.loc_data = sys_data['locators'][loc]
            self.commit_data(self.loc, self.loc_data)

        for loc in self.sys_members():
            # reposition locator based on commited data
            self.load_loc(loc)
            self.update_loc()

        if sys_data['root']:
            # reconnects root locator to system according to data
            self.set_root(sys_data['root'])

        self.update_sys_data()

    def rebuild_sys(self):
        """
        Queries system data, deletes single system and rebuilds from data
        :return:
        """
        self.update_sys_data()
        mc.delete(self.sys_data['group'])
        self.rebuild_sys_from_data(self.sys_data)

    def reposition_system(self):
        root = mc.listConnections('{}.root'.format(self.sys_data['group']), s=True, d=False)[0]
        pass

    # LOAD SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def load_sys(self, system=''):
        group = system if system else mc.ls(sl=1)[0]
        self.load_sys_data(group)

    def load_sys_data(self, system=''):
        self.sys_data = eval(mc.getAttr('{}.metadata'.format(system)))

    def load_loc(self, loc=''):
        self.loc = loc if loc else mc.ls(sl=1)[0]
        self.load_loc_data()
        self.load_sys(self.loc_sys())

    def load_loc_data(self, data=''):
        data = data if data else mc.getAttr('{}.metadata'.format(self.loc))
        self.loc_data = eval(data)

    def load_env_data(self):
        self.environment_data = eval(mc.getAttr('{}.metadata'.format(self.environment_data['group'])))

    def list_systems(self):
        data = mc.listConnections('{}.sys_list'.format(self.environment_data['group']))
        return data

    def list_sys_locs(self, system=''):
        sys = system if system else self.sys_data['group']
        data = mc.listConnections('{}.loc_data'.format(sys))
        return data

    # UPDATE DATA SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def update_loc_data(self):
        parent = mc.listConnections('{}.parent'.format(self.loc), s=1, d=0)
        child = mc.listConnections('{}.child'.format(self.loc), s=0, d=1)

        self.loc_data.update({
            'name': self.loc,
            'parent': '' if parent is None else str(parent[0]),
            'child': '' if child is None else str(child[0]),
            'system_grp': self.loc_sys(),
            'position': {'t': mc.xform(self.loc, q=1, t=1, ws=1),
                         'r': mc.xform(self.loc, q=1, ro=1, ws=1),
                         's': mc.xform(self.loc, q=1, s=1, ws=1)},
            'index': self.loc_index(),
        })

        self.commit_data(self.loc, self.loc_data)

    def update_sys_data(self):
        members_data = self.sys_members_data()
        root = self.sys_root()
        parent = self.sys_parent()

        self.sys_data.update({
            'locators': members_data,
            'root': root,
            'sys_parent': parent})

        self.commit_data(self.sys_data['group'], self.sys_data)

    def update_template_data(self):
        self.environment_data['systems'] = self.template_members_data()
        self.commit_data(self.environment_data['group'], self.environment_data)

    def update_sys_locs_data(self):
        locators = self.sys_members()

        for loc in locators:
            self.load_loc(loc)
            self.update_loc_data()

        self.sys_data['locators'] = locators
        self.commit_data(self.sys_data['group'], self.sys_data)

    def update_loc(self):
        mc.xform(self.loc,
                 t=self.loc_data['position']['t'],
                 ro=self.loc_data['position']['r'],
                 ws=True)

        if self.loc_data['parent']:
            self.set_loc_parent(self.loc_data['parent'])

    # SET SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def commit_data(self, group, data):
        mc.setAttr('{}.metadata'.format(group), data, type='string')

    def set_root(self, loc_choice=''):
        """
        Connect and sets current loc/joint to root attribute
        """
        loc = loc_choice if loc_choice else self.loc
        mc.connectAttr('{}.metadata'.format(loc), '{}.root'.format(self.sys_data['group']))

    def set_loc_sys(self, system=''):
        """
        Changes loaded locator system
        :param system:
        """
        self.load_sys(self.loc_sys())
        mc.disconnectAttr('{}.system_grp'.format(self.loc), '{}.loc_list'.format(self.sys_data['group']),
                          nextAvailable=1)
        self.loc_data['system_grp'] = system if system else mc.ls(sl=1)[0]
        self.load_sys(self.loc_data['system_grp'])
        mc.connectAttr('{}.system_grp'.format(self.loc), '{}.loc_list'.format(self.sys_data['group']),
                       nextAvailable=True)

        loc_list = self.sys_members(self.loc_data['system_grp'])
        loc_index = get_next_index(loc_list)

        loc_name = '{}_'.format(self.loc_data['unique_name']) if self.loc_data['unique_name'] else ''
        name = '{}{}_{:02d}_loc'.format(loc_name, self.sys_data['name'], loc_index)
        self.loc = mc.rename(self.loc, name)
        mc.parent(self.loc, self.loc_data['system_grp'])

        self.update_loc_data()

    def set_loc_parent(self, parent=''):
        parent = parent if parent else mc.ls(sl=1)[0]
        mc.connectAttr('{}.child'.format(parent), '{}.parent'.format(self.loc))

    def set_loc_parent_sel_order(self):
        sel = mc.ls(sl=1)
        loc_dict = {}
        for n, loc in enumerate(sel):
            if loc == sel[-1]:
                break
            else:
                loc_dict.update({loc: sel[n+1]})

        for loc in loc_dict:
            self.load_loc(loc)
            self.set_loc_parent(loc_dict[loc])

    def set_loc_children(self):
        pass

    def set_loc_index(self, index):
        new_name = self.loc.replace('{:02d}'.format(self.loc_index()), '{:02d}'.format(index))
        self.loc = mc.rename(self.loc, new_name)
        self.update_loc_data()

        return new_name

    def set_sys_parent(self, loc=''):
        parent_loc = loc if loc else mc.ls(sl=1)[0]
        mc.connectAttr('{}.sys_child'.format(parent_loc), '{}.sys_parent'.format(self.sys_data['group']))

        self.update_sys_data()

    # GET SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def template_members(self):
        members = mc.listConnections('{}.sys_data'.format(self.environment_data['group']))
        return members

    def template_members_data(self):
        current_sys = self.sys_data['group']
        members = self.template_members()
        members_data = {}

        for member in members:
            self.load_sys(member)
            self.load_loc(self.sys_members()[0])
            self.update_sys_data()
            data = self.sys_data
            members_data.update({member: data})

        self.load_sys(current_sys)
        return members_data

    def sys_parent(self):
        parent = mc.listConnections('{}.sys_parent'.format(self.sys_data['group']), s=1, d=0)
        return '' if parent is None else parent[0]

    def sys_root(self):
        root = mc.listConnections('{}.root'.format(self.sys_data['group']), s=1, d=0)
        return '' if root is None else root[0]

    def sys_members_data(self):
        current_loc = self.loc
        members_data = {}

        for member in self.sys_members():
            self.load_loc(member)
            self.update_loc_data()
            members_data.update({member: self.loc_data})

        self.load_loc(current_loc)
        return members_data

    def sys_members(self, system=''):
        sys = system if system else self.sys_data['group']
        members = mc.listConnections('{}.loc_data'.format(sys))
        return members

    def loc_sys(self):
        sys = mc.listConnections('{}.metadata'.format(self.loc), s=0, d=1)
        return '' if sys is None else sys[0]

    def loc_parent(self):
        parent_query = mc.listConnections('{}.parent'.format(self.loc), s=1, d=0)
        return '' if parent_query is None else parent_query[0]

    def loc_index(self):
        name_split = self.loc.split('_')
        index = ''

        for word in name_split:
            if word.isdigit():
                index = int(word)

        return index

    def list_all_loc(self):
        pass

    # ACTION SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def check_root(self):
        pass

    def parent_template(self):
        """
        Parent all systems in template, including systems themselves
        """
        for sys in self.template_members():
            self.load_sys(sys)
            self.parent_sys()

            if self.sys_parent():
                mc.parentConstraint(self.sys_parent(), self.sys_data['root'], mo=True)
            else:
                continue

    def parent_sys(self):
        """
        Parent locators in system based on connection data
        """
        locators = self.sys_members()
        curve_grp = mc.group(em=True, name='{}_crv_grp'.format(self.sys_data['name']))
        mc.parent(curve_grp, self.sys_data['group'])

        for loc in locators:
            self.load_loc(loc)
            parent = self.loc_parent()
            offset_grp = add_offset_grp(loc)
            mc.parent(offset_grp, self.loc_sys())

            if parent:
                mc.parentConstraint(parent, offset_grp, mo=True)
                mc.scaleConstraint(parent, offset_grp, mo=True)

                # Creating connection line
                parent_tr = mc.xform(parent, q=True, t=True, ws=True)
                self_tr = mc.xform(self.loc, q=True, t=True, ws=True)
                bridge_line = mc.curve(d=True, p=[self_tr, parent_tr], name='{}_crv'.format(self.loc))
                mc.parent(bridge_line, curve_grp)
                mc.setAttr("{}.overrideEnabled".format(bridge_line), 1)
                mc.setAttr("{}.overrideDisplayType".format(bridge_line), 1)
                mc.skinCluster(self.loc, parent, bridge_line, toSelectedBones=True, bindMethod=0,
                               skinMethod=0, normalizeWeights=1)
            else:
                continue

    # def bridge_curve(self):
    #     if self.loc_parent():
    #         parent_tr = mc.xform(self.loc_parent(), q=True, t=True, ws=True)
    #         self_tr = mc.xform(self.loc, q=True, t=True, ws=True)
    #
    #         bridge_line = mc.curve(d=True, p=[self_tr, parent_tr], name='{}_crv'.format(self.loc))
    #         mc.parent(bridge_line, curve_grp)
    #
    #         mc.setAttr("{}.overrideEnabled".format(bridge_line), 1)
    #         mc.setAttr("{}.overrideDisplayType".format(bridge_line), 1)
    #         mc.skinCluster(self.loc, parent, bridge_line,
    #                        toSelectedBones=True,
    #                        bindMethod=0,
    #                        skinMethod=0,
    #                        normalizeWeights=1)

    def export_template_data(self):
        """
        Export system data to json for future reconstruction
        """
        # update and stores template data
        self.update_template_data()
        data = self.environment_data

        # queries project data path
        project_path = mc.workspace(q=True, rootDirectory=True)
        data_path = '{}data/'.format(project_path)
        # queries jason files in path
        files_in_path = glob.glob('{}*.json'.format(data_path))

        # check versions and defines latest name
        next_index = get_next_index(files_in_path) if files_in_path else 1
        file_name = 'tp_rigSystems_rigTemplate_{:02d}_data.json'.format(next_index)
        file_path = '{}{}'.format(data_path, file_name)

        # exports json file
        with open(file_path, 'w') as file_for_write:
            json.dump(data, file_for_write, indent=4)

    def import_template_data(self):
        """
        Imports latest json file from project data folder
        :return environment data from file:
        """
        # queries project data path
        project_path = mc.workspace(q=True, rootDirectory=True)
        data_path = '{}data/'.format(project_path)

        # queries jason files in path
        files_in_path = glob.glob('{}*.json'.format(data_path))
        latest = max(files_in_path, key=os.path.getctime)

        with open(latest, 'r') as file_for_read:
            self.environment_data = json.load(file_for_read)

    def reorder_indexes(self):
        """
        Reorder system indexes in selection order
        """
        pass


# import tpUtils as tp
# reload(tp)
#
# loc = tp.RigTemplate()
# loc.export_template_data()
# loc.import_template_data()
# loc.rebuild_template_from_data(loc.environment_data)
#
# loc.set_loc_parent_sel_order()
# loc.load_sys()
# loc.sys_members()
# loc.update_template_data()
# loc.load_loc()
# loc.update_loc()
# loc.new_sys('head')
#
# neck_loc = ['d1', 'd2', 'd3', 'd4', 'd5', 'd6']
# for item in neck_loc:
#     loc.new_loc(item)
#
# loc.new_loc('t4')
#
# loc.rebuild_template()
# loc.parent_template()
# loc.rebuild_sys()
# loc.parent_sys()
# loc.rebuild_sys_from_data(loc.sys_data)
# loc.list_systems()
#
# loc.sys_members()
# loc.sys_members_data()
# loc.update_sys_data()
# loc.update_loc_data()
# loc.update_template_data()
# loc.loc_set_index(3)
# loc.template_members()
# loc.template_members_data()
#
# loc.set_root()
# loc.loc
# loc.loc_data
#
# loc.set_loc_sys()
# loc.list_sys_locs()
# loc.set_sys_parent()
