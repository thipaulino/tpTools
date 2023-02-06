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

"""
MOD List
    - Kill rotation on bind joints
    - Invert controls on the rigth side **
    - Hide system groups
    - Add top/bottom ctrls to single main ctrl group
    - Remove parenting from corner controls
    - Level controls Y to single value
    - Change controls color based on X? position
    - Create jaw rig

    LIPS SLIDE
    - Create control for sliding **

    SURFACE CTRL
    - Create control **
    - Build system on surface duplicate
    - Add surface to system group

    LIPS ROLL/ PUCKER
    - Develop strcucture
    - Add controls
    - Script system 

    CHEEKS PUFF
    CHEEKS VOLUME
    
    NOSE

    ZIPPER LIPS
    NECK
    EARS

    - Add square for build scale control
    - Lock and hide unused attributes
    - Add lips sliding
    - Add rig to surface for back and forth sliding

    DONE ------
    - Position top and bottom controls away from the lips # DONE
    - Apply corner script #DONE
    - Ctrl joints are directly parented to controls #DONE
        - Create remote control locs and connect controls to them
        - So that we can move controls freely
    - Organize all created nodes #DONE
    - Parent superior and inferior mouth corner controls #DONE
    - Adjust joint and locators size #DONE
"""

from __future__ import division
import maya.OpenMaya as om
import maya.cmds as cmds

import tpUtils as tpu
import tpRig.tpControl.tpControl as tpCtrl
import tpRig.tpRigUtils as tpUtils

import ast

"""
mouth = mouth_system()
mouth.name = "Mouth"
mouth.surface = cmds.ls(sl=1)[0]
mouth.sup_edge_list = cmds.ls(sl=1)
mouth.inf_edge_list = cmds.ls(sl=1)
mouth.settings_ctrl_template = cmds.ls(sl=1)
mouth.mouth_slide_ctrl_template = cmds.ls(sl=1)
mouth.store_data()
mouth.build()
mouth.delete()
"""


"""
Development list for Moonshine project

    ISSUES
        - control "Mouth_Sup_Lip_01_ctrl" not connected - running free
        - corner control left - oriented to world, instead of face normal
        - all joints must be parented to joint hierarchy
        
    REQUIREMENTS FOR DEMO
        - Mouth system with controls
    
    SYSTEM FUNCTIONALITY
        - Eyebrows
        - Mouth slide
        - Cheek Puff
        - Nose 
            - flair
            - Raise
            
    ACTION LIST - FOCUS ON MINIMUM VIABLE PRODUCT
        - neck - platisma
        - lip roll sys
    
        - DONE - cheek puff - eyebrow joints - change joint direction - X must point to main movement
        - DONE - under chin - sub maxilar
        - DONE - ears
        - DONE - hide all end joint controls
        
        - mouth slide system
            - fix right corner control joint that is not binded to curve
                - possible solution - first selected edge seems to be changing directions
                - rebuild the system based on a cleaner edge selection
            - add slide control - cluster on low res curves 
            - slide surface control - add control to move entire surface
            - * switch control creation to control class in order to change shapes and save reliably
            - store control objects to change later
            - joint similar elements for each system - ie. ctrl groups -
            - add tags to system elements as attributes  
                    
        - muscle controls - add null group on top to control via attribute
            - must be added probably to output joint, not remote
        - control attribute - create control attribute for all drivable muscles        
        - change control shapes
        - add nose flare
        
        - create setting control
            - add control visibility attributes
            - add face controls attribute
         
            

"""


