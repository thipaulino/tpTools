#-------------------------------------------------------------------------------
# Name:        tp_autoLid v2.0
# Purpose:     Creates eyelid system based on given data:
#              - Eyeball Center Locator - Master Control - Look Control
#              - Superior Eyelid EdgeLoop - Superior Eyelid EdgeLoop
#
# Author:      Thiago Paulino
# Reference:   Marco Giordano
# 
# Location:    Vancouver, BC
# Contact:     tpaulino.com@gmail.com
# Created:     11/14/2019
# Copyright:   (c) Thiago Paulino 2019
# Licence:     MIT
#-------------------------------------------------------------------------------

from __future__ import division
import maya.api.OpenMaya as om2
import maya.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel
import math

'''
DEV LIST
    - Group everything at the end
    - Create look and master Ctrl
    - Or - Ask for control to assign attributes

    - Group curves in system group
    - Change bind joint names and number position - skip 0
    - Change bind joint group name
    - Parent ctrl joint group to system group
    - Group inferior and superior systen groups
    - Group left and rigth system groups
    - Group Eyelid Ctrl Grps
    - Parent blink controls to main control group
    - Add locators to system group
    - Unify eyelid corner controls
    - Add blink contols to attributes
    - Create square ctrls around look ctrls
    - Change blink target curve names
    - Rename all created nodes and deformers
    - remove joints from inside locators
    
    - Separate top and bottom controls effect on blink # DONE
    - Change ctrl color L R
    - Hide main system group
    
    PLUS
    - Make system deletable

'''

"""
l_eye = tp_autoLid()
l_eye.run()
"""


class tp_autoLid:

    def __init__(self):
        self.sys_name = "Eyelid"
        self.sys_side = "L_"

        self.sup_edge = []
        self.inf_edge = []
        self.center_loc = []

        self.look_ctrl = []
        self.master_ctrl = []

        self.cv_amount = 5.0
        self.ctrl_amount = 5.0
        self.ctrl_type = 2 # Sphere
        self.ctrl_radius = 0.2

        self.attr = {
            "sys_name": "string",
            "sys_side": "string",
            "sup_edge": "string",
            "inf_edge": "string",
            "center_loc": "string",
            "cv_amount": "float",
            "ctrl_amount": "float",
            "ctrl_type": "integer",
            "ctrl_radius": "float"}

        if cmds.objExists(self.sys_name + "_BuildPack"): 
            self.buildpack = self.sys_name + "_BuildPack"
            self.load_data()
        else:
            self.buildpack = createBuildPack(self.attr, self.sys_name)

    def load_data(self):
        buildPack = self.buildpack
        self.sys_name = cmds.getAttr(buildPack + ".sys_name")
        self.sys_side = cmds.getAttr(buildPack + ".sys_side")

        self.sup_edge = cmds.getAttr(buildPack + ".sup_edge").split(",")
        self.inf_edge = cmds.getAttr(buildPack + ".inf_edge").split(",")
        self.center_loc = cmds.getAttr(buildPack + ".center_loc")

        self.cv_amount = cmds.getAttr(buildPack + ".cv_amount")
        self.ctrl_amount = cmds.getAttr(buildPack + ".ctrl_amount")
        self.ctrl_type = cmds.getAttr(buildPack + ".ctrl_type") # Sphere
        self.ctrl_radius = cmds.getAttr(buildPack + ".ctrl_radius")

    def run(self):

        build_lid_sys(self.center_loc, self.sys_side, self.sys_name, self.sup_edge, 
                        self.inf_edge, self.cv_amount, self.ctrl_amount, self.ctrl_type, self.ctrl_radius)


"""
eyebrow = tp_autoBrow()
eyebrow.sys_name = "Orbicularis_Oculi"
eyebrow.sys_side = "L_"

eyebrow.edge_list = cmds.ls(sl=1)
eyebrow.center_loc = cmds.ls(sl=1)[0]

eyebrow.cv_amount = 10.0
eyebrow.ctrl_amount = 10.0
eyebrow.ctrl_type = 2 # Sphere
eyebrow.ctrl_radius = 0.2

eyebrow.run()
"""


class tp_autoBrow():
    def __init__(self):
        self.sys_name = "Eyebrow"
        self.sys_side = "L_"

        self.edge_list = []
        self.center_loc = []

        self.cv_amount = 5.0
        self.ctrl_amount = 5.0
        self.ctrl_type = 2 # Sphere
        self.ctrl_radius = 0.2

        self.attr = {"sys_name": "string", 
                    "sys_side": "string", 
                    "edge_list": "string", 
                    "center_loc": "string", 
                    "cv_amount": "float", 
                    "ctrl_amount": "float", 
                    "ctrl_type": "integer", 
                    "ctrl_radius": "float"}

        if cmds.objExists(self.sys_name + "_BuildPack"): 
            self.buildpack = self.sys_name + "_BuildPack"
            self.load_data()
        else: self.buildpack = createBuildPack(self.attr, self.sys_name)

    def load_data(self):
        buildPack = self.buildpack
        self.sys_name = cmds.getAttr(buildPack + ".sys_name")
        self.sys_side = cmds.getAttr(buildPack + ".sys_side")

        self.sup_edge = cmds.getAttr(buildPack + ".edge_list").split(",")
        self.center_loc = cmds.getAttr(buildPack + ".center_loc")

        self.cv_amount = cmds.getAttr(buildPack + ".cv_amount")
        self.ctrl_amount = cmds.getAttr(buildPack + ".ctrl_amount")
        self.ctrl_type = cmds.getAttr(buildPack + ".ctrl_type") # Sphere
        self.ctrl_radius = cmds.getAttr(buildPack + ".ctrl_radius")

    def run(self):

        build_brow_sys(self.center_loc, self.sys_side, self.sys_name, self.edge_list, 
                    self.cv_amount, self.ctrl_amount, self.ctrl_type, self.ctrl_radius)


"""
orbicular = tp_autoOrbicular()
orbicular.run()
"""

