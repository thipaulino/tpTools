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

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as omui

# LAYOUT SECTION ___________________________________________________

def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

class flexiLoft_UI(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(flexiLoft_UI, self).__init__(parent)

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
        sysName_layout = QtWidgets.QHBoxLayout()
        sysName_layout.addWidget(self.angle_label)
        sysName_layout.addWidget(self.name_input)

        checkBox_layout = QtWidgets.QHBoxLayout()
        checkBox_layout.addWidget(self.ikSpline_chBox)
        checkBox_layout.addWidget(self.bind_chBox)
        checkBox_layout.addWidget(self.loft_chBox)
        checkBox_layout.addWidget(self.cluster_chBox)
        checkBox_layout.addWidget(self.strechy_chBox)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(sysName_layout)
        main_layout.addLayout(checkBox_layout)
        main_layout.addWidget(self.build_button)

    def create_connections(self):
        self.build_button.clicked.connect(self.build_system)

    def build_system(self):
        ikSpline = self.ikSpline_chBox.isChecked()
        bind = self.bind_chBox.isChecked()
        loft = self.loft_chBox.isChecked()
        cluster = self.cluster_chBox.isChecked()
        strechy = self.strechy_chBox.isChecked()

        name = self.name_input.text()

        flexiLoft(addIk=ikSpline, bind=bind, loft=loft, cluster=cluster, strechy=strechy, name=name)
    
def flexiLoft(addIk=0, bind=0, loft=0, cluster=0, strechy=0, name=""):
    raw_curves = cmds.ls(sl=1)
    curves = []
    ikHandle_list = []
    ikSpline_crv_list = []
    joint_list = []
    joint_chain_dict = {}
    grp_list = []

    # Creating brand new, clean curves out of selection
    for j, i in enumerate(raw_curves, 1):
        new_curve = cmds.duplicate(i, n="{}_Loft_Crv{}".format(name, j))
        try: 
            cmds.parent(new_curve, w=1)
        except: 
            pass
        cmds.makeIdentity(new_curve, apply=True, t=1, r=1, s=1, n=0)
        cmds.delete(new_curve, ch=1)
        cmds.xform(new_curve, cp=1)
        curves.append(new_curve[0])

    # Joint chain and ikSpline section
    for n, i in enumerate(curves):
        crv_joint_list = jointsOnCVs(path_crv=i)
        parentInOrder(sel=crv_joint_list)
        cmds.joint(crv_joint_list, e=1, oj="xyz", secondaryAxisOrient="yup")
        joint_chain_dict.update({i:crv_joint_list})
        joint_list.append(crv_joint_list[0])
        cmds.select(cl=1)
        
        if addIk == 1:
            # Creating ikSpline - rename curve - append to grouping lists
            ikHandle_data = cmds.ikHandle(sj=crv_joint_list[0], ee=crv_joint_list[-1],
                                          sol="ikSplineSolver", n=i + "_ikHandle")
            ik_crv = cmds.rename(ikHandle_data[2], "{}_ikSpline_Crv{}".format(name, n+1))
            ikHandle_list.append(ikHandle_data[0])
            ikSpline_crv_list.append(ik_crv)

            if strechy == 1:
                makeStrechySpline(crv_joint_list, ik_crv, new_curve[0])

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

def makeStrechySpline(jnt_chain, spline_crv, name):
    # Create float constant - Store original length
    arcLength_init = cmds.shadingNode("floatConstant", asUtility=1, n=name + "_arcLength_init")
    # Curve info to get arcLength
    crvInfo_node = cmds.shadingNode("curveInfo", asUtility=1, n=name + "_curveInfo")
    
    # Get initial arcLength and store in float contant
    cmds.connectAttr(spline_crv + ".local", crvInfo_node + ".inputCurve")
    arcLength_data = cmds.getAttr(crvInfo_node + ".arcLength")
    cmds.setAttr(arcLength_init + ".inFloat", arcLength_data)

    # Use variable arcLenght value from crvInfo node to calculate strech percentage
    multiply_node = cmds.shadingNode("multiplyDivide", asUtility=1, n=name + "_joint_scaleMath_multDiv")
    cmds.setAttr(multiply_node + ".operation", 2)
    cmds.connectAttr(arcLength_init + ".outFloat", multiply_node + ".input2X")
    cmds.connectAttr(crvInfo_node + ".arcLength", multiply_node + ".input1X")
    
    # Connect math result to joints scale
    for joint in jnt_chain: cmds.connectAttr(multiply_node + ".outputX", joint + ".scaleX")

def jointsOnCVs(path_crv):
    """
    Creates joints for each CV on Curve
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
        
def parentInOrder(sel):
    """
    Parent in selection order
    :param sel:
    :return:
    """
    for z, i in enumerate(sel):
        cmds.parent(sel[z+1], i)

        if z+1 >= len(sel)-1:
            break