class mouth_system():

    def __init__(self):
        self.sys_data = {}

        self.name = 'Mouth'
        self.surface = ''
        self.sup_edge_list = []
        self.inf_edge_list = []
        self.executed = False

        self.setting_ctrl_template = None
        self.mouth_slide_ctrl_template = None
        self.head_ctrl_template = None

        self.attr = {"sys_name": "string",
                     "sys_surface": "string",
                     "sup_edge": "string",
                     "inf_edge": "string",
                     "settings_template": "string",
                     "mouth_slide_template": "string",
                     "head_ctrl_template": "string"}

        if cmds.objExists(self.name + "_BuildPack"):
            self.build_pack = self.name + "_BuildPack"
            self.load_data()
        else:
            self.build_pack = createBuildPack(self.attr, self.name)

        # system controls ----
        self.control_object_dict = {}
        self.main_face_control = None
        self.settings_control = None
        self.mouth_slide_control = None
        self.surface_control = None

        # system elements ----
        self.sup_edge_curve = None
        self.sup_low_res_edge_curve = None
        self.inf_edge_curve = None
        self.inf_low_res_edge_curve = None

        self.follicle_list = None
        self.sup_bind_joint_list = None
        self.inf_bind_joint_list = None
        self.sup_control_joint_list = None
        self.inf_control_joint_list = None
        self.sup_aim_loc_list = None
        self.inf_aim_loc_list = None

        self.sys_build_list = [
            self.create_main_face_control,
            self.build_stage,
            self.create_mouth_slide_surface_control,
            self.build_mouth_slide_control,
        ]

    def build_face_template(self):
        pass

    def build(self):
        # self.sys_data = build_mouth_sys(self.sup_edge_list, self.inf_edge_list, self.surface, self.name)
        # self.executed = True

        for stage in self.sys_build_list:
            stage()

    def build_stage(self):
        self.sys_data = build_mouth_sys(self.sup_edge_list, self.inf_edge_list, self.surface, self.name)

        self.sup_low_res_edge_curve = self.sys_data['sup_lip_sys']['driver_low_res_curve']
        self.sup_edge_curve = self.sys_data['sup_lip_sys']['edge_extract_curve']
        self.inf_low_res_edge_curve = self.sys_data['inf_lip_sys']['driver_low_res_curve']
        self.inf_edge_curve = self.sys_data['inf_lip_sys']['edge_extract_curve']

        self.executed = True

        # sys_data = {
        #     "main_sys_grp": main_sys_grp,
        #     "loc_pci_node_list": loc_pci_node_list,
        #     "driver_wire_node": driver_wire_node,
        #     "skinCluster_node": skinCluster_node,
        #     "surface_closestPoint_node_list": surface_sys_data[1],
        #     "surface_setRange_node_list": surface_sys_data[2],
        #     "ctrl_list": ctrl_list,
        #     "ctrl_dict": ctrl_dict,
        #     "remoteCtrl_dict": remoteCtrl_loc_dict,
        #     "remoteCtrl_list": remoteCtrl_loc_list
        # }

    def delete(self):
        if self.executed:
            for item in self.sys_data[0]: 
                try:
                    cmds.delete(self.sys_data[0][item], self.sys_data[1][item])
                except RuntimeError:
                    print('[MOUTH SLIDE SYSTEM - DELETE] Nothing found for {} to be deleted'.format(item))
                    continue
            cmds.delete(self.sys_data[2])
        else:
            cmds.warning("[MOUTH SLIDE SYSTEM] System not yet executed")

    def load_data(self):
        mouth_build_pack = "Mouth_BuildPack"
        self.name = cmds.getAttr(mouth_build_pack + ".sys_name")
        self.surface = cmds.getAttr(mouth_build_pack + ".sys_surface")
        self.sup_edge_list = ast.literal_eval(cmds.getAttr(mouth_build_pack + ".sup_edge"))
        self.inf_edge_list = ast.literal_eval(cmds.getAttr(mouth_build_pack + ".inf_edge"))
        self.mouth_slide_ctrl_template = cmds.getAttr(mouth_build_pack + ".mouth_slide_template")
        self.setting_ctrl_template = cmds.getAttr(mouth_build_pack + ".settings_template")
        self.head_ctrl_template = cmds.getAttr(mouth_build_pack + ".head_ctrl_template")

    def store_data(self):
        cmds.setAttr(self.build_pack + ".sys_name", self.name, type='string')
        cmds.setAttr(self.build_pack + ".sys_surface", self.surface, type='string')
        cmds.setAttr(self.build_pack + ".sup_edge", self.sup_edge_list, type='string')
        cmds.setAttr(self.build_pack + ".inf_edge", self.inf_edge_list, type='string')
        cmds.setAttr(self.build_pack + ".settings_template", self.setting_ctrl_template, type='string')
        cmds.setAttr(self.build_pack + ".mouth_slide_template", self.mouth_slide_ctrl_template, type='string')
        cmds.setAttr(self.build_pack + ".head_ctrl_template", self.head_ctrl_template, type='string')

    # system build actions
    def create_main_face_control(self):
        # create control
        self.main_face_control = tpCtrl.Control(name=self.name + '_main_face_ctrl')
        # set to circle
        self.main_face_control.set_type('open_circle')
        # add top group
        self.main_face_control.add_offset_grp()
        # place it at neck position
        self.main_face_control.top_group_match_position(self.head_ctrl_template, t=True)

        self.control_object_dict.update({self.main_face_control.get_name(): self.main_face_control})

    def create_mouth_slide_surface_control(self):
        # create cluster
        cluster_node, cluster_handle = cmds.cluster(self.sup_low_res_edge_curve,
                                                    self.inf_low_res_edge_curve,
                                                    self.surface,
                                                    name='{}_surfaceSys_cls'.format(self.name))

        # create control
        self.surface_control = tpCtrl.Control(name='{}_offset_ctrl'.format(self.name))
        self.surface_control.set_type('open_circle')
        self.surface_control.add_offset_grp()  # top group with no index would be better

        # position control according to template
        self.surface_control.top_group_match_position(self.mouth_slide_ctrl_template, t=True)

        # connect transformation attributes
        for attr in ".t,.rotate,.s".split(','):
            cmds.connectAttr(self.surface_control.get_name() + attr, cluster_handle + attr, force=True)

        cmds.parent(self.surface_control.get_top_group(), self.main_face_control.get_name())

    def build_mouth_slide_control(self):
        # create cluster
        cluster_node, cluster_handle = cmds.cluster(self.sup_low_res_edge_curve,
                                                    self.inf_low_res_edge_curve,
                                                    name='{}_lipSlide_cls'.format(self.name))
        # create control
        self.mouth_slide_control = tpCtrl.Control(name='{}_slide_ctrl'.format(self.name))
        self.mouth_slide_control.add_offset_grp()  # top group with no index would be better

        # position control according to template
        self.mouth_slide_control.top_group_match_position(self.mouth_slide_ctrl_template, t=True)

        # connect transformation attributes
        for attr in ".t,.rotate,.s".split(','):
            cmds.connectAttr(self.mouth_slide_control.get_name() + attr, cluster_handle + attr, force=True)

        cmds.parent(self.mouth_slide_control.get_top_group(), self.surface_control.get_name())

    def create_setting_control(self):
        # create control
        # place it in template location
        # parent to parent group

        # create control attributes

        # create visibility attributes

        pass

    # def export_control_shapes(self):
    #     """
    #     Exports controls shapes based on the control objects that have been created
    #     during the build process.
    #
    #     Obs. 14.11.2022 - This feature should be inside of the class, or in a control manager
    #     class - Having it outside of the class just makes the system broken, considering that
    #     if we had to transfer this function to another project, this feature wouldn't be
    #     available.
    #
    #     :return:
    #     """
    #
    #     all_controls_data_dict = {}
    #
    #     for control in self.control_object_dict:
    #         shape_dict = self.control_object_dict[control].get_position_data()
    #
    #         control_data = {
    #             'curve_color': self.control_object_dict[control].get_curve_color(),
    #             'curve_form': self.control_object_dict[control].get_shape_type(),
    #             'shape_data': shape_dict
    #         }
    #
    #         all_controls_data_dict.update({control: control_data})
    #
    #     tpUtils.export_dict_as_json(all_controls_data_dict,
    #                                 self.project_data_file_dict['control_shape'],
    #                                 self.project_dir_dict['control_shape'])
    #
    #     print('[File Exported] {}{}.json'.format(self.project_data_file_dict['control_shape'],
    #                                              self.project_dir_dict['control_shape']))
    #
    # def _import_control_shapes(self):
    #     control_shape_data = tpUtils.read_json_file(
    #         '{}{}.json'.format(self.project_dir_dict['control_shape'],
    #                            self.project_data_file_dict['control_shape']))
    #
    #     for control in control_shape_data:
    #         control_type = self.control_object_dict[control].get_shape_type()
    #
    #         if control_type != control_shape_data[control]['curve_form']:
    #             self.control_object_dict[control].set_type(control_shape_data[control]['curve_form'])
    #
    #         self.control_object_dict[control].restore_shape_position_from_data(
    #             control_shape_data[control]['shape_data'])
    #         self.control_object_dict[control].set_color_rgb(control_shape_data[control]['curve_color'])



