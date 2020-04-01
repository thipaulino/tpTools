from __future__ import division
import maya.cmds as mc
import maya.cmds as cmds
import os
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import struct
import glob
import math

#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------

# FOLLICLE SECTION __________________________________________________________________

def sysFromEdgeLoop(egde, surface, name=""):
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
    surface_sys_data = follicleOnClosestPoint(surface, locator_list, name)
    # Group and organize system on Outliner

def follicleOnClosestPoint(surface, locator_list, name=""):

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

'''
# Locator on CV's - Select curve, run script
# locatorOnCVs()
'''
def locatorOnCVs(path_crv):
    cmds.select(cl=1)
    cv_list = cmds.getAttr(path_crv + '.cv[:]')
    locator_list = []

    for i, cv in enumerate(cv_list):
        locator = cmds.spaceLocator(n="{}_{:02d}_Loc".format(path_crv, i))
        cmds.xform(locator, t=cv)
        cmds.select(cl=1)

        locator_list.append(locator)

    return locator_list



'''
# Distribute follicles on surface + joints and controls
'''
# follicle2D(name="testFlc", rows=10.0, colums=10.0, widthPercentage=1, hightPercentage=1)

def follicle2D(name="", rows=3, colums=3, widthPercentage=1, hightPercentage=1):
    """ Distribute follicles in a 2D array of a polygon surface"""

    # If colums/rows equals 1, position in center
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
    #Create a follicle
    follicleShape = cmds.createNode('follicle')
    #Get the transform of the follicle
    follicleTrans = cmds.listRelatives(follicleShape, parent=True)[0]
    #Rename the follicle
    follicleTrans = cmds.rename(follicleTrans, name)
    follicleShape = cmds.rename(cmds.listRelatives(follicleTrans, c=True)[0], (name + 'Shape'))

    #If the inputSurface is of type 'nurbsSurface', connect the surface to the follicle
    if cmds.objectType(inputSurface[0]) == 'nurbsSurface':
        cmds.connectAttr((inputSurface[0] + '.local'), (follicleShape + '.inputSurface'))
    #If the inputSurface is of type 'mesh', connect the surface to the follicle
    if cmds.objectType(inputSurface[0]) == 'mesh':
        cmds.connectAttr((inputSurface[0] + '.outMesh'), (follicleShape + '.inputMesh'))

    #Connect the worldMatrix of the surface into the follicleShape
    cmds.connectAttr((inputSurface[0] + '.worldMatrix[0]'), (follicleShape + '.inputWorldMatrix'))
    #Connect the follicleShape to it's transform
    cmds.connectAttr((follicleShape + '.outRotate'), (follicleTrans + '.rotate'))
    cmds.connectAttr((follicleShape + '.outTranslate'), (follicleTrans + '.translate'))
    #Set the uValue and vValue for the current follicle
    cmds.setAttr((follicleShape + '.parameterU'), uVal)
    cmds.setAttr((follicleShape + '.parameterV'), vVal)
    #Lock the translate/rotate of the follicle
    cmds.setAttr((follicleTrans + '.translate'), lock=True)
    cmds.setAttr((follicleTrans + '.rotate'), lock=True)

    #If it was set to be hidden, hide the follicle
    if hide:
        cmds.setAttr((follicleShape + '.visibility'), 0)
    #If a scale-group was defined and exists
    if scaleGrp and cmds.objExists(scaleGrp):
        #Connect the scale-group to the follicle
        cmds.connectAttr((scaleGrp + '.scale'), (follicleTrans + '.scale'))
        #Lock the scale of the follicle
        cmds.setAttr((follicleTrans + '.scale'), lock=True)
    #Return the follicle and it's shape
    return follicleTrans, follicleShape

'''
# Place locator in object center
import maya.cmds as cmds

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
'''

'''
# Multi connect Attributes
list1_attr = cmds.ls(sl=1)
list2_attr = cmds.ls(sl=1)

for n, i in enumerate(list1_attr):
    cmds.connectAttr(i + '.translate', list2_attr[n] + '.translate')
    cmds.connectAttr(i + '.rotate', list2_attr[n] + '.rotate')
    cmds.connectAttr(i + '.scale', list2_attr[n] + '.scale')
'''

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

'''
# Parent in selection order
'''
def parentInOrder(sel):
    for z, i in enumerate(sel):
        cmds.parent(sel[z+1], i)
        if z+1 >= len(sel)-1: break