class tp_autoOrbicular():
    def __init__(self):
        self.sys_name = "Orbicular"
        self.sys_side = "L_"

        self.edge_list = ""
        self.center_loc = ""

        self.cv_amount = 10.0
        self.ctrl_amount = 10.0
        self.ctrl_type = 2 # Sphere
        self.ctrl_radius = 0.2

        self.attr = {
            "sys_name": "string", 
            "sys_side": "string", 
            "edge_list": "string", 
            "center_loc": "string", 
            "cv_amount": "float", 
            "ctrl_amount": "float", 
            "ctrl_type": "integer", 
            "ctrl_radius": "float"
            }

        self.attr_relation = {
            "sys_name": self.sys_name, 
            "sys_side": self.sys_side, 
            "edge_list": self.edge_list, 
            "center_loc": self.center_loc, 
            "cv_amount": self.cv_amount, 
            "ctrl_amount": self.ctrl_amount, 
            "ctrl_type": self.ctrl_type, 
            "ctrl_radius": self.ctrl_radius
            }

        if cmds.objExists(self.sys_name + "_BuildPack"): 
            self.buildpack = self.sys_name + "_BuildPack"
            self.load_data()
        else: 
            self.buildpack = createBuildPack(self.attr, self.sys_name)
            for attr in self.attr_relation:
                try: cmds.setAttr("{}.{}".format(self.buildpack, attr), self.attr_relation[attr])
                except: cmds.setAttr("{}.{}".format(self.buildpack, attr), self.attr_relation[attr], type="string")

    def load_data(self):

        buildPack = self.buildpack
        self.sys_name = cmds.getAttr(buildPack + ".sys_name")
        self.sys_side = cmds.getAttr(buildPack + ".sys_side")

        self.edge_list = cmds.getAttr(buildPack + ".edge_list").split(",")
        self.center_loc = cmds.getAttr(buildPack + ".center_loc")

        self.cv_amount = cmds.getAttr(buildPack + ".cv_amount")
        self.ctrl_amount = cmds.getAttr(buildPack + ".ctrl_amount")
        self.ctrl_type = cmds.getAttr(buildPack + ".ctrl_type") # Sphere
        self.ctrl_radius = cmds.getAttr(buildPack + ".ctrl_radius")

    def run(self):

        build_brow_sys(self.center_loc, self.sys_side, self.sys_name, self.edge_list, 
                    self.cv_amount, self.ctrl_amount, self.ctrl_type, self.ctrl_radius, major_ctrl=1)

# EYEBROW BUILD -------------------------------------------------------------------------------------------------------

def build_brow_sys(center_locator, sys_side, sys_name="Eyebrow", edge_list=[], 
                    cv_amount=5.0, ctrl_amount=5.0, ctrl_type=2, ctrl_radius=1, major_ctrl=0):
    
    mirror_sys_side = "R_" if sys_side == "L_" else "L_"

    # Mirror Locator
    loc_position = cmds.xform(center_locator, q=1, t=1)
    mirror_loc = cmds.duplicate(center_locator, n="{}{}".format(mirror_sys_side, center_locator.split("_", 1)[1]))[0]
    try: cmds.parent(mirror_loc, w=1)
    except: pass
    cmds.xform(mirror_loc, t=[loc_position[0]*-1, loc_position[1], loc_position[2]])
    # Mirror edge list
    mirror_edge_list = mirror_edges(edge_list)

    # Build reference side system
    ref_sys = build_brow(center_locator, sys_side, sys_name, edge_list, 
                            cv_amount, ctrl_amount, ctrl_type, ctrl_radius, major_ctrl)
    # Build mirror system
    mirror_sys = build_brow(mirror_loc, mirror_sys_side, sys_name, mirror_edge_list, 
                            cv_amount, ctrl_amount, ctrl_type, ctrl_radius, major_ctrl)

    # ORGANIZING OUTPUT SECTION ===================================
    reference_grp = cmds.group(center_locator, mirror_loc, n="{}_Reference_Grp".format(sys_name))
    main_grp = cmds.group(ref_sys["main_grp"], mirror_sys["main_grp"], reference_grp, n="{}_Grp".format(sys_name))

    return main_grp


def build_brow(center_locator, sys_side, sys_name="Eyebrow", edge_list=[], 
                    cv_amount=5, ctrl_amount=5, ctrl_type=2, ctrl_radius=1, major_ctrl=0):

    # Upper_ Run Stage 1 - Joint System Aim Constrained to Locators on Lid Curve
    sys_data = build_lid_root_sys(sys_side, sys_name , center_locator, edge_list)
    # Upper_ Run Stage 2 - Control system for stage one
    brow_sys = build_lid_ctrl_sys(sys_data["anchor_curve"], cv_amount, ctrl_amount, 
                                ctrl_type, ctrl_radius, sys_side, sys_name)

    # ORGANIZING OUTPUT SECTION ===================================
    # Parent Ctrl Joints Grp to system group
    cmds.parent(brow_sys["joint_grp"], sys_data["sys_grp"])
    # Parent RemoteCtrl Loc group to system group
    cmds.parent(brow_sys["remoteCtrl_grp"], sys_data["sys_grp"])

    # Group sys group and ctrl group
    main_grp = cmds.group(sys_data["sys_grp"], brow_sys["ctrl_grp"], n="{}{}_Grp".format(sys_side, sys_name))
    cmds.setAttr(sys_data["sys_grp"] + ".visibility", 0)

    # Create full sys ctrl
    if major_ctrl:
        major_ctrl_data = cmds.duplicate(brow_sys["driver_crv"], n="{}{}_Major_Ctrl".format(sys_side, sys_name))[0]
        cmds.parent(major_ctrl_data, w=1)
        cmds.xform(major_ctrl_data, cp=1)

        attr = cmds.listAttr(major_ctrl_data)
        for a in attr: 
            try: cmds.setAttr("{}.{}".format(major_ctrl_data, a), lock=0)
            except: pass

        piv_t = cmds.xform(major_ctrl_data, q=1, piv=1, ws=1)

        major_ctrl_grp = cmds.group(empty=1, n=major_ctrl_data + "_Grp")
        cmds.xform(major_ctrl_grp, t=(piv_t[0], piv_t[1], piv_t[2]))
        cmds.parent(major_ctrl_data, major_ctrl_grp)
        cmds.makeIdentity(major_ctrl_data, t=1, r=1, s=1, apply=1)

        cmds.xform(major_ctrl_grp, t=(piv_t[0], piv_t[1], piv_t[2] +1))
        cmds.parent(major_ctrl_grp, brow_sys["ctrl_grp"])

        major_ctrl_cluster = cmds.cluster(sys_data["anchor_curve"], n="{}{}_Major_Ctrl_Cls".format(sys_side, sys_name))
        major_cls_grp = cmds.group(major_ctrl_cluster, n=major_ctrl_cluster[0] + "_Grp")
        cmds.parent(major_cls_grp, sys_data["sys_grp"])

        for attr in ".t,.r,.s".split(','): cmds.connectAttr(major_ctrl_data + attr, major_ctrl_cluster[1] + attr, f=1)

    # Create dict with function output
    sys_data = {
        "main_grp": main_grp, 
        "ctrl_grp": brow_sys["ctrl_grp"], 
        "sys_grp": sys_data["sys_grp"]
        }

    return sys_data
                                

# EYELID BUILD --------------------------------------------------------------------------------------------------------