def load_attr(build_pack, attr):
    data = ",".join(cmds.ls(sl=1))
    cmds.setAttr(build_pack + attr, data, type="string")


def build_corner(sup_ctrl, inf_ctrl, sup_remoteCtrl, inf_remoteCtrl, name):
    """
    Builds mouth corner controls, which brings together sup and inf lip systems.
    Until this point both systems are independent.

    :param sup_ctrl:
    :param inf_ctrl:
    :param sup_remoteCtrl:
    :param inf_remoteCtrl:
    :param name:
    :return:
    """
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
    avg_position = [(posA + posB) / 2 for posA, posB in zip(sup_position, inf_position)]
    avg_rotation = [(roA + roB) / 2 for roA, roB in zip(sup_rotation, inf_rotation)]

    # Create corner control and postion according to calculated position
    corner_ctrl = tpu.build_ctrl(ctrl_type="sphere", name=name + "_Corner", scale=0.3, spaced=1)
    cmds.xform(corner_ctrl['group'], t=avg_position, ro=avg_rotation)
    cmds.parent(sup_ctrl_grp, inf_ctrl_grp, corner_ctrl['control'])

    # Create remoteCtrl Locator and position
    corner_remoteCtrl_loc = cmds.spaceLocator(n="{}_RemoteCtrl_Loc".format(name))[0]
    corner_remoteCtrl_grp = cmds.group(n=corner_remoteCtrl_loc + "_Grp")
    cmds.xform(corner_remoteCtrl_grp, t=avg_position, ro=avg_rotation)
    cmds.parent(sup_remoteCtrl_grp, inf_remoteCtrl_grp, corner_remoteCtrl_loc)

    # Connect Corner control and remote control Locator
    for attr in ".t,.rotate,.s".split(','): cmds.connectAttr(corner_ctrl['control'] + attr,
                                                             corner_remoteCtrl_loc + attr, f=1)
    # Reduce locator scale
    for dimension in ["X", "Y", "Z"]: cmds.setAttr("{}.localScale{}".format(corner_remoteCtrl_loc, dimension), 0.4)
    # Turn Sup and Inf controls visibility off
    cmds.setAttr(sup_ctrl_grp + ".visibility", 0)
    cmds.setAttr(inf_ctrl_grp + ".visibility", 0)

    sys_data = {
        "corner_ctrl": corner_ctrl,
        "corner_remoteCtrl": corner_remoteCtrl_grp
    }

    return sys_data