"""
# Create joint chain from edge selection
# Under contruction
def chainFromEdge(reverse=0, crvOnly=0):
    sel = cmds.sl(ls=1)
    
    polyToCurve -form 2 -degree 3 -conformToSmoothMeshPreview 1 #mel
    curveDeg = cmds.getAttr(v_curve_shape + ".degree")
    curveSpa = cmds.getAttr(v_curve_shape + ".spans")
    # CV's = degrees + spans
    cvCount = curveDeg + curveSpa
    
    # Deletes extra cvs, rebuilds curve, del hist, unparent curve
    cmds.delete(v_curve[0] + '.cv[{}]'.format(cvCount-2), v_curve[0] + '.cv[1]')
    cmds.rebuildCurve(v_curve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=1, kt=0, d=1, tol=0.01)
    cmds.rebuildCurve(v_curve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=1, kt=0, d=3, tol=0.01)
    
    cv_list = cmds.getAttr(path_crv + '.cv[:]')
    
    for i, cv in enumerate(cv_list):
        ctrl = tp_staticCtrl('ctrl_cv' + str(i))
        cmds.xform(ctrl[1], t= cv)
"""


# CONTROL SECTION __________________________________________________________________

def bd_buildCtrl(ctrl_type="circle", name="", sufix="_Ctrl", scale=1, spaced=1, offset=0):
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

    shapes = cmds.listRelatives(c1, f = True, s=True)
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


def create_ctrl(name, position=(0,0,0), rotation=(0,0,0)):
    """
    Creates circular control and positions on given coordenates
    :param name:
    :param position:
    :param rotation:
    :return ctrl_list:
    """
    ctrl = cmds.circle(n=name, c=(0,0,0), nr=(1,0,0), r=1, ch=0)[0]
    spaceGrp = cmds.group(ctrl, n=name + '_Grp')
    cmds.xform(spaceGrp, t=position, ro=rotation)
    pack = [ctrl, spaceGrp]

    return pack

def placeOnEachSel(type="circle", scale=1, spaced=1):
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

        control = bd_buildCtrl(ctrl_type=type, name=i, scale=scale, spaced=spaced)

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


'''
# Controls on CV's
path_crv = cmds.ls(sl=1)[0]
cv_list = cmds.getAttr(path_crv + '.cv[:]')

for i, cv in enumerate(cv_list):
    ctrl = tp_staticCtrl('ctrl_cv' + str(i))
    cmds.xform(ctrl[1], t= cv)
'''


def placeOnEach_cluster(name="", type="circle", scale=1, color=(1,1,1), parentConstraint=0):
    """
    Control on each Cluster selection
    :param name:
    :param type:
    :param scale:
    :param color:
    :param parentConstraint:
    :return:
    """
    sel = cmds.ls(sl=1)

    for n, i in enumerate(sel):
        cls_shape = cmds.listRelatives(i, type="shape")
        cls_tr = cmds.getAttr(cls_shape[0] + ".origin")[0]

        new_ctrl = bd_buildCtrl(ctrl_type=type, name=i, sufix="_Ctrl".format(n), scale=scale, spaced=1, offset=0)
        setCtrlColor(new_ctrl[0], color = color)
        cmds.xform(new_ctrl[1], t=cls_tr)
        if parentConstraint == 1: cmds.parentConstraint(new_ctrl[0], i, mo=1)


def placeOnEach_joint(name, scale=1, color=(1,1,1), parentConstraint=0):
    """
    Control on each Joint selection
    :param name:
    :param scale:
    :param color:
    :param parentConstraint:
    :return:
    """
    sel = cmds.ls(sl=1)

    for n, i in enumerate(sel):
        position = cmds.xform(i, q=1, t=1, ws=1)
        rotation = cmds.joint(i, q=1, o=1)
        new_ctrl = bd_buildCtrl(ctrl_type="circle", name=name, sufix="_Ctrl{}".format(n), scale=scale, spaced=1, offset=0)
        setCtrlColor(new_ctrl[0], color = color)
        cmds.xform(new_ctrl[1], t=position, ro=rotation)
        if parentConstraint == 1: cmds.parentConstraint(new_ctrl[0], i, mo=1)