def build_lid_sys(center_locator, sys_side, sys_name="Eyelid", sup_edge_list=[], 
                    inf_edge_list=[], cv_amount=5, ctrl_amount=5, ctrl_type=2, ctrl_radius=1):

    mirror_sys_side = "R_" if sys_side == "L_" else "L_"
    look_ctrl_offset = 8
    master_ctrl_offset = 14

    # Mirror Locator
    loc_position = cmds.xform(center_locator, q=1, t=1)
    mirror_loc = cmds.duplicate(center_locator, n="{}{}".format(mirror_sys_side, center_locator.split("_", 1)[1]))[0]
    try: cmds.parent(mirror_loc, w=1)
    except: pass
    cmds.xform(mirror_loc, t=[loc_position[0]*-1, loc_position[1], loc_position[2]])

    # BUILD CONTROLS SECTION ==============================================
    # Get center locator position
    loc_position = cmds.xform(center_locator, q=1, t=1)
    # Look controls
    main_look_ctrl = tp_buildCtrl("sphere", "Main_Look", scale=0.5, spaced=1)
    l_look_ctrl = tp_buildCtrl("circle", "L_Look", scale=0.5, spaced=1, normal=(0,0,1))
    cmds.xform(l_look_ctrl[1], t=(loc_position[0], 0, 0))

    r_look_ctrl = tp_buildCtrl("circle", "R_Look", scale=0.5, spaced=1, normal=(0,0,1))
    cmds.xform(r_look_ctrl[1], t=(loc_position[0]*-1, 0, 0))
    
    cmds.parent(l_look_ctrl[1], r_look_ctrl[1], main_look_ctrl[0])
    cmds.xform(main_look_ctrl[1], t=(0, loc_position[1], loc_position[2] + look_ctrl_offset))
    # Bink controls
    main_master_ctrl = tp_buildCtrl("sphere", "Main_Master", scale=0.5, spaced=1)
    l_master_ctrl = tp_buildCtrl("circle", "L_Master", scale=0.5, spaced=1, normal=(0,0,1))
    cmds.xform(l_master_ctrl[1], t=(2, 0, 0))
    
    r_master_ctrl = tp_buildCtrl("circle", "R_Master", scale=0.5, spaced=1, normal=(0,0,1))
    cmds.xform(r_master_ctrl[1], t=(-2, 0, 0))
    
    cmds.parent(l_master_ctrl[1], r_master_ctrl[1], main_master_ctrl[0])
    cmds.xform(main_master_ctrl[1], t=(master_ctrl_offset, loc_position[1], 0))
    eye_ctrl_grp = cmds.group(main_master_ctrl[1], main_look_ctrl[1], n="Eye_Ctrl_Grp")

    # Mirror edge list
    mirror_sup_edge_list = mirror_edges(sup_edge_list)
    mirror_inf_edge_list = mirror_edges(inf_edge_list)

    # Build reference side system
    ref_sys = main_function(center_locator, l_look_ctrl[0], l_master_ctrl[0], sys_side, 
                            sys_name, sup_edge_list, inf_edge_list, 
                            cv_amount, ctrl_amount, ctrl_type=2, ctrl_radius=0.3)
    # Build mirror system
    mirror_sys = main_function(mirror_loc, r_look_ctrl[0], r_master_ctrl[0], mirror_sys_side, 
                                sys_name, mirror_sup_edge_list, mirror_inf_edge_list, 
                                cv_amount, ctrl_amount, ctrl_type=2, ctrl_radius=0.3)

    # Group and hide
    reference_grp = cmds.group(center_locator, mirror_loc, n="{}_Reference_Grp".format(sys_name))
    ctrl_grp = cmds.group(ref_sys["ctrl_grp"], mirror_sys["ctrl_grp"], eye_ctrl_grp, n="{}_Ctrl_Grp".format(sys_name))
    sys_grp = cmds.group(ref_sys["sys_grp"], mirror_sys["sys_grp"], reference_grp, n="{}_Sys_Grp".format(sys_name))
    cmds.setAttr(sys_grp + ".visibility", 0)

    cmds.delete(ref_sys["main_grp"], mirror_sys["main_grp"])

    # Add eye center pivot to reference group
    sys_grp = cmds.group(ctrl_grp, sys_grp, n="{}_Grp".format(sys_name))

    return sys_grp


def main_function(center_locator, look_ctrl, master_ctrl, sys_side,
                  sys_name="Eyelid", sup_edge_list=[], inf_edge_list=[],
                  cv_amount=5, ctrl_amount=5, ctrl_type=2, ctrl_radius=1):

    # BUILD SECTION ==============================================
    # Upper_ Run Stage 1 - Joint System Aim Constrained to Locators on Lid Curve
    sup_01_sys = build_lid_root_sys(sys_side, "Sup_" + sys_name , center_locator, sup_edge_list)
    # Upper_ Run Stage 2 - Control system for stage one
    sup_02_sys = build_lid_ctrl_sys(sup_01_sys["anchor_curve"], cv_amount, ctrl_amount, 
                                ctrl_type, ctrl_radius, sys_side, "Sup_" + sys_name)

    # Bottom_ Run Stage 1
    inf_01_sys = build_lid_root_sys(sys_side, "Inf_" + sys_name, center_locator, inf_edge_list)
    # Bottom_ Run Stage 2
    inf_02_sys = build_lid_ctrl_sys(inf_01_sys["anchor_curve"], cv_amount, ctrl_amount, 
                                ctrl_type, ctrl_radius, sys_side, "Inf_" + sys_name)

    # Run Stage 3
    blink_sys = tp_blink_ctrl_sys(sup_01_sys["anchor_curve"], inf_01_sys["anchor_curve"], sup_02_sys['driver_crv'], 
                                    inf_02_sys['driver_crv'], master_ctrl, look_ctrl, sys_name, sys_side)

    # Create corner controls
    l_corner_ctrl = build_corner(sup_02_sys["ctrl_list"][0], inf_02_sys["ctrl_list"][0], sup_02_sys["remoteCtrl_list"][0], 
                                    inf_02_sys["remoteCtrl_list"][0], name="{}{}_L_Corner".format(sys_side, sys_name))
    r_corner_ctrl = build_corner(sup_02_sys["ctrl_list"][-1], inf_02_sys["ctrl_list"][-1], sup_02_sys["remoteCtrl_list"][-1], 
                                    inf_02_sys["remoteCtrl_list"][-1], name="{}{}_R_Corner".format(sys_side, sys_name))

    corner_remoteCtrl_grp = cmds.group(l_corner_ctrl["corner_remoteCtrl"], r_corner_ctrl["corner_remoteCtrl"], 
                                        n="{}{}_Corner_RemoteCtrl_Loc_Grp".format(sys_side, sys_name))

    # ORGANIZING OUTPUT SECTION ===================================
    # Parent Ctrl Joints Grp to system group
    cmds.parent(sup_02_sys["joint_grp"], sup_01_sys["sys_grp"])
    # Parent RemoteCtrl Loc group to system group
    cmds.parent(sup_02_sys["remoteCtrl_grp"], sup_01_sys["sys_grp"])

    # Parent Ctrl Joints Grp to system group
    cmds.parent(inf_02_sys["joint_grp"], inf_01_sys["sys_grp"])
    # Parent RemoteCtrl Loc group to system group
    cmds.parent(inf_02_sys["remoteCtrl_grp"], inf_01_sys["sys_grp"])

    # Group superior and inferior control groups
    main_ctrl_grp = cmds.group(sup_02_sys["ctrl_grp"], inf_02_sys["ctrl_grp"], l_corner_ctrl["corner_ctrl"][1], 
                                r_corner_ctrl["corner_ctrl"][1], n="{}{}_Ctrl_Grp".format(sys_side, sys_name))
    # Group superior and inferior system groups
    main_sys_grp = cmds.group(sup_01_sys["sys_grp"], inf_01_sys["sys_grp"], blink_sys["blink_crv_grp"], 
                                corner_remoteCtrl_grp, n="{}{}_Sys_Grp".format(sys_side, sys_name))
    # Group sys group and ctrl group
    eyelid_grp = cmds.group(main_sys_grp, main_ctrl_grp, n="{}{}_Grp".format(sys_side, sys_name))
    
    # Create dict with function output
    sys_data = {"main_grp": eyelid_grp, 
                "ctrl_grp": main_ctrl_grp, 
                "sys_grp": main_sys_grp}

    return sys_data