def build_surface():
    """ Stage under development"""
    pass


# MAIN FUNCTION SECTION _______________________________________________________________

def build_mouth_sys(sup_edge_list=[], inf_edge_list=[], surface="", name=""):
    """
    MOD LIST
    - Add full system ctrl
    - Add control on top of all - pivot on surface center

    :param sup_edge_list:
    :param inf_edge_list:
    :param surface:
    :param name:
    :return:
    """
    
    # Create independent superior and inferior lip systems
    sup_lip_sys = sysFromEdgeLoop(sup_edge_list, surface, name=name + "_Sup_Lip")
    inf_lip_sys = sysFromEdgeLoop(inf_edge_list, surface, name=name + "_Inf_Lip")
    # Create main group for both systems
    main_mouth_grp = cmds.group(sup_lip_sys['main_sys_grp'], inf_lip_sys['main_sys_grp'], n=name + "_Sys_Grp")

    # Offset controls position to be in front of lips
    sup_ctrl_dict = sup_lip_sys['ctrl_dict']
    inf_ctrl_dict = inf_lip_sys['ctrl_dict']
    offset_y = 0.6
    offset_z = 0.85

    for sup_ctrl, inf_ctrl in zip(sup_ctrl_dict, inf_ctrl_dict):
        sup_position = cmds.xform(sup_ctrl_dict[sup_ctrl], q=1, t=1)
        inf_position = cmds.xform(inf_ctrl_dict[inf_ctrl], q=1, t=1)
        sup_offset = [sup_position[0], sup_position[1] + offset_y, sup_position[2] + offset_z]
        inf_offset = [inf_position[0], inf_position[1] - offset_y, sup_position[2] + offset_z]

        cmds.xform(sup_ctrl_dict[sup_ctrl], t=sup_offset)
        cmds.xform(inf_ctrl_dict[inf_ctrl], t=inf_offset)

    # Get created control lists
    sup_ctrl_list = sup_lip_sys['ctrl_list']
    inf_ctrl_list = inf_lip_sys['ctrl_list']
    sup_remoteCtrl_list = sup_lip_sys["remoteCtrl_list"]
    inf_remoteCtrl_list = inf_lip_sys["remoteCtrl_list"]
    # Create unified corner controls
    r_corner_ctrl = build_corner(sup_ctrl=sup_ctrl_list[0], inf_ctrl=inf_ctrl_list[0],
                                 sup_remoteCtrl=sup_remoteCtrl_list[0], inf_remoteCtrl=inf_remoteCtrl_list[0],
                                 name="R_" + name)
    
    l_corner_ctrl = build_corner(sup_ctrl=sup_ctrl_list[-1], inf_ctrl=inf_ctrl_list[-1],
                                 sup_remoteCtrl=sup_remoteCtrl_list[-1], inf_remoteCtrl=inf_remoteCtrl_list[-1],
                                 name="L_" + name)

    cmds.parent(
        r_corner_ctrl['corner_remoteCtrl'],
        l_corner_ctrl['corner_remoteCtrl'],
        r_corner_ctrl['corner_ctrl']['group'],
        l_corner_ctrl['corner_ctrl']['group'],
        main_mouth_grp)

    return {
        'sup_lip_sys': sup_lip_sys,
        'inf_lip_sys': inf_lip_sys,
        'main_sys_grp': main_mouth_grp}