def parent_FkOrder():
    """
    Parents in FK Order - Select Ctrl Grps, Last to First
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


def createCtrl(name, position=(0,0,0), rotation=(0,0,0)):
    """
    # Creates circular control and positions on given coordenates
    :param name:
    :param position:
    :param rotation:
    :return:
    """
    ctrl = cmds.circle(n=name, c=(0,0,0), nr=(1,0,0), r=1, ch=0)[0]

    spaceGrp = cmds.group(ctrl, n=name + '_Grp')
    cmds.xform(spaceGrp, t=position, ro=rotation)
    pack = [ctrl, spaceGrp]

    return pack

'''
# Parent two lists
list1 = cmds.ls(sl=1)
list2 = cmds.ls(sl=1)

for n, i in enumerate(list1):
    cmds.parentConstraint(i, list2[n])
'''


def cubeOverGeo():
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

# Creates snapshots from "front, right_side, back, left_side, quarter_left, quarter_right" - Saves to Desktop
# snapshotMachine(objDistance=100, height=25, sideOffset=0, widthHight=(1920,1080))
# Add turn on Anti Alias
# setAttr "hardwareRenderingGlobals.lineAAEnable" 1;
# setAttr "hardwareRenderingGlobals.multiSampleEnable" 1;


def snapshotMachine(objDistance=100, height=30, sideOffset=0, widthHight=(1000,500)):
    camera = cmds.camera(n="tempCam")
    pivot_grp = cmds.group(camera, n="pivot_grp")
    cmds.xform(camera, t=(sideOffset, height, objDistance))

    view = OpenMayaUI.M3dView.active3dView()
    cam = OpenMaya.MDagPath()
    view.getCamera(cam)
    current_cam_shape = cam.partialPathName()
    current_cam = cmds.listRelatives(current_cam_shape, type="transform", p=1)

    filepath = cmds.file(q=True, sn=True)
    filename = os.path.basename(filepath)
    raw_name, extension = os.path.splitext(filename)

    cmds.lookThru(camera)

    cam_angle = {'front':0, 'right_side':90, 'back':180, 'left_side':270, 'quarter_left':45, 'quarter_right':315}
    user_path = os.environ["HOMEPATH"]

    for i in cam_angle:
        cmds.xform(pivot_grp, ro=(0,cam_angle[i],0))
        cmds.playblast(orn=0, fr=1, p=100, v=0, fo=1, fmt="image", compression="jpg", wh=widthHight,
                       f="C:{}\\Desktop\\{}_{}".format(user_path, raw_name, i))

    cmds.lookThru(current_cam)
    cmds.delete(pivot_grp)


# Image resize function
# resizeImage('<sourceImage.png>','<outputImage.png>', 800, 600)
def resizeImage(sourceImage, outputImage, width, height):

    image = om.MImage()
    image.readFromFile(sourceImage)

    image.resize( width, height )
    image.writeToFile( outputImage, 'png')


'''
# BlendShape with output geo name and envelope to 1
my_string = cmds.ls(sl=1)[1]
blnd_name = my_string.split("_CH",1)[0] 

blnd_node = cmds.blendShape(automatic=1, n="{}_FinalOutput_BlendShape".format(blnd_name))
# Gets number of shapes - Sets all weights to 1
blnd_weights = cmds.blendShape(blnd_node, q=True, w=1)
for y, z in enumerate(blnd_weights): cmds.blendShape(blnd_node, edit=1, w=[(y, 1.0)])
'''


# bd_blendLists("_Lattice", 1)
def bd_blendLists(tag, addTarg=0):
    """ Bardel Reference Geo
    BlandShapes Rig Geo to Reference geo
    """

    listB = cmds.ls(sl=1)
    reference_dict = {}

    for i in listB:
        # Name search based on current naming structure
        name_split = i.split(":", 1)
        blend_name = name_split[1].split("_Geo", 1)
        new_name = blend_name[0] + tag + "_Com_Geo" + blend_name[1]

        # Getting blendShape node
        # Note - In this rig, all ref geo is being controlled by a joint
        # Therefore - going through skinCluster to find blendShape node
        shapes = cmds.listRelatives(i, s=1)
        skinCluster = cmds.listConnections(shapes[1], type="skinCluster")
        blend_node = cmds.listConnections(skinCluster[0], type="blendShape")

        reference_dict.update({new_name: [i, blend_node]})

    for i in reference_dict:
        # Change sufix in case it's character or else
        blend_name = blnd_name = i.split("_PR", 1)[0]

        if addTarg == 0:
            blend_node = cmds.blendShape(i, reference_dict[i][0], automatic=1, n="{}_End_BlendShape".format(blend_name))
            blend_weights = cmds.blendShape(blend_node, q=True, w=1)
        else:
            cmds.blendShape(reference_dict[i][1], e=1, t=(reference_dict[i][0], 1, i, 1.0))
            blend_node = reference_dict[i][1]
            blend_weights = cmds.blendShape(reference_dict[i][1], q=True, w=1)
        # Gets number of shapes - Sets all weights to 1
        for y, z in enumerate(blend_weights): cmds.blendShape(blend_node, edit=1, w=[(y, 1.0)])

'''
import maya.cmds as cmds
from maya.mel import eval

cmds.setAttr('defaultResolution.aspectLock', 0)
cmds.setAttr('defaultResolution.width', 1920)
cmds.setAttr('defaultResolution.height', 1080)
cmds.select('defaultResolution')
eval('ToggleAttributeEditor')
eval('checkAspectLockHeight2 "defaultResolution"')
eval('checkAspectLockWidth2 "defaultResolution"')
'''

#-------------------------------------------------------------------------------
# Name:        get_image_size
# Purpose:     extract image dimensions given a file path using just
#              core modules
#
# Author:      Paulo Scardine (based on code from Emmanuel VAISSE)
#
# Created:     26/09/2013
# Copyright:   (c) Paulo Scardine 2013
# Licence:     MIT
#-------------------------------------------------------------------------------
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


class swapOutputRefGeo_v1():

    def __init__(self):
        self.ref_geo = cmds.ls(sl=1)
        self.connect_dict = {}

        for i in self.ref_geo:
            geo_shape = cmds.listRelatives(i, s=1)[0]
            blend_output = cmds.listConnections(geo_shape, type="blendShape", source=1, p=1)[0]
            geo_input = cmds.listConnections(geo_shape, type="blendShape", source=1, c=1)[0]

            self.connect_dict.update({blend_output: geo_input})

    def breakConnections(self):
        for i in self.connect_dict:
            cmds.disconnectAttr(i, self.connect_dict[i])

    def reconnect(self):
        for i in self.connect_dict:
            cmds.connectAttr(i, self.connect_dict[i])

# cookie = swapOutputRefGeo()
# cookie.breakConnections()
# cookie.reconnect()


class swapOutputRefGeo_v4():
    """ Updates output reference geo as long as the only input are blendShapes"""

    def __init__(self):
        self.ref_geo = cmds.ls(sl=1)
        self.connect_dict = {}
        self.blend_nodes = []

        for i in self.ref_geo:
            # Getting Geo and BlendShape node information
            geo_shape = cmds.listRelatives(i, s=1)[0]
            blend_node = cmds.listConnections(geo_shape, type="blendShape")[0]
            geo_input = cmds.listConnections(blend_node, d=0, type='shape')[0]

            # Getting shader information
            cmds.select(i, r=1)
            cmds.hyperShade(shaderNetworksSelectMaterialNodes=True)
            shader = cmds.ls(sl=1)[0]
            cmds.select(cl=1)

            self.connect_dict.update({i: [geo_input, shader]})
            self.blend_nodes.append(blend_node)

        # Getting main Geo connections - visibility etc..
        cmds.select(self.connect_dict.keys())
        connection_list = cmds.listConnections(cmds.ls(sl=1), c=1, p=1, d=0)
        self.output_attr_list = connection_list[1::2]
        self.input_attr_list = connection_list[::2]

    def delete_blends(self):
        cmds.delete(self.blend_nodes)

    def removeRefs(self):
        for ref in self.ref_geo:
            reference_file = cmds.referenceQuery(ref, f=1)
            cmds.file(ref, rr=1)

    def re_blend(self):
        for i in self.connect_dict:
            # BlendShapes section
            blnd_name = i.split("_CH",1)[0]

            blnd_node = cmds.blendShape(self.connect_dict[i][0], i, automatic=1, n="{}_End_BlendShape".format(blnd_name))
            # Gets number of shapes - Sets all weights to 1
            blnd_weights = cmds.blendShape(blnd_node, q=True, w=1)
            for y, z in enumerate(blnd_weights): cmds.blendShape(blnd_node, edit=1, w=[(y, 1.0)])

            # Re-assigning shaders
            cmds.select(i)
            cmds.hyperShade(assign=self.connect_dict[i][1])
            cmds.select(cl=1)

        # Re-connect attributes
        for i, z in zip(self.output_attr_list, self.input_attr_list):
            try:
                cmds.connectAttr(str(i), str(z), f=1)
            except: pass

# cookie_13 = swapOutputRefGeo_v4()
# cookie_13.delete_blends()
# cookie_13.removeRefs()
# cookie_13.re_blend()


class replaceReference():

    def __init__(self):
        self.geo_list = []
        self.geo_data = {}
        self.shader_data = {}

    def load_data(self):
        """ This method querys the geo, name space and deletes name space

        Usage:
            - In Reference Editor, from desired reference, Import Objects From Reference
            - Select all desired Geo -> Run load_data()

        """

        self.geo_list = cmds.ls(sl=1)

        for geo in self.geo_list:
            root_geo = geo.split(":")[1]
            self.geo_data.update({geo:root_geo})

            # Getting shader information
            cmds.select(geo, r=1)
            cmds.hyperShade(shaderNetworksSelectMaterialNodes=True)
            shader = cmds.ls(sl=1)[0]
            cmds.select(cl=1)
            self.shader_data.update({geo + "_Shader":shader})

        namespace = self.geo_list[0].split(":")[0]
        cmds.namespace(rm=namespace, mergeNamespaceWithRoot=1)

    def reconnect(self):

        for geo in self.geo_data:
            # BlendShapes section
            name_edit = self.geo_data[geo].split("_")
            del name_edit[-3:-1]
            blendShape_name = "_".join(name_edit)

            blnd_node = cmds.blendShape(self.geo_data[geo], geo, automatic=1, n="{}_End_BS".format(blendShape_name))
            # Gets number of shapes - Sets all weights to 1
            blnd_weights = cmds.blendShape(blnd_node, q=True, w=1)
            for y, z in enumerate(blnd_weights): cmds.blendShape(blnd_node, edit=1, w=[(y, 1.0)])

            # Re-assigning shaders
            cmds.select(geo)
            cmds.hyperShade(assign=self.shader_data[geo + "_Shader"])
            cmds.select(cl=1)

class replaceReference_v2():
    """ This class has the goal of turning current Reference output Geo
    into rig common geo, importing the latest reference and
    blendShaping previews geo to new refernce geo.

    Usage:
        - Select desired Reference Geo only (no groups, deformers, etc.)
        - Create class instance
        - Excecute self.run()
    """

    def __init__(self):
        """ All global variables"""
        self.geo_list = []
        self.geo_data = {}
        self.shader_data = {}
        self.ref_dir = ""
        self.ref_namespace = ""

    def load_data(self):
        """
        Queries:
            Geo name, namespace, assigned shaders, reference directory, reference namespace
        Actions:
            Import Objects from Reference, deletes namespace
        """
        # Get geo selection
        self.geo_list = cmds.ls(sl=1)

        for geo in self.geo_list:
            # Separates geo name and namespace
            root_geo = geo.split(":")[1]
            # Stores both in dict
            self.geo_data.update({geo:root_geo})

            # Getting shader information
            cmds.select(geo, r=1)
            cmds.hyperShade(shaderNetworksSelectMaterialNodes=True)
            shader = cmds.ls(sl=1)[0]
            cmds.select(cl=1)
            self.shader_data.update({geo + "_Shader":shader})

        # Get reference directory
        ref_name = cmds.referenceQuery(self.geo_list[0], filename=1)
        ref_path_split = ref_name.split("/")
        del ref_path_split[-1]
        # Stores directory
        self.ref_dir = "/".join(ref_path_split) + "/"
        # Stores currenct Namespace
        self.ref_namespace = self.geo_list[0].split(":")[0]
        # Import Objects from Reference - reference gone
        cmds.file(ref_name, importReference=True)

        # Deletes namespce - Merge with root
        namespace = self.geo_list[0].split(":")[0]
        cmds.namespace(rm=namespace, mergeNamespaceWithRoot=1)

    def import_latest(self):
        # Get latest file from previews reference directory
        list_of_files = glob.glob(self.ref_dir + "*.ma")
        latest_file = max(list_of_files, key=os.path.getctime)

        # Import new reference
        cmds.file(latest_file, r=True, namespace=self.ref_namespace)

    def reconnect(self):
        """ BlendShapes old geo to new reference """
        for geo in self.geo_data:
            # Cleans Geo name for blendShape node creation
            name_edit = self.geo_data[geo].split("_")
            del name_edit[-3:-1]
            blendShape_name = "_".join(name_edit)

            # Blending old rig geo to new reference
            blnd_node = cmds.blendShape(self.geo_data[geo], geo, automatic=1, n="{}_End_BS".format(blendShape_name))
            # Gets number of targets - Sets all weights to 1
            blnd_weights = cmds.blendShape(blnd_node, q=True, w=1)
            for y, z in enumerate(blnd_weights): cmds.blendShape(blnd_node, edit=1, w=[(y, 1.0)])

            # Re-assigning shaders
            cmds.select(geo)
            cmds.hyperShade(assign=self.shader_data[geo + "_Shader"])
            cmds.select(cl=1)

            # Rename commmon geo
            cmds.rename(self.geo_data[geo], "Bind_" + self.geo_data[geo])

    def renameAll(self):
        main_grp = cmds.ls(sl=1)
        all_children = cmds.listRelatives(main_grp, children=1, type='transform', ad=1)

        for i in all_children:
            prefix = i.split("_")[0]
            if prefix != "Bind": cmds.rename(i, "Bind_" + i)

        cmds.rename(main_grp, "Bind_" + main_grp)

    def run(self):
        self.load_data()
        self.import_latest()
        self.reconnect()

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

def getClosestVertex_v2(mayaMesh, pos=[0,0,0]):
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
def getClosestVertex(mayaMesh, pos=[0,0,0]):
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
    #============

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

def remoteLoc_allJoints(selection):
    """
    Creates and places joints on each selection
    :param selection:
    :return List of joints created:
    """
    parent_dict = {}

    # Store hierarchy position for every joint
    for i in selection:
        try: parent_dict.update({i: cmds.listRelatives(i, parent=1)[0]})
        except: continue

    # Unparent all joints - parent to world
    cmds.parent(selection, w=1)
    cmds.select(cl=1)
    remoteCtrl_list = []

    for joint in selection:
        # Get joint data
        translate = cmds.xform(joint, q=1, t=1, ws=1)
        rotate = cmds.joint(joint, q=1, o=1)
        scale = cmds.xform(joint, q=1, s=1)

        # Set name for loc based on joint
        new_name = joint.replace("_Jnt", "_RemoteCtrl_Loc")
        # Create locator and space grp
        remote_loc = cmds.spaceLocator(n=new_name)[0]
        remoteCtrl_grp = cmds.group(remote_loc, n=remote_loc + "_Grp")
        # Place locator grp on joint position
        cmds.xform(remoteCtrl_grp, t=translate, ro=[rotate[2], rotate[1]*-1+180, rotate[0]], s=scale)
        # Append new locator to list
        remoteCtrl_list.append(remote_loc)

    for joint in parent_dict:

        cmds.parent(joint, parent_dict[joint])
        cmds.parent(joint.replace("_Jnt", "_RemoteCtrl_Loc_Grp"), parent_dict[joint].replace("_Jnt", "_RemoteCtrl_Loc"))
        cmds.parentConstraint(joint.replace("_Jnt", "_RemoteCtrl_Loc"), joint)

    return remoteCtrl_list, parent_dict


def rename_sel(old, new):
    sel = mc.ls(sl=1)

    for item in sel:
        name = item.replace(old, new)
        mc.rename(item, name)


def list_unique(list):
    """
    Find unique items in a list
    :param list:
    :return unique items list:
    """
    unique_list = []

    # traverse for all elements
    for x in list:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)

    return unique_list

def poleVector_math(dist=0.5):
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


class RigTemplate:

    """
    Class development:
        create template group dict
        parent system
        parent template
        rebuild system
        line between locators
        export system
        import system
        export/import all
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
                'locators': {}},

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
                'joint': ''},

            'tag_data': {
                'creation_date': '',
                'last_modified': '',
                'original_file': '',
                'class_version': '',
                'id': '',
                'credits': 'Create By Thiago Paulino'}}

        self.init_template_sys()

    def init_template_sys(self):
        """
        Initializes system by searching for tag for tp_rigSystems_rigTemplate tag and getting environment
        if nonexistent, creates tag and environment
        :return:
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

    # NEW STUFF SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def new_environment(self):
        """
        Creates new group for all template systems with necessary attributes
        Connects to tag group for easy class access
        :return:
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
        self.sys_data = self.data_templates['sys_data']
        self.sys_data['name'] = name if name else 'tempName'
        self.sys_data['group'] = mc.group(name='{}_sys_grp'.format(name), empty=True)
        mc.parent(self.sys_data['group'], self.environment_data['group'])

        mc.addAttr(self.sys_data['group'], longName='metadata', dataType='string')
        mc.addAttr(self.sys_data['group'], longName='loc_data', dataType='string', multi=True,
                   indexMatters=False)

        mc.connectAttr('{}.metadata'.format(self.sys_data['group']),
                       '{}.sys_data'.format(self.environment_data['group']),
                       nextAvailable=True)

        self.commit_data(self.sys_data['group'], self.sys_data)

    def new_loc(self, unique_name='', index='', system=''):
        """
        Creates new template locator with metadata attribute
        """
        if system:
            self.load_sys(system)

        if index:
            loc_index = index
        else:
            loc_list = self.list_sys_locs()
            loc_index = 1 if loc_list is None else get_next_index(loc_list)

        loc_name = '{}_'.format(unique_name) if unique_name else ''
        name = '{}{}_{:02d}_loc'.format(loc_name, self.sys_data['name'], loc_index)

        self.loc = mc.spaceLocator(name=name)[0]
        mc.addAttr(self.loc, longName='metadata', dataType='string')
        mc.addAttr(self.loc, longName='system_grp', attributeType='message')
        mc.addAttr(self.loc, longName='parent', attributeType='message')
        mc.addAttr(self.loc, longName='child', attributeType='message')
        mc.connectAttr('{}.metadata'.format(self.loc), '{}.loc_data'.format(self.sys_data['group']),
                       nextAvailable=True)

        self.loc_data = self.data_templates['loc_data']
        self.loc_data.update({
            'unique_name': unique_name,
            'system_grp': self.sys_data['group'],
            'system_plug': mc.listConnections('{}.metadata'.format(self.loc), d=1, s=0, p=1)[0].split('.')[1],
            'name': self.loc})
        self.commit_data(self.loc, self.loc_data)

        mc.parent(self.loc, self.sys_data['group'])

    def load_sys(self, system=''):
        if system:
            self.sys_data['group'] = system
        else:
            self.sys_data['group'] = mc.ls(sl=1)[0]

        self.load_sys_data()

    def load_loc(self, loc=''):
        self.loc = loc if loc else mc.ls(sl=1)[0]
        self.load_loc_data()
        self.load_sys(self.loc_sys())

    def load_loc_data(self, data=''):
        data = data if data else mc.getAttr('{}.metadata'.format(self.loc))
        self.loc_data = eval(data)

    def list_systems(self):
        data = mc.listConnections('{}.sys_list'.format(self.environment_data['group']))
        return data

    def list_sys_locs(self, system=''):
        sys = system if system else self.sys_data['group']
        data = mc.listConnections('{}.loc_data'.format(sys))
        return data

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

        loc_list = self.list_sys_locs(self.loc_data['system_grp'])
        loc_index = get_next_index(loc_list)

        loc_name = '{}_'.format(self.loc_data['unique_name']) if self.loc_data['unique_name'] else ''
        name = '{}{}_{:02d}_loc'.format(loc_name, self.sys_data['name'], loc_index)
        self.loc = mc.rename(self.loc, name)
        mc.parent(self.loc, self.loc_data['system_grp'])

        self.update_loc_data()

    # UPDATE DATA SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def update_loc_data(self):
        parent = mc.listConnections('{}.parent'.format(self.loc), s=1, d=0)
        child = mc.listConnections('{}.child'.format(self.loc), s=0, d=1)

        self.loc_data.update({
            'name': self.loc,
            'unique_name': self.loc_data['unique_name'],
            'parent': '' if parent is None else str(parent[0]),
            'child': '' if child is None else str(child[0]),
            'system_grp': self.loc_sys(),
            'position': {'t': mc.xform(self.loc, q=1, t=1, ws=1),
                         'r': mc.xform(self.loc, q=1, ro=1, ws=1),
                         's': mc.xform(self.loc, q=1, s=1, ws=1)},
            'index': self.loc_index(),
            'ref_vertex': self.loc_data['ref_vertex'],
            'joint': self.loc_data['joint']
        })

        self.commit_data(self.loc, self.loc_data)

    def update_sys_data(self):
        current_loc = self.loc
        data_dict = {}
        data_array = mc.listAttr('{}.loc_data'.format(self.sys_data['group']), multi=1)

        for plug in data_array:
            loc = mc.listConnections('{}.{}'.format(self.sys_data['group'], plug), s=1, d=0)[0]
            self.load_loc(loc)
            self.update_loc_data()
            loc_data = eval(mc.getAttr('{}.{}'.format(self.sys_data['group'], plug)))
            data_dict.update({loc: loc_data})

        self.sys_data['locators'] = data_dict
        self.commit_data(self.sys_data['group'], self.sys_data)
        self.load_loc(current_loc)

    def update_template_data(self):
        pass

    def refresh_loc(self):
        pass

    def update_sys_locs_data(self):
        locators = self.list_sys_locs()

        for loc in locators:
            self.load_loc(loc)
            self.update_loc_data()

        self.sys_data['locators'] = locators
        self.commit_data(self.sys_data['group'], self.sys_data)

    def parent_template_sys(self):
        pass

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

    def loc_sys(self):
        sys = mc.listConnections('{}.metadata'.format(self.loc), s=0, d=1)[0]
        return sys

    def loc_parent(self):
        parent_query = mc.listConnections('{}.parent'.format(self.loc), s=1, d=0)
        parent = '' if parent_query is None else parent_query[0]
        return parent

    def loc_index(self):
        name_split = self.loc.split('_')
        index = ''

        for word in name_split:
            if word.isdigit():
                index = int(word)

        return index

    def set_loc_index(self, index):
        new_name = self.loc.replace('{:02d}'.format(self.loc_index()), '{:02d}'.format(index))
        self.loc = mc.rename(self.loc, new_name)
        self.update_loc_data()

        return new_name

    def parent_all(self):
        pass

    def parent_sys(self):
        locators = self.list_sys_locs()

        for loc in locators:
            self.load_loc(loc)
            parent = self.loc_parent()
            offset_grp = add_offset_grp(loc)
            mc.parent(offset_grp, self.loc_sys())

            if parent:
                mc.parentConstraint(parent, offset_grp, mo=True)
            else:
                continue

    def unparent_chain(self, system):
        pass

    def load_env_data(self):
        self.environment_data = eval(mc.getAttr('{}.metadata'.format(self.environment_data['group'])))

    def load_sys_data(self):
        self.sys_data = eval(mc.getAttr('{}.metadata'.format(self.sys_data['group'])))

    def commit_data(self, group, data):
        mc.setAttr('{}.metadata'.format(group), data, type='string')

    def update_grp_data(self):
        pass

    def export_template_data(self, system):
        """
        Export system data to json for future reconstruction
        """
        pass

    def import_template_data(self):
        pass

    def rebuild_from_data(self, data):
        pass

    def rebuild_sys(self):
        self.update_sys_data()

        self.temp_sys_data = self.sys_data
        mc.delete(self.sys_data['group'])
        self.new_sys(self.sys_data['name'])

        for loc in self.temp_sys_data['locators']:
            self.new_loc(self.temp_sys_data['locators'][loc]['unique_name'],
                         index=self.temp_sys_data['locators'][loc]['index'])
            self.loc_data = self.temp_sys_data['locators'][loc]
            self.commit_data(self.loc, self.loc_data)

        for loc in self.list_sys_locs():
            self.load_loc(loc)
            self.update_loc()

        self.update_sys_data()

    def update_loc(self):
        mc.xform(self.loc,
                 t=self.loc_data['position']['t'],
                 ro=self.loc_data['position']['r'],
                 ws=True)

        if self.loc_data['parent']:
            self.set_loc_parent(self.loc_data['parent'])

    def rebuild_loc_from_data(self, data):
        self.loc_data = data
        pass

    def reorder_indexes(self):
        """
        Reorder system indexes in selection order
        """
        # locators = self.list_sys_locs()
        pass

    def list_all_loc(self):
        pass


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