#-----------------------------------------------------------------------------------------------------------------------------# 


# MAIN FUNCTIONS SECTION _________________________________________________________________________________________

def build_lid_root_sys(sys_side, sys_purpose, center_loc, edge_slct):
    # Build Anchor Curve from Slc Edges-> Get Name -> Del History
    cmds.select(edge_slct)
    anchor_curve = cmds.polyToCurve(name=sys_side + sys_purpose + '_Anchor_Crv', form=2, 
                                    degree=1, conformToSmoothMeshPreview=0)[0]
    
    reverse_crv = xDirection_positive(anchor_curve)
    if reverse_crv == False: cmds.reverseCurve(anchor_curve, rpo=1)
    cmds.delete(anchor_curve, ch=1)

    # Convert edges to Verts -> Get vertex
    vtx_query = cmds.polyListComponentConversion(edge_slct, fe=1, tv=1)
    cmds.select(vtx_query, r=1)
    vtx = cmds.ls(sl=1, fl=1)

    # Declare lists
    eyelid_jnt_list = []
    center_jnt_list = []
    aimLoc_list = []
    pointOnCrvInfo_node_list = []

    # Create groups
    jnt_grp = cmds.group(name=sys_side + sys_purpose + '_Jnt_Grp', empty=1)
    loc_grp = cmds.group(name=sys_side + sys_purpose + '_AimLoc_Grp', empty=1)
    sys_grp = cmds.group(name=sys_side + sys_purpose + '_Sys_Grp', empty=1)
    sys_items = [anchor_curve, jnt_grp, loc_grp]

    # CREATE JOINT PAIR - Selected vertex and center
    for i, v in enumerate(vtx) :
        # Create lid joint
        cmds.select(cl=1)
        lid_joint = cmds.joint(name="{}{}_{:02d}_Jnt".format(sys_side, sys_purpose, i+1))
        eyelid_jnt_list.append(lid_joint)
        pos = cmds.xform(v, q=1, ws=1, t=1)
        cmds.xform(lid_joint, ws=1, t=pos)

        # Create and position center joint
        center_position = cmds.xform(center_loc, q=1, ws=1, t=1)
        cmds.select(cl=1)
        center_joint = cmds.joint(name="{}{}_{:02d}_Pivot_Jnt".format(sys_side, sys_purpose, i+1))
        center_jnt_list.append(center_joint)
        cmds.xform(center_joint, ws=1, t=center_position)
        cmds.parent(lid_joint, center_joint)
        # Orient joints
        cmds.joint(center_joint, e=1, oj="xyz", secondaryAxisOrient="yup", ch=1, zso=1)

        # Change joints radius
        cmds.setAttr(center_joint + ".radius", 0.1)
        cmds.setAttr(lid_joint + ".radius", 0.1)
        cmds.parent(center_joint, jnt_grp)

    # CREATE LOCATORS FOR EACH JOINT -> AimConstrain Joints to Locators
    for z, lid_jnt in enumerate(eyelid_jnt_list) :
        # Create locator, append to list
        lidJnt_loc = cmds.spaceLocator(n="{}{}_{:02d}_Aim_Loc".format(sys_side, sys_purpose, z+1))[0]
        aimLoc_list.append(lidJnt_loc)
        # Position locator on lid joint position
        lidJnt_pos = cmds.xform(lid_jnt, q=1, ws=1, t=1)
        cmds.xform(lidJnt_loc, ws=1, t=lidJnt_pos)
        # Reduce locator size
        cmds.setAttr(lidJnt_loc + ".localScaleX", 0.2)
        cmds.setAttr(lidJnt_loc + ".localScaleY", 0.2)
        cmds.setAttr(lidJnt_loc + ".localScaleZ", 0.2)
        # Aim constraint center joint to lid locator
        lidJnt_prnt = cmds.listRelatives(lid_jnt, p=1)[0]
        cmds.aimConstraint(lidJnt_loc, lidJnt_prnt, mo=1, weight=1, aimVector=(1,0,0), 
                            upVector=(0,1,0), worldUpType="object", worldUpObject=center_loc)
        # Parent to joint gorup
        cmds.parent(lidJnt_loc, loc_grp)

    # ATTACH LOCATORS TO CURVE - On CV location
    for loc in aimLoc_list :
        # Get locator position and parameter U on anchor curve
        loc_pos = cmds.xform(loc, q=1, ws=1, t=1)
        loc_u = getUParam(loc_pos, anchor_curve)
        # Create Point on Curve Info node
        pciNode_name = loc.replace("_loc", "_pci")
        pciNode = cmds.createNode("pointOnCurveInfo", n=pciNode_name)
        pointOnCrvInfo_node_list.append(pciNode)
        # Make connections between anchor curve and locator
        cmds.connectAttr(anchor_curve + ".worldSpace", pciNode + ".inputCurve")
        cmds.setAttr(pciNode + ".parameter", loc_u)
        cmds.connectAttr(pciNode + ".position" , loc + ".t")

    cmds.parent(sys_items, sys_grp)

    sys_data = {
        "anchor_curve": anchor_curve, 
        "center_joint_list": center_jnt_list, 
        "eyelid_jnt_list": eyelid_jnt_list, 
        "joint_group": jnt_grp, 
        "aim_loc_list": aimLoc_list, 
        "aim_loc_group": loc_grp, 
        "pointOnCrvInfo_node_list": pointOnCrvInfo_node_list, 
        "sys_grp": sys_grp
        }

    return sys_data