def sysFromEdgeLoop(edge, surface, name=""):
    # Extract curve from edge
    cmds.select(edge)
    anchor_curve = cmds.polyToCurve(name=name + '_Anchor_Crv', form=2, 
                                    degree=1, conformToSmoothMeshPreview=0)[0]
    
    # Check curve direction and reverse
    reverse_crv = xDirection_positive(anchor_curve)
    if reverse_crv is False:
        cmds.reverseCurve(anchor_curve, ch=0, rpo=1)
    cmds.delete(anchor_curve, ch=1)

    # Create locators on each anchor curve CV
    locator_list = locatorOnCVs(anchor_curve, scale=0.2)
    # Connect locators to CVs
    loc_pci_node_list = connectLocatorToCrv(locator_list, anchor_curve)

    # Duplicate -> Rebuild to low res
    driver_crv = cmds.duplicate(anchor_curve, name=name + '_Driver_Crv')[0]
    cmds.rebuildCurve(driver_crv, ch=0, rpo=1, rt=0, end=1, kr=0,
                      kcp=0, kep=1, kt=1, s=6, d=1, tol=0.01)
    cmds.rebuildCurve(driver_crv, ch=0, rpo=1, rt=0, end=1, kr=0,
                      kcp=1, kep=1, kt=1, s=4, d=3, tol=0.01)
    cmds.delete(driver_crv, ch=1)
    
    # Wire high res to low res curve
    driver_wire_node = cmds.wire(anchor_curve, w=driver_crv, gw=False, en=1.000000, ce=0.000000, li=0.000000)

    # Create joints on each low res CV
    cv_position = getCVAngle(driver_crv)
    driver_jnt_list = []
    ctrl_dict = {}
    ctrl_list = []
    remoteCtrl_loc_dict = {}
    remoteCtrl_loc_list = []

    for n, position in enumerate(cv_position):
        cmds.select(cl=1)
        driver_jnt = cmds.joint(rad=0.3, n="{}_{:02d}_Ctrl_Jnt".format(name, n))
        driver_jnt_list.append(driver_jnt)
        cmds.xform(driver_jnt, t=position[0], ro=[0, position[1][1], 0])

        # Create controls for each joint
        ctrl_data = tpu.build_ctrl(ctrl_type="cube", name="{}_{:02d}".format(name, n), scale=0.3, spaced=1)
        ctrl_dict.update({ctrl_data['control']: ctrl_data['group']})
        ctrl_list.append(ctrl_data['control'])
        cmds.xform(ctrl_data['group'], t=position[0], ro=[0, position[1][1], 0])

        # Create remote ctrl locator
        remoteCtrl_loc = cmds.spaceLocator(n="{}_{:02d}_RemoteCtrl_Loc".format(name, n))[0]

        for i in "X,Y,Z".split(","):  # setting scale
            cmds.setAttr("{}.localScale{}".format(remoteCtrl_loc, i), 0.3)

        remoteCtrl_loc_grp = cmds.group(remoteCtrl_loc, n=remoteCtrl_loc + "_Grp")
        remoteCtrl_loc_dict.update({remoteCtrl_loc:remoteCtrl_loc_grp})
        remoteCtrl_loc_list.append(remoteCtrl_loc)
        cmds.xform(remoteCtrl_loc_grp, t=position[0], ro=[0, position[1][1], 0])

        # Connect control/joint transforms
        cmds.parentConstraint(remoteCtrl_loc, driver_jnt, mo=1)
        for attr in ".t,.rotate,.s".split(','):
            cmds.connectAttr(ctrl_data['control'] + attr, remoteCtrl_loc + attr, f=1)

    # Bind low res curve to joints
    skinCluster_node = cmds.skinCluster(driver_jnt_list, driver_crv)

    # Create system on surface
    surface_sys_data = follicleOnClosestPoint(surface, locator_list, name)
    follicle_dict = surface_sys_data[0]

    # Create joints for each follicle
    follicle_jnt_list = jointsOnSelection(follicle_dict.keys(), constraint=True, rad=0.2)

    # Group and organize system on Outliner
    crv_grp = cmds.group(anchor_curve, driver_crv, driver_crv + "BaseWire", n="{}_Crv_Grp".format(name))
    # Locator Groups
    remoteCtrl_loc_grp = cmds.group(remoteCtrl_loc_dict.values(), n="{}_RemoteCtrl_Loc_Grp".format(name))
    aim_loc_grp = cmds.group(locator_list, n="{}_Aim_Loc_Grp".format(name))
    locator_grp = cmds.group(remoteCtrl_loc_grp, aim_loc_grp, n="{}_Loc_Grp".format(name))
    # Joint groups
    bind_joint_grp = cmds.group(follicle_jnt_list, n="{}_Bind_Jnt_Grp".format(name))
    ctrl_joint_grp = cmds.group(driver_jnt_list, n="{}_Ctrl_Jnt_Grp".format(name))
    joint_grp = cmds.group(bind_joint_grp, ctrl_joint_grp, n="{}_Jnt_Grp".format(name))
    # Controls group
    ctrl_grp = cmds.group(ctrl_dict.values(), n="{}_Ctrl_Grp".format(name))
    # Follicle group
    follicle_grp = cmds.group(follicle_dict.keys(), n="{}_Flc_Grp".format(name))

    main_sys_grp = cmds.group(crv_grp, locator_grp, ctrl_grp, follicle_grp, joint_grp, n="{}_Sys_Grp".format(name))

    sys_data = {
        "main_sys_grp": main_sys_grp, 
        "loc_pci_node_list": loc_pci_node_list, 
        "driver_wire_node": driver_wire_node, 
        "skinCluster_node": skinCluster_node, 
        "surface_closestPoint_node_list": surface_sys_data[1], 
        "surface_setRange_node_list": surface_sys_data[2], 
        "ctrl_list": ctrl_list, 
        "ctrl_dict": ctrl_dict, 
        "remoteCtrl_dict": remoteCtrl_loc_dict,
        "remoteCtrl_list": remoteCtrl_loc_list,
        'driver_low_res_curve': driver_crv,
        'edge_extract_curve': anchor_curve
        }

    return sys_data


