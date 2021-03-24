# -------------------------------------------------------------------------------
# Name:        tp_flexiLoft v1.0
# Purpose:     Creates a flexible surface out of a set of curves
#              controled by ikSplines
#
# Author:      Thiago Paulino
# Location:    Vancouver, BC
# Contact:     tpaulino.com@gmail.com
#
# Created:     04/11/2019
# Copyright:   (c) Thiago Paulino 2019
# Licence:     MIT
# -------------------------------------------------------------------------------

from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as mc
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as omui

# LAYOUT SECTION ___________________________________________________


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


class FlexiLoftUI(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(FlexiLoftUI, self).__init__(parent)

        # Set window name and size
        self.setWindowTitle("tp_flexiLoft v1.0")
        self.setMinimumWidth(200)
        self.setMaximumWidth(600)
        # Delete helper button "?" from window
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        # Initialize Layout
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        self.ikSpline_chBox = QtWidgets.QCheckBox("ikSpline")
        self.bind_chBox = QtWidgets.QCheckBox("Bind")
        self.loft_chBox = QtWidgets.QCheckBox("Loft")
        self.cluster_chBox = QtWidgets.QCheckBox("Cluster")
        self.strechy_chBox = QtWidgets.QCheckBox("Strechy")

        self.ikSpline_chBox.setChecked(True)
        self.bind_chBox.setChecked(True)
        self.loft_chBox.setChecked(True)
        self.cluster_chBox.setChecked(True)
        self.strechy_chBox.setChecked(True)

        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setText("flexiLoft")
        self.angle_label = QtWidgets.QLabel("System Name:")

        self.build_button = QtWidgets.QPushButton("BUILD")
        self.build_button.setStyleSheet("background-color:#228F4E;"
                                        "min-height: 3em;")

    def create_layouts(self):
        sys_name_layout = QtWidgets.QHBoxLayout()
        sys_name_layout.addWidget(self.angle_label)
        sys_name_layout.addWidget(self.name_input)

        check_box_layout = QtWidgets.QHBoxLayout()
        check_box_layout.addWidget(self.ikSpline_chBox)
        check_box_layout.addWidget(self.bind_chBox)
        check_box_layout.addWidget(self.loft_chBox)
        check_box_layout.addWidget(self.cluster_chBox)
        check_box_layout.addWidget(self.strechy_chBox)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(sys_name_layout)
        main_layout.addLayout(check_box_layout)
        main_layout.addWidget(self.build_button)

    def create_connections(self):
        self.build_button.clicked.connect(self.build_system)

    def build_system(self):
        ik_spline = self.ikSpline_chBox.isChecked()
        bind = self.bind_chBox.isChecked()
        loft = self.loft_chBox.isChecked()
        cluster = self.cluster_chBox.isChecked()
        stretchy = self.strechy_chBox.isChecked()

        name = self.name_input.text()

        flexi_loft(add_ik=ik_spline, bind=bind, loft=loft, cluster=cluster, stretchy=stretchy, name=name)
    

def flexi_loft(add_ik=0, bind=0, loft=0, cluster=0, stretchy=0, name=""):
    raw_curves = mc.ls(sl=1)
    curves = []
    ik_handle_list = []
    ik_spline_crv_list = []
    joint_list = []
    joint_chain_dict = {}
    grp_list = []

    # Creating brand new, clean curves out of selection
    for j, n in enumerate(raw_curves, 1):
        new_curve = mc.duplicate(n, n="{}_Loft_Crv{}".format(name, j))
        try: 
            mc.parent(new_curve, w=1)
        except: 
            pass
        mc.makeIdentity(new_curve, apply=True, t=1, r=1, s=1, n=0)
        mc.delete(new_curve, ch=1)
        mc.xform(new_curve, cp=1)
        curves.append(new_curve[0])

    # Joint chain and ikSpline section
    for n, n in enumerate(curves):
        crv_joint_list = joint_on_curve_cvs(path_crv=n)
        parent_in_order(sel=crv_joint_list)
        mc.joint(crv_joint_list, e=1, oj="xyz", secondaryAxisOrient="yup")
        joint_chain_dict.update({n: crv_joint_list})
        joint_list.append(crv_joint_list[0])
        mc.select(cl=1)
        
        if add_ik == 1:
            # Creating ikSpline - rename curve - append to grouping lists
            ik_handle_data = mc.ikHandle(sj=crv_joint_list[0], ee=crv_joint_list[-1],
                                         sol="ikSplineSolver", n=n + "_ikHandle")
            ik_crv = mc.rename(ik_handle_data[2], "{}_ikSpline_Crv{}".format(name, n + 1))
            ik_handle_list.append(ik_handle_data[0])
            ik_spline_crv_list.append(ik_crv)

            if stretchy == 1:
                make_stretchy_spline(crv_joint_list, ik_crv, new_curve[0])

            if n == 0:
                # If it is the first loop - create groups - else - parent new items
                ik_grp = mc.group(ik_handle_data[0], n=name + "_ikHandle_Grp")
                spline_grp = mc.group(ik_crv, n=name + "_ikSpline_Crv_Grp")
                grp_list.append(ik_grp)
                grp_list.append(spline_grp)
            else: 
                mc.parent(ik_handle_data[0], ik_grp)
                mc.parent(ik_crv, spline_grp)

        if bind == 1:
            mc.skinCluster(crv_joint_list, n)

    if loft == 1: 
        loft_data = mc.loft(curves, ch=1, u=1, c=0, ar=0, d=3, ss=10, rn=0, po=1, rsn=1)
        loft_srf = mc.rename(loft_data[0], name + "_LoftSrf_Geo")
        loft_grp = mc.group(loft_srf, n=name + "_LoftSrf_Geo_Grp")
        grp_list.append(loft_grp)

    if cluster == 1 and add_ik == 1:
        # Creates clusters holding the same cv on each ikSpline curve
        # Calculating the number of Cv's for loop
        curve_deg = mc.getAttr(ik_spline_crv_list[0] + ".degree")
        curve_spa = mc.getAttr(ik_spline_crv_list[0] + ".spans")
        # CV's = degrees + spans
        cv_count = curve_deg + curve_spa
        cls_list = []

        for n in range(cv_count):
            mc.select(cl=1)
            for j in ik_spline_crv_list:
                mc.select("{}.cv[{}]".format(j, n), add=1)
            cluster = mc.cluster(n="{}_Csl{}".format(name, n))
            cls_list.append(cluster[1])
        
        cluster_grp = mc.group(cls_list, n=name + "_Cls_Grp")
        grp_list.append(cluster_grp)

    else:
        mc.warning("addIk is off")

    curves_grp = mc.group(curves, n="{}_Loft_Crv_Grp".format(name))
    joint_grp = mc.group(joint_list, n=name + "_Jnt_Grp")
    grp_list.append(curves_grp)
    grp_list.append(joint_grp)
    sys_grp = mc.group(grp_list, n=name + "_Sys_Grp")

    return sys_grp


def make_stretchy_spline(jnt_chain, spline_crv, name):
    # Create float constant - Store original length
    arc_length_original = mc.shadingNode("floatConstant", asUtility=1, n=name + "_arcLength_init")
    # Curve info to get arcLength
    crv_info_node = mc.shadingNode("curveInfo", asUtility=1, n=name + "_curveInfo")
    
    # Get initial arcLength and store in float content
    mc.connectAttr(spline_crv + ".local", crv_info_node + ".inputCurve")
    arc_length_data = mc.getAttr(crv_info_node + ".arcLength")
    mc.setAttr(arc_length_original + ".inFloat", arc_length_data)

    # Use variable arc length value from crvInfo node to calculate stretch percentage
    multiply_node = mc.shadingNode("multiplyDivide", asUtility=1, n=name + "_joint_scaleMath_multDiv")
    mc.setAttr(multiply_node + ".operation", 2)
    mc.connectAttr(arc_length_original + ".outFloat", multiply_node + ".input2X")
    mc.connectAttr(crv_info_node + ".arcLength", multiply_node + ".input1X")
    
    # Connect math result to joints scale
    for joint in jnt_chain:
        mc.connectAttr(multiply_node + ".outputX", joint + ".scaleX")


def joint_on_curve_cvs(path_crv):
    """
    Creates joints for each CV on Curve
    :param path_crv:
    :return joint_list:
    """
    mc.select(cl=1)
    cv_list = mc.getAttr(path_crv + '.cv[:]')
    joint_list = []
    
    for i, cv in enumerate(cv_list):
        joint = mc.joint(n="{}_Jnt{}".format(path_crv, i))
        mc.xform(joint, t=cv)
        mc.select(cl=1)
        
        joint_list.append(joint)
        
    return joint_list


def parent_in_order(sel):
    """
    Parent in selection order
    :param sel:
    :return:
    """
    for z, i in enumerate(sel):
        mc.parent(sel[z + 1], i)

        if z+1 >= len(sel)-1:
            break


def parent_in_list_order(item_list):
    """
    Parent in selection order
    :param item_list:
    :return:
    """
    for z, i in enumerate(item_list):
        mc.parent(sel[z + 1], i)

        if z+1 >= len(sel)-1:
            break


def create_curve_from_point_list(point_list):
    pass


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
    mc.delete(bridge_curve, ch=1)

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


class ProxyCurve:

    def __init__(self):
        self.curve = None
        self.point_list = None
        self.degree = None

    def build(self):
        self.curve = mc.curve(d=True, p=self.point_list, name='{}_crv'.format(name))

    def set_to_proxy(self):
        mc.setAttr("{}.overrideEnabled".format(self.curve), 1)
        mc.setAttr("{}.overrideDisplayType".format(self.curve), 1)