def build_lid_ctrl_sys(anchor_curve, cv_amount, ctrl_amount, ctrl_type, ctrl_radius, sys_side, sys_name):

    sys_data = {'anchor_crv':anchor_curve, 'driver_crv':''}
    crv_step = 100 / (ctrl_amount-1) / 100
    crv_inverse = 0

    # Declaring lists for objects
    jnt_list = []; ctrl_list = []; remoteCtrl_list = []

    # Creating groups
    jnt_grp = cmds.group(name=sys_side + sys_name + '_Ctrl_Jnt_Grp', empty=1)
    ctrl_grp = cmds.group(name=sys_side + sys_name + '_Ctrl_Grp', empty=1)
    remoteCtrl_grp = cmds.group(name=sys_side + sys_name + '_RemoteCtrl_Loc_Grp', empty=1)

    # Duplicate and rebuild curve to become system drives
    driver_crv = cmds.duplicate(anchor_curve, name= sys_side + sys_name + '_Driver_Crv')[0]
    cmds.rebuildCurve(driver_crv, rpo=1, rt=0, end=1, kr=0, 
                        kcp=0, kep=1, kt=1, s=cv_amount, d=1, tol=0.01)
    cmds.rebuildCurve(driver_crv, rpo=1, rt=0, end=1, kr=0, 
                        kcp=1, kep=1, kt=1, s=4, d=3, tol=0.01)
    # cmds.delete(driver_crv, ch=1)
    
    driver_wire_node = cmds.wire(anchor_curve, w=driver_crv, gw= False, en= 1.000000, ce= 0.000000, li= 0.000000)

    for i in range(int(ctrl_amount)):
        parameter = crv_step * i
        position = getPointOnCurve(anchor_curve, parameter, crv_inverse)

        # Create control joint for CV position
        step_jnt = cmds.joint(name="{}{}_{:02d}_Driver_Jnt".format(sys_side, sys_name, i+1), rad= 0.3)

        # Create remote control, reduce localScale and group it
        remoteCtrl_loc = cmds.spaceLocator(name="{}{}_{:02d}_RemoteCtrl_Loc".format(sys_side, sys_name, i+1))[0]
        for dimension in ["X","Y","Z"]: cmds.setAttr("{}.localScale{}".format(remoteCtrl_loc, dimension), ctrl_radius)
        remoteCtrl_loc_grp = cmds.group(remoteCtrl_loc, n=remoteCtrl_loc + "_Grp")

        # Check control type and create controls
        if ctrl_type == 1:
            ctrl_data = tp_buildCtrl(ctrl_type="circle", name="{}{}_{:02d}".format(sys_side, sys_name, i+1), scale=ctrl_radius, spaced=1, normal=(0,0,1))
        elif ctrl_type == 2:
            ctrl_data = tp_buildCtrl(ctrl_type="sphere", name="{}{}_{:02d}".format(sys_side, sys_name, i+1), scale=ctrl_radius, spaced=1)
        else:
            ctrl_data = tp_buildCtrl(ctrl_type="circle", name="{}{}_{:02d}".format(sys_side, sys_name, i+1), scale=ctrl_radius, spaced=1, normal=(0,0,1))
            blnd_ctrl_data = tp_buildCtrl(ctrl_type="sphere", name="{}{}_{:02d}_{}".format(sys_side, sys_name, i, "Blnd"), scale=ctrl_radius, spaced=1)
            cmds.parent(ctrl_data[1], blnd_ctrl_data[0])

        # Position joint, control and remoteCtrl on CV position
        cmds.xform(ctrl_data[1], ws=1, t=position[0], ro=(0,position[1][1],0))
        cmds.xform(step_jnt, ws=1, t=position[0], ro=(0,position[1][1],0))
        cmds.xform(remoteCtrl_loc_grp, ws=1, t=position[0], ro=(0,position[1][1],0))
        # Parente remote control to joint
        cmds.parentConstraint(remoteCtrl_loc, step_jnt, mo=1)

        # Connect control to remote control
        # Add mirror control option
        cmds.connectAttr(ctrl_data[0] + '.translate', remoteCtrl_loc + '.translate')
        cmds.connectAttr(ctrl_data[0] + '.rotate', remoteCtrl_loc + '.rotate')
        cmds.connectAttr(ctrl_data[0] + '.scale', remoteCtrl_loc + '.scale')
        
        # Parent created objects to groups
        cmds.parent(step_jnt, jnt_grp)
        cmds.parent(ctrl_data[1], ctrl_grp)
        cmds.parent(remoteCtrl_loc_grp, remoteCtrl_grp)
        
        # Append objects to lists
        jnt_list.append(step_jnt)
        ctrl_list.append(ctrl_data[0])
        remoteCtrl_list.append(remoteCtrl_loc)

    cmds.skinCluster(jnt_list, driver_crv)

    # Group curves and parent to sys group
    sys_grp = cmds.listRelatives(anchor_curve, p=1)[0]
    crv_grp = cmds.group(anchor_curve, driver_crv, driver_crv + "BaseWire", n="{}{}_Crv_Grp".format(sys_side, sys_name))

    sys_data.update({
        "ctrl_list": ctrl_list, 
        "ctrl_grp": ctrl_grp, 
        "joint_list": jnt_list, 
        "joint_grp": jnt_grp, 
        "remoteCtrl_list": remoteCtrl_list, 
        "remoteCtrl_grp": remoteCtrl_grp, 
        "driver_crv": driver_crv, 
        "driver_baseWire": driver_crv + "BaseWire", 
        "wire_node": driver_wire_node
        })
    
    return sys_data