"""
Created Nodes
    - anchor_crv
    - driver_crv
    - aim locators
    - aim locators nodes
    - driver crv wire node
    - driver crv skinCluster node
    - ctrls - ctrl grps
    - ctrl joints
    - follicle joints
    - follicle sys data
        - follicle_dict
        - closesPoint_node_list
        - setRange_node_list

Groups
    - Mouth segment system
        - crv grp
        - locator grp
        - ctrl grp
        - remote ctrl grp
        - follicle grp
        - joint grp
            - ctrl joints
            - bind joints
"""


def follicleOnClosestPoint(surface, locator_list, name=""):

    surface_shape = cmds.listRelatives(surface, type="shape")[0]
    follicle_dict = {}
    closestPoint_node_list = []
    setRange_node_list = []

    for n, loc in enumerate(locator_list):
        # Create Point on Curve Info node
        closestPoint_node = cmds.createNode("closestPointOnSurface", n="{}_{:02d}_closestPointOnSrf".format(name, n))
        closestPoint_node_list.append(closestPoint_node)
        # Create follicle on surface
        follice_data = createFollicle(inputSurface=[surface_shape], hide=0, name="{}_{:02d}_Flc".format(name, n))
        follicle_dict.update({follice_data[0]:follice_data[1]})

        # Connect surface to pci
        cmds.connectAttr(surface_shape + ".local", closestPoint_node + ".inputSurface", f=1)
        # Connect locator to pci 
        cmds.connectAttr(loc + ".translate", closestPoint_node + ".inPosition")
        
        # Create set range for parameterV
        setRage_node = cmds.shadingNode("setRange", asUtility=1, n="{}_{:02d}_setRange".format(name, n))
        setRange_node_list.append(setRage_node)
        # Get surface max U and V parameters
        cmds.connectAttr(surface_shape + ".maxValueV", setRage_node + ".oldMaxX")
        cmds.connectAttr(surface_shape + ".maxValueU", setRage_node + ".oldMaxY")
        cmds.setAttr(setRage_node + ".maxX", 1)
        cmds.setAttr(setRage_node + ".maxY", 1)
        # Connect pci to follicle
        cmds.connectAttr(closestPoint_node + ".parameterV", setRage_node + ".valueX", f=1)
        cmds.connectAttr(closestPoint_node + ".parameterU", setRage_node + ".valueY", f=1)
        cmds.connectAttr(setRage_node + ".outValueX", follice_data[1] + ".parameterV")
        cmds.connectAttr(setRage_node + ".outValueY", follice_data[1] + ".parameterU")

    return follicle_dict, closestPoint_node_list, setRange_node_list