def tp_blink_ctrl_sys(sup_a_crv, inf_a_crv, sup_d_crv, inf_d_crv, mst_ctrl, look_ctrl, sys_name="", sys_side=""):
    # Pre-stabilished variables
    sup_maxRange = 2.2
    inf_maxRange = 2.2
    ctrls_sensitivity = 0.250

    # Create blink curve
    blink_targ = cmds.duplicate(sup_d_crv, n="{}{}_BlinkTarget_Crv".format(sys_side, sys_name))[0]
    # Duplicate static sup and inf driver curves for blink target to blend with no ctrls effect
    sup_blinkTarget_crv = cmds.duplicate(sup_d_crv, n=sup_d_crv.replace("Driver", "BlinkTarget_Blend"))[0]
    inf_blinkTarget_crv = cmds.duplicate(inf_d_crv, n=inf_d_crv.replace("Driver", "BlinkTarget_Blend"))[0]
    blink_bShape = cmds.blendShape(sup_blinkTarget_crv, inf_blinkTarget_crv, blink_targ, 
                                    n="{}{}_BlinkLevel_bShape".format(sys_side, sys_name))[0]

    # Create, configure and connect setRange nodes
    bt_full_setRng = cmds.shadingNode('setRange', n=blink_targ + '_full_setRange', asUtility=1)
    bt_supInv_setRng = cmds.shadingNode('setRange', n=blink_targ + '_supInv_setRange', asUtility=1)

    cmds.setAttr(bt_full_setRng + '.oldMinY', -1)
    cmds.setAttr(bt_full_setRng + '.oldMaxY', 1)
    cmds.setAttr(bt_full_setRng + '.minY', 1)
    cmds.setAttr(bt_supInv_setRng + '.oldMaxY', 1)
    cmds.setAttr(bt_supInv_setRng + '.minY', 1)

    cmds.connectAttr(mst_ctrl + '.translateY', bt_full_setRng + '.value.valueY', f=1)
    cmds.connectAttr(bt_full_setRng + '.outValue.outValueY', blink_bShape + '.' + inf_blinkTarget_crv, f=1)
    cmds.connectAttr(bt_full_setRng + '.outValue.outValueY', bt_supInv_setRng + '.value.valueY', f=1)
    cmds.connectAttr(bt_supInv_setRng + '.outValue.outValueY', blink_bShape + '.' + sup_blinkTarget_crv, f=1)

    # Create blink target sup, inf, wired curves
    sup_a_targ = cmds.duplicate(sup_a_crv, n=sup_a_crv.replace("Anchor", "BlinkTarget"))
    inf_a_targ = cmds.duplicate(inf_a_crv, n=inf_a_crv.replace("Anchor", "BlinkTarget"))

    cmds.setAttr(mst_ctrl + '.translateY', 1)
    sup_blinkT_wire = cmds.wire(sup_a_targ, w=blink_targ, gw= False, en= 1.000000, ce= 0.000000, li= 0.000000, 
                                n="{}{}_Sup_BlinkTarget_Wire".format(sys_side, sys_name))[0]
    cmds.setAttr(sup_blinkT_wire + '.scale[0]', 0)
    sup_blinkTarg_baseWire = cmds.rename(blink_targ + "BaseWire", blink_targ.replace("BlinkTarget", "Sup_BlinkTarget") + "BaseWire")

    cmds.setAttr(mst_ctrl + '.translateY', -1)
    inf_blinkT_wire = cmds.wire(inf_a_targ, w= blink_targ, gw= False, en= 1.000000, ce= 0.000000, li= 0.000000,
                                n="{}{}_Sup_BlinkTarget_Wire".format(sys_side, sys_name))[0]
    cmds.setAttr(mst_ctrl + '.translateY', 0)
    cmds.setAttr(inf_blinkT_wire + '.scale[0]', 0)
    inf_blinkTarg_baseWire = cmds.rename(blink_targ + "BaseWire", blink_targ.replace("BlinkTarget", "Inf_BlinkTarget") + "BaseWire")

    # Create Eyelid Curve blendShape to curve wired on blink target curve
    bShape_sup = cmds.blendShape(sup_a_targ, sup_a_crv, n="{}{}_Sup_LidBlink_bSahpe".format(sys_side, sys_name))[0]
    bShape_inf = cmds.blendShape(inf_a_targ, inf_a_crv, n="{}{}_Inf_LidBlink_bSahpe".format(sys_side, sys_name))[0]
    
    # Get wire deformer node
    sup_wire = cmds.listHistory(sup_a_crv, pdo=1, il=1)[1]
    inf_wire = cmds.listHistory(inf_a_crv, pdo=1, il=1)[1]

    # Reorder deformers
    cmds.reorderDeformers(sup_wire, bShape_sup, sup_a_crv)
    cmds.reorderDeformers(inf_wire, bShape_inf, inf_a_crv)
    cmds.select(cl=1)
    
    # Create output attribute on Master control - Connect system - Ads blenshape and reorder
    '''
    Pending
    - Create user input variable for Maximum Control Range (fixed in 2.2 at the moment)
    ---- Consider separate renges for master control and look control
    - Control Max Range and Sensitivity through channel box
    '''
    # Superior control setup
    cmds.addAttr(mst_ctrl, ln= 'sup_output', at='double', min= -2, max= 2, dv= 0)
    cmds.setAttr(mst_ctrl + '.sup_output', e=1, keyable=True)

    sup_look_inverse = cmds.shadingNode('multiplyDivide', n=look_ctrl + '_sup_inverse_mpDivider', asUtility=1)
    cmds.setAttr(sup_look_inverse + '.input2X', -1)

    sup_look_gearDown = cmds.shadingNode('multiplyDivide', n=look_ctrl + '_sup_gearDown_mpDivide', asUtility=1)
    cmds.setAttr(sup_look_gearDown + '.input2X', ctrls_sensitivity)
    
    cmds.connectAttr(look_ctrl + '.translateY', sup_look_inverse + '.input1X')
    cmds.connectAttr(sup_look_inverse + '.outputX', sup_look_gearDown + '.input1X')
    tp_doubleInputCtrl(mst_ctrl, sup_look_gearDown, mst_ctrl, sup_maxRange, '.translateX', '.outputX', '.sup_output')

    # Inferior control setup
    cmds.addAttr(mst_ctrl, ln= 'inf_output', at='double', min= -2, max= 2, dv= 0)
    cmds.setAttr(mst_ctrl + '.inf_output', e=1, keyable=True)
    
    inf_look_gearDown = cmds.shadingNode('multiplyDivide', n=look_ctrl + 'inf_gearDown_mpDivide', asUtility=1)
    cmds.setAttr(inf_look_gearDown + '.input2X', ctrls_sensitivity)

    cmds.connectAttr(look_ctrl + '.translateY', inf_look_gearDown + '.input1X')
    tp_doubleInputCtrl(mst_ctrl, inf_look_gearDown, mst_ctrl, inf_maxRange, '.translateX', '.outputX', '.inf_output')
    
    # Add range adjustment
    sup_adjust_setRng = cmds.shadingNode('setRange', n=blink_targ + '_sup_adjust_setRange', asUtility=1)
    
    cmds.setAttr(sup_adjust_setRng + '.minX', -0.5)
    cmds.setAttr(sup_adjust_setRng + '.maxX', 1)
    cmds.setAttr(sup_adjust_setRng + '.oldMinX', (sup_maxRange * -1)/2)
    cmds.setAttr(sup_adjust_setRng + '.oldMaxX', sup_maxRange)

    inf_adjust_setRng = cmds.duplicate(sup_adjust_setRng, n=blink_targ + '_inf_adjust_setRange')[0]

    cmds.connectAttr(mst_ctrl + '.sup_output', sup_adjust_setRng + '.value.valueX')
    cmds.connectAttr(mst_ctrl + '.inf_output', inf_adjust_setRng + '.value.valueX')
    cmds.connectAttr(sup_adjust_setRng + '.outValueX', bShape_sup + '.' + sup_a_targ[0])
    cmds.connectAttr(inf_adjust_setRng + '.outValueX', bShape_inf + '.' + inf_a_targ[0])

    # List created nodes to return
    wire_list = [sup_blinkT_wire, inf_blinkT_wire]
    blendShape_list = [blink_bShape, bShape_sup, bShape_inf]
    curve_list = [blink_targ, sup_blinkTarget_crv, sup_blinkTarg_baseWire, 
                    inf_blinkTarget_crv, inf_blinkTarg_baseWire, sup_a_targ[0], inf_a_targ[0]]

    blink_crv_grp = cmds.group(curve_list, n="{}{}_Blink_Crv_Grp".format(sys_side, sys_name))

    shadingNode_list = [bt_full_setRng, bt_supInv_setRng, sup_look_inverse, 
                        sup_look_gearDown, inf_look_gearDown, sup_adjust_setRng, inf_adjust_setRng]

    sys_data = {
        "blink_targ_crv": blink_targ, 
        "sup_blinkTarget_crv": sup_blinkTarget_crv, 
        "inf_blinkTarget_crv": inf_blinkTarget_crv, 
        "blink_bSahpe_node": blink_bShape, 
        "blink_crv_grp": blink_crv_grp, 
        "shadingNode_list": shadingNode_list, 
        "curve_list": curve_list, 
        "wire_list": wire_list, 
        "blendShape_list": blendShape_list
        }

    return sys_data