# UTILITY FUNCTION SECTION _______________________________________________________________
def connectLocatorToCrv(loc_list, crv):
    pointOnCurve_node_list = []

    for loc in loc_list :
        loc_pos = cmds.xform(loc, q=1, ws=1, t=1)
        loc_u = getUParam(loc_pos, crv)
        pciNode_name = loc.replace("_loc", "_pci")
        pciNode = cmds.createNode("pointOnCurveInfo", n=pciNode_name) 
        cmds.connectAttr(crv + ".worldSpace", pciNode + ".inputCurve")
        cmds.setAttr(pciNode + ".parameter", loc_u)
        cmds.connectAttr(pciNode + ".position" , loc + ".t")

        pointOnCurve_node_list.append(pciNode)

    return pointOnCurve_node_list


def locatorOnCVs(path_crv, scale=1):
    """ Locator on CV's - Select curve, run script """

    cmds.select(cl=1)
    cv_list = cmds.getAttr(path_crv + '.cv[:]')
    locator_list = []
    
    for n, cv in enumerate(cv_list):
        locator = cmds.spaceLocator(n="{}_{:02d}_Loc".format(path_crv, n))[0]
        for i in "X,Y,Z".split(","): cmds.setAttr("{}.localScale{}".format(locator, i), scale)
        cmds.xform(locator, t=cv)
        cmds.select(cl=1)
        
        locator_list.append(locator)
        
    return locator_list


# Out of use
def jointsOnCVs(path_crv):
    cmds.select(cl=1)
    cv_list = cmds.getAttr(path_crv + '.cv[:]')
    joint_list = []
    
    for i, cv in enumerate(cv_list):
        joint = cmds.joint(n="{}_{:02d}_Jnt".format(path_crv, i))
        cmds.xform(joint, t=cv)
        cmds.select(cl=1)
        
        joint_list.append(joint)
        
    return joint_list


def jointsOnSelection(selection, constraint, rad=1):
    """ Creates and places joints on each selection
        Returns - List of joints created """
        
    joint_list = []
    
    for i in selection:
        translate = cmds.xform(i, q=1, t=1)
        rotate = cmds.xform(i, q=1, ro=1)

        newJoint = cmds.joint(rad=rad, n=i + "_Jnt")
        cmds.select(cl=1)
        cmds.xform(newJoint, t=translate, ro=rotate)

        if constraint: cmds.parentConstraint(i, newJoint, mo=1)

        joint_list.append(newJoint)

    return joint_list


def getUParam(position=[], crv=None):
    """ Get ParameterU based on position on curve 
        Function will break the undo stack - Further improvement necessary
        Function using Maya API 1.0 """

    point = om.MPoint(position[0],position[1],position[2])
    curveFn = om.MFnNurbsCurve(getDagPath(crv))
    paramUtill = om.MScriptUtil()
    paramPtr = paramUtill.asDoublePtr()
    isOnCurve = curveFn.isPointOnCurve(point)
    
    if isOnCurve == True :
        curveFn.getParamAtPoint(point, paramPtr, 0.001, om.MSpace.kObject)
    else :
        point = curveFn.closestPoint(point, paramPtr, 0.001, om.MSpace.kObject)
        curveFn.getParamAtPoint(point, paramPtr, 0.001, om.MSpace.kObject)
    
    param = paramUtill.getDouble(paramPtr) 

    return param


def getDagPath(objectName):
    selectionList = om.MSelectionList()
    selectionList.add(objectName)
    oNode = om.MDagPath()
    selectionList.getDagPath(0, oNode)

    return oNode


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
    
    # Using pointPosition to get first and last CVs tranlation
    start_x_position = cmds.pointPosition(curve + '.cv[0]')[0]
    end_x_position = cmds.pointPosition(curve + '.cv[{}]'.format(cvCount))[0]

    if start_x_position <= end_x_position: x_direction = True
    else: x_direction = False
    
    return x_direction