def build_corner(sup_ctrl, inf_ctrl, sup_remoteCtrl, inf_remoteCtrl, name):
    # Get controls and remoteCtrls parent groups
    sup_ctrl_grp = cmds.listRelatives(sup_ctrl, p=1)[0]
    inf_ctrl_grp = cmds.listRelatives(inf_ctrl, p=1)[0]
    sup_remoteCtrl_grp = cmds.listRelatives(sup_remoteCtrl, p=1)[0]
    inf_remoteCtrl_grp = cmds.listRelatives(inf_remoteCtrl, p=1)[0]

    # Get superior ctrl translate
    sup_position = cmds.xform(sup_ctrl, q=1, t=1, ws=1)
    sup_rotation = cmds.xform(sup_ctrl, q=1, ro=1, ws=1)
    
    # Get superior ctrl rotation
    inf_position = cmds.xform(inf_ctrl, q=1, t=1, ws=1)
    inf_rotation = cmds.xform(inf_ctrl, q=1, ro=1, ws=1)
    
    # Find mid point between both controls
    avg_position = [(posA + posB)/2 for posA, posB in zip(sup_position, inf_position)]
    avg_rotation = [(roA + roB)/2 for roA, roB in zip(sup_rotation, inf_rotation)]
    
    # Create corner control and postion acording to calculated position
    corner_ctrl = tp_buildCtrl(ctrl_type="sphere", name=name + "_Corner", scale=0.3, spaced=1)
    cmds.xform(corner_ctrl[1], t=avg_position, ro=avg_rotation)
    cmds.parent(sup_ctrl_grp, inf_ctrl_grp, corner_ctrl[0])
    
    # Create remoteCtrl Locator and position
    corner_remoteCtrl_loc = cmds.spaceLocator(n="{}_RemoteCtrl_Loc".format(name))[0]
    corner_remoteCtrl_grp = cmds.group(n=corner_remoteCtrl_loc + "_Grp")
    cmds.xform(corner_remoteCtrl_grp, t=avg_position, ro=avg_rotation)
    cmds.parent(sup_remoteCtrl_grp, inf_remoteCtrl_grp, corner_remoteCtrl_loc)
    
    # Connect Corner control and remote control Locator
    for attr in ".t,.rotate,.s".split(','): cmds.connectAttr(corner_ctrl[0] + attr, corner_remoteCtrl_loc + attr, f=1)
    # Reduce locator scale
    for dimension in ["X","Y","Z"]: cmds.setAttr("{}.localScale{}".format(corner_remoteCtrl_loc, dimension), 0.4)
    # Turn Sup and Inf controls visibility off
    cmds.setAttr(sup_ctrl_grp + ".visibility", 0)
    cmds.setAttr(inf_ctrl_grp + ".visibility", 0)

    sys_data = {
        "corner_ctrl": corner_ctrl, 
        "corner_remoteCtrl": corner_remoteCtrl_grp
        }

    return sys_data


# CONTROL FUNCTION SECTION _________________________________________________________________________________________

def tp_doubleInputCtrl(ctrl1_out, ctrl2_out, ctrl3_in, max_range=1, ctrl1_out_attr=".translateX", 
                        ctrl2_out_attr=".translateX", ctrl3_in_attr=".translateX"):
    '''
    How it works
    - The system uses a variable initial range where the total range is the sum of the to controllers max.
    - With a setRange, we cap the sum of the controls to start showing only after total_range/2 - therefore 1 -> 2, 
        instead of 0 -> 2
    - This value is then sumed into total_range/2, and pulged into oldMax
    - This causes the initial range to increase when the sum of both controls is higher then total_range/2, 
        yet the new renge is always 0 to 1
    '''
    total_range = max_range * 2

    sum_total = cmds.shadingNode('plusMinusAverage', asUtility=1, n="{}_sumTotal_plusMA".format(ctrl1_out))
    sum_oldMax = cmds.shadingNode('plusMinusAverage', asUtility=1, n="{}_oldMax_plusMA".format(ctrl1_out))

    sRange_clamp = cmds.shadingNode('setRange', asUtility=1, n="{}_clamp_setRange".format(ctrl1_out))
    sRange_result = cmds.shadingNode('setRange', asUtility=1, n="{}_result_setRange".format(ctrl1_out))

    cmds.connectAttr(ctrl1_out + ctrl1_out_attr, sum_total + '.input1D[0]')
    cmds.connectAttr(ctrl2_out + ctrl2_out_attr, sum_total + '.input1D[1]')
    cmds.connectAttr(sum_total + '.output1D', sRange_clamp + '.valueX')

    cmds.setAttr(sRange_clamp + '.maxX', max_range)
    cmds.setAttr(sRange_clamp + '.oldMinX', max_range)
    cmds.setAttr(sRange_clamp + '.oldMaxX', total_range)

    cmds.connectAttr(sRange_clamp + '.outValueX', sum_oldMax + '.input2D[1].input2Dx')
    cmds.setAttr(sum_oldMax + '.input2D[0].input2Dx', max_range)

    cmds.connectAttr(sum_total + '.output1D', sRange_result + '.valueX')
    cmds.connectAttr(sum_oldMax + '.output2Dx', sRange_result + '.oldMaxX')
    cmds.setAttr(sRange_result + '.minX', (max_range * -1)/2 )
    cmds.setAttr(sRange_result + '.maxX', max_range)
    cmds.setAttr(sRange_result + '.oldMinX', (max_range * -1)/2 )

    cmds.connectAttr(sRange_result + '.outValueX', ctrl3_in + ctrl3_in_attr)


def tpSphere_Ctrl(name='tpSphere', radius= 1):
    shapes = []
    circles = []

    for i in range(4):
        deg = 45 * i
        circle = cmds.circle(name= name + str(i+1), r= radius, ch=0)[0]
        cmds.xform(circle, ro= (0, deg, 0))
        cmds.makeIdentity(circle, apply=1, t=1, r=1, s=1, n=0, pn=1)

        shape = cmds.listRelatives(circle, shapes=True)[0]
        shapes.append(shape)
        circles.append(circle)

    ctrl = cmds.circle(name= name, r= radius, nr= (0, 1, 0), ch=0)
    
    cmds.parent(shapes, ctrl, s=1, r=1)
    cmds.delete(circles)
    cmds.select(ctrl)
    
    return ctrl[0]


def tp_buildCtrl(ctrl_type="circle", name="", sufix="_Ctrl", scale=1, spaced=1, offset=0, normal=(1,0,0)):
    """ctrl_type - Cube, Sphere, Circle (add - square, pointer, arrow, spherev2) """
    pack = []

    if ctrl_type == "cube":
        cube_coord = [
            (-1.0, 1.0, 1.0), (-1.0, 1.0, -1.0), (1.0, 1.0, -1.0), 
            (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, -1.0, 1.0), 
            (1.0, -1.0, 1.0), (1.0, -1.0, -1.0), (-1.0, -1.0, -1.0), 
            (-1.0, -1.0, 1.0), (-1.0, -1.0, -1.0), (-1.0, 1.0, -1.0), 
            (1.0, 1.0, -1.0), (1.0, -1.0, -1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0)
            ]
            
        c1 = cmds.curve(n=name + sufix, p=cube_coord, k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], d=1)
		
        cmds.setAttr(c1 + ".scale.scaleX", scale)
        cmds.setAttr(c1 + ".scale.scaleY", scale)
        cmds.setAttr(c1 + ".scale.scaleZ", scale)
        cmds.makeIdentity(c1, apply=True, t=1, r=1, s=1, n=0)
        pack.append(c1)

    elif ctrl_type == "sphere":
        c1 = cmds.circle(n=name + sufix, nr=(1, 0, 0), r=scale, ch=0)[0]
        c2 = cmds.circle(nr=(0, 1, 0), r=scale, ch=0)[0]
        c3 = cmds.circle(nr=(0, 0, 1), r=scale, ch=0)[0]

        cmds.parent(cmds.listRelatives(c2, s=True), cmds.listRelatives(c3, s=True), c1, r=True, s=True)
        cmds.delete(c2, c3)
        pack.append(c1)

    else:
        c1 = cmds.circle(n=name + sufix, nr=normal, r=scale, ch=0)[0]
        pack.append(c1)

    shapes = cmds.listRelatives(c1, f=True, s=True)
    for y, shape in enumerate(shapes):
        cmds.rename(shape, "{}Shape{:02d}".format(c1, y+1))    

    if spaced == 1:
        ctrl_grp = cmds.group(c1, n=name + sufix + "_Grp")
        pack.append(ctrl_grp)
        
    if offset == 1:
		# Creates offset group for static control
        offset_grp = cmds.group(c1, n=name + sufix + "_Offset_Grp")
        mpDivide_node = cmds.shadingNode('multiplyDivide', au=1)
        
        cmds.connectAttr(c1 + '.translate', mpDivide_node + '.input1')
        cmds.connectAttr(mpDivide_node + '.output', offset_grp + '.translate')
        cmds.setAttr(mpDivide_node + '.input2X', -1)
        cmds.setAttr(mpDivide_node + '.input2Y', -1)
        cmds.setAttr(mpDivide_node + '.input2Z', -1)
        pack.append(offset_grp)

	# pack = [ctrl, ctrl_grp, offset_ctrl_grp]
    return pack


# UTILITY FUNCTION SECTION _________________________________________________________________________________________

# Not in use
def mirror_vertex_selection(vert_list, mesh):
    """ Mirror selection translation values and feeds to getClosest function"""
    vert_list = cmds.filterExpand(vert_list, sm=31)
    mirror_vert_list = []

    for vert in vert_list:
        vertPos = cmds.xform(vert, q=1, t=1)
        mirror_pos = [(vertPos[0] * -1), vertPos[1], vertPos[2]]
        mirror_vert_list.append(getClosestVertex_v2(mesh, mirror_pos))
    
    # cmds.select(mirror_vert_list, r=1)

    return mirror_vert_list

# Not in use


def getClosestVertex_v2(mayaMesh, pos=[0,0,0]):
    """ Returns the closest vertex given a mesh and a position [x,y,z] in world space.
        Uses om2.MfnMesh.getClosestPoint() returned face ID and iterates through face's vertices."""

    # Using MVector type to represent position
    mVector = om2.MVector(pos) 
    selectionList = om2.MSelectionList()
    selectionList.add(mayaMesh)
    dPath = selectionList.get_dag_path(0)
    mMesh = om2.MFnMesh(dPath)
    # Getting closest face ID
    face_ID = mMesh.getClosestPoint(om2.MPoint(mVector), space=om2.MSpace.kWorld)[1]
    # Face's vertices list
    vert_list = cmds.ls(cmds.polyListComponentConversion('{}.f[{}]'.format(mayaMesh, face_ID), ff=True, tv=True), flatten=True)
    
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


def mirror_edges(edge_list):
    vert_list = cmds.filterExpand(cmds.polyListComponentConversion(edge_list, fe=1, tv=1), sm=31)
    mirror_vert_list = mirrorSelection(vert_list)
    cmds.select(mirror_vert_list, r=1)
    mel.eval('PolySelectConvert 20')
    mirror_edge_list = cmds.ls(sl=1)
    cmds.select(cl=1)

    return mirror_edge_list


def xDirection_positive(curve):
    """ True if curve X direction is positive, 
        False if curve X direction is negative """
    
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


def getUParam(position=[], crv=None):
    """
    Get ParameterU based on position on curve
    Function will break the undo stack - Further improvement necessary
    Function using Maya API 1.0
    """

    point = om.MPoint(position[0], position[1], position[2])
    curve_fn = om.MFnNurbsCurve(get_dag_path(crv))
    param_util = om.MScriptUtil()
    param_ptr = param_util.asDoublePtr()
    is_on_curve = curve_fn.isPointOnCurve(point)
    
    if is_on_curve:
        curve_fn.getParamAtPoint(point, param_ptr, 0.001, om.MSpace.kObject)
    else:
        point = curve_fn.closestPoint(point, param_ptr, 0.001, om.MSpace.kObject)
        curve_fn.getParamAtPoint(point, param_ptr, 0.001, om.MSpace.kObject)
    
    param = param_util.getDouble(param_ptr)

    return param


def get_dag_path(object_name):
    selection_list = om.MSelectionList()
    selection_list.add(object_name)
    oNode = om.MDagPath()
    selection_list.getDagPath(0, oNode)

    return oNode


def getPointOnCurve(crv, parameter, inverse = 0):
    """
    Gets position and rotation of point on curve using motion path
    """

    poc_loc = cmds.spaceLocator(name= 'Poc_Temp_Loc')
    mPath_Crv = cmds.duplicate(crv, name= 'mPath_Temp_Crv')[0]
    # cmds.delete(mPath_Crv, ch=1)
    
    mPath = cmds.pathAnimation(poc_loc, mPath_Crv, n= 'mPath_Temp', fractionMode=1, 
                                followAxis= 'x', upAxis= 'y', worldUpType= "vector", 
                                inverseUp= inverse, inverseFront= inverse)
    cmds.disconnectAttr(mPath + '_uValue.output', mPath + '.uValue')
    cmds.setAttr(mPath + '.uValue', parameter)

    tr = cmds.xform(poc_loc, q=1, t=1)
    rt = cmds.xform(poc_loc, q=1, ro=1)

    point = []
    point.append(tr)
    point.append(rt)
    
    cmds.delete(mPath + '_uValue', mPath, poc_loc, mPath_Crv)
    
    # point = [[t.x, t.y, t.z], [r.x, r.y, r.z]]
    return point


def createBuildPack(attr_dict, name):
    container = cmds.container(type="dagContainer", ind=("history", "channels"), 
                                includeHierarchyBelow=1, includeTransform=1, n=name + "_BuildPack")

    options_dict = {
        "float": "cmds.addAttr('{}', ln='{}', at='double', dv=0)".format(container, "--REPLACE--"), 
        "integer": "cmds.addAttr('{}', ln='{}', at='long', dv=0)".format(container, "--REPLACE--"), 
        "boolean": "cmds.addAttr('{}', ln='{}', at='bool')".format(container, "--REPLACE--"), 
        "string": "cmds.addAttr('{}', ln='{}', dt='string')".format(container, "--REPLACE--"), 
        "enum": "cmds.addAttr('{}', ln='{}', at='enum', en='{}')".format(container, "--REPLACE--", "--ENUM--")
        }

    for attr in attr_dict:
        exec(options_dict[attr_dict[attr]].replace("--REPLACE--", attr))

    return container


def load_attr(build_pack, attr):
    data = ",".join(cmds.ls(sl=1))
    cmds.setAttr(build_pack + attr, data, type="string")


def setCtrlColor(ctrl, color=(1,1,1)):
    """ Set control color function"""

    rgb = ("R","G","B")
    cmds.setAttr(ctrl + ".overrideEnabled", 1)
    cmds.setAttr(ctrl + ".overrideRGBColors", 1)
    
    for channel, color in zip(rgb, color):
        cmds.setAttr("{}.overrideColor{}".format(ctrl, channel), color)