def getPointOnCurve(crv, parameter, inverse=0):
    """ Gets position and rotation of point on curve using motion path """

    poc_loc = cmds.spaceLocator(name= 'Poc_Temp_Loc')
    mPath_Crv = cmds.duplicate(crv, name= 'mPath_Temp_Crv')[0]
    cmds.delete(mPath_Crv, ch=1)
    
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


def getCVAngle(crv):
    """ Given a curve, returns the rotation tangent on each CV """

    locator_list = locatorOnCVs(crv)
    position_list = []

    for n, loc in enumerate(locator_list):
        loc_pos = cmds.xform(loc, q=1, ws=1, t=1)
        loc_u = getUParam(loc_pos, crv)
        
        loc_rotation = getPointOnCurve(crv, loc_u)
        # new_loc = cmds.spaceLocator(n="{}_{:02d}_Loc".format(crv, n))
        # cmds.xform(new_loc, t=loc_rotation[0], ro=[loc_rotation[1][0], loc_rotation[1][1], 0])
        
        position_list.append(loc_rotation)

    cmds.delete(locator_list)

    return position_list


def curvesFromSurface(surface, UorV="v", crvAmount=10, name=""):
    """ This funciton extracts curves from a NURBS Surface """

    # Get max U V valeus
    maxValueU = cmds.getAttr(surface + ".maxValueU")
    maxValueV = cmds.getAttr(surface + ".maxValueV")

    # Calculate space between each curve
    uStep = maxValueU / (crvAmount -1)
    vStep = maxValueV / (crvAmount -1)

    # Select U or V valeu based on user input
    step = uStep if UorV == "u" else vStep
    crv_list = []

    for n in range(crvAmount):
        # Calculate current crv position
        crv_parameter = n * step
        crv = cmds.duplicateCurve("{}.{}[{}]".format(surface, UorV, crv_parameter), 
                                    local=True, ch=0, n="{}_{:02d}_Crv".format(name, n))
        # Unparent from surface
        cmds.parent(crv, w=1)
        # Add curve list
        crv_list.append(crv[0])

    return crv_list


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

# BACKUP TOOLS _______________________________________________________________________


# unused ------
def tp_ctrlInvert(ctrl_list):
    """ Invert control translateX connection - For right side ctrls"""

    for ctrl in ctrl_list:
        jnt = cmds.listConnections(ctrl, d=1)[0]
        ctrl_grp = cmds.listRelatives(ctrl, p=1)[0]
                
        mult = cmds.shadingNode('multiplyDivide', asUtility=1, n= ctrl + '_MulpD')
        cmds.setAttr(mult + '.input2X', -1)
        cmds.connectAttr(ctrl + '.translate.translateX', mult + '.input1.input1X', f=1)
        cmds.connectAttr(mult + '.output.outputX', jnt + '.translate.translateX', f=1)
        
        cmds.setAttr(ctrl_grp + ".scaleX", -1)


def neckConnect(ctrl, target_list):
    target_len = len(target_list)
    rotation_fraction = 1.0 / target_len

    for target in range(target_len):
        fraction_mpDiv_node = cmds.createNode("multiplyDivide", n="{}_fraction_mpDiv".format(target))
        cmds.setAttr(fraction_mpDiv_node + ".input2X", rotation_fraction)
        cmds.setAttr(fraction_mpDiv_node + ".input2Y", rotation_fraction)
        cmds.setAttr(fraction_mpDiv_node + ".input2Z", rotation_fraction)
        cmds.connectAttr(ctrl + ".r", fraction_mpDiv_node + ".input1")

        inverse_mpDiv_node = cmds.createNode("multiplyDivide", n="{}_inverse_mpDiv".format(target))
        cmds.setAttr(inverse_mpDiv_node + ".input2X", -1)
        cmds.setAttr(inverse_mpDiv_node + ".input2Z", -1)

        cmds.connectAttr(fraction_mpDiv_node + ".outputX", inverse_mpDiv_node + ".input1X")
        cmds.connectAttr(fraction_mpDiv_node + ".outputZ", inverse_mpDiv_node + ".input1Z")
        cmds.connectAttr(fraction_mpDiv_node + ".outputY", target + ".rx")
        cmds.connectAttr(inverse_mpDiv_node + ".outputX", target + ".rz")
        cmds.connectAttr(inverse_mpDiv_node + ".outputZ", target + ".ry")
