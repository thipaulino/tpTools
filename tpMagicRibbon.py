# -------------------------------------------------------------------------------
# Name:        tp_magicRibbon v3.0
# Purpose:     Creates a ribbon system based on a surface
#
# Author:      Thiago Paulino
# Contact:     tpaulino.com@gmail.com
# LinkedIn:    https://www.linkedin.com/in/tpaulino/
# Location:    Vancouver, BC
#
# Created:     18/09/2019
# Copyright:   (c) Thiago Paulino 2019
# Licence:     MIT
# -------------------------------------------------------------------------------

from __future__ import division
import maya.cmds as cmds

# Run all functions bellow, select surface, and run this line
# buildSystem(ctrl_amount=5.0, fk_ctrl_amount=10, bindJnt_amount=50.0, name="fkSuccess")

def buildSystem(ctrl_amount=3, fk_ctrl_amount=3, bindJnt_amount=30.0, name=""):
	#########################################################################
	# SETUP SECTION ---
	# We need free controls only in the middle - so increasing the ctrl count by 2, considering the start and end
	crvStep = 100 / (ctrl_amount+1) / 100

	ctrl_color_dic = {'yellow':(0,1,1), 'orange':(0.28,0.42,0.99), 'red':(0.83,0.04,1), 'magenta':(1,0.04,0.57), 'purple':(1,0,0), 'babyBlue':(1,0.5,0), 'aqua':(1,1,0)}

	# Get surface from selection
	raw_surface = cmds.ls(sl=1)
	# Duplicate and rename surface
	surface = cmds.duplicate(raw_surface, n="{}_Output_Srf".format(name))
	cmds.setAttr(raw_surface[0] + ".visibility", 0)
	cmds.select(cl=1)
	# Create wire curve from surface
	v_curve = cmds.duplicateCurve(surface[0] + ".v[.5]", local=True, ch=0, n=name + "_MainWire_Crv")
	
	# Get degrees and spans to calculte CV's
	v_curve_shape = cmds.listRelatives(v_curve, s=1)[0]
	curveDeg = cmds.getAttr(v_curve_shape + ".degree")
	curveSpa = cmds.getAttr(v_curve_shape + ".spans")
	# CV's = degrees + spans
	cvCount = curveDeg + curveSpa
    
	# Deletes extra cvs, rebuilds curve, del hist, unparent curve
	cmds.delete(v_curve[0] + '.cv[{}]'.format(cvCount-2), v_curve[0] + '.cv[1]')
	cmds.rebuildCurve(v_curve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=1, kt=0, d=1, tol=0.01)
	cmds.rebuildCurve(v_curve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=1, kt=0, d=3, tol=0.01)
	cmds.delete(surface[0], v_curve, ch=1)
	cmds.parent(v_curve, w=1)
	cmds.select(cl=1)

	# Declaring lists for Group and Hide
	surface_list = []
	crv_list = []
	freeSys_ctrl_list = []
	main_ctrl_list = []
	cluster_list = []
	follicle_list = []
	
	#########################################################################
	# FK SYSTEM SECTION
	fk_sys_data = createFKSys(ctrl_amount=fk_ctrl_amount, curve=v_curve, name=name, color1=ctrl_color_dic['purple'], color2=ctrl_color_dic['magenta'])
	crv_list.append(fk_sys_data['curve'])
	crv_list.append(fk_sys_data['base_wire'])

	#########################################################################
	# FREE CONTROL SYSTEM SECTION ---
	# Create FreeCtrl Sys - According to Ctrl Amount
	for i in range(int(ctrl_amount)):
		# i starts in 0, so adding 1 to skip
		# Find current ctrl parameter
		parameter = (i + 1) * crvStep
		# Duplicate curve and surface for parallel sys
		crv_copy = cmds.duplicate(v_curve, n="{}_{}_freeSys_Wire_Crv".format(name, str(i)))
		surface_copy = cmds.duplicate(surface, n="{}_{}_freeSys_Srf".format(name, str(i)))
		cmds.select(cl=1)

		# Create free control system 
		new_ctrl_data = createCtrlSys(crv=crv_copy, rootCrv=v_curve, surface=surface_copy, rootSurface=surface, name=name, parameter=parameter, iteration=i)
		# Set control color
		setCtrlColor(new_ctrl_data[3], color=ctrl_color_dic['babyBlue'])

		# Add surface to blend list
		surface_list.append(surface_copy[0])
		# Get base wire - Append curve and Base Wire to group list
		crv_copy_bWire = crv_copy[0] + "BaseWire"
		crv_list.append(crv_copy[0])
		crv_list.append(crv_copy_bWire)
		# Append cluster, ctrl and follicle
		cluster_list.append(new_ctrl_data[0])
		freeSys_ctrl_list.append(new_ctrl_data[1])
		follicle_list.append(new_ctrl_data[2])
	
	# Group freeSys follicles
	follicle_freeSys_grp = cmds.group(follicle_list, n="{}_FreeSys_Flc_Grp".format(name))
	
	#########################################################################
	# MAIN SYSTEM SECTION ---
	# Build Start/End(Main) control system
	baseSys_surface_copy = cmds.duplicate(surface, n="{}_MainSys_Srf".format(name))
	main_ctrl_data = createBaseCtrl(v_curve, baseSys_surface_copy, name=name + "_Main", color1=ctrl_color_dic['orange'], color2=ctrl_color_dic['red'])

	# Append created clusters
	cluster_list.append(main_ctrl_data[4][1])
	cluster_list.append(main_ctrl_data[5][1])
	# Append created surface to blendshape list
	surface_list.append(baseSys_surface_copy[0])
	# Append created control groups to list
	main_ctrl_list.append(main_ctrl_data[1])
	main_ctrl_list.append(main_ctrl_data[3])
	# Append curve and base wire to group list
	v_curve_bWire = v_curve[0] + "BaseWire"
	crv_list.append(v_curve[0])
	crv_list.append(v_curve_bWire)

	#########################################################################
	# GLOBAL CTRL SECTION ---
	# Create joint
	outputSrf_jnt = cmds.joint(n="{}_GlobalCtrl_Jnt".format(name))
	# Position joint on surface middle - find mid position
	ctrl_avg = []
	ctrl_start_ws = cmds.xform(main_ctrl_data[0], q=1, t=1, ws=1)
	ctrl_end_ws = cmds.xform(main_ctrl_data[2], q=1, t=1, ws=1)
	for t, p in zip(ctrl_start_ws, ctrl_end_ws): ctrl_avg.append((t+p)/2)
	cmds.xform(outputSrf_jnt, t=ctrl_avg)
	# Skin bind to output surface
	skinBind_node = cmds.skinCluster(surface[0], outputSrf_jnt)
	# Create global ctrl + grp - ADD- Make scale variable to arcLength
	global_ctrl_data = bd_buildCtrl(ctrl_type="sphere", name=name + "_Global", scale=5)
	# Change Ctrl color
	setCtrlColor(global_ctrl_data[0], color=ctrl_color_dic['yellow'])
	# Position ctrl
	cmds.xform(global_ctrl_data[1], t=ctrl_avg)

	'''
	# Add control visibility attributes - Bind Ctrls, Free Ctrls
	cmds.addAttr(control, ln="bindCtrls", nn="Bind_Ctrls", at="double", min=0, max=1, dv=0.5, keyable=True)
	cmds.addAttr(control, ln="freeCtrls", nn="Free_Ctrls", at="double", min=0, max=360, dv=0, keyable=True)
	for i in follicle_list: cmds.connectAttr(global_ctrl_data[0] + ".bindCtrls", i + ".visibility")
	# Add search keyword as attr to  select bind joints 
	'''

	#########################################################################
	# SINE DEFORMER SYSTEM SECTION ---
	sine_data = createSineSys(surface, global_ctrl_data[0], name)
	# Append surface to surface list
	surface_list.append(sine_data[2])
	surface_list.append(sine_data[3])

	#########################################################################
	# BLENDSHAPE WRAP UP SECTION ---
	# Appends the output surface as the last surface - Selects in order and creates blendShape node
	surface_list.append(surface[0])
	cmds.select(cl=1)
	for x in surface_list: cmds.select(x, add=1)
	blnd_node = cmds.blendShape(automatic=1)
	# Gets number of shapes - Sets all weights to 1
	blnd_weights = cmds.blendShape(blnd_node, q=True, w=1)
	for y, z in enumerate(blnd_weights): cmds.blendShape(blnd_node, edit=1, w=[(y, 1.0)])
	cmds.select(cl=1)
	# Parent constrain output Ribbon jnt to global ctrl
	cmds.parentConstraint(global_ctrl_data[0], outputSrf_jnt, mo=1)
	cmds.scaleConstraint(global_ctrl_data[0], outputSrf_jnt)
	
	#########################################################################
	# FOLLICLE BIND JNTS SECTION ---
	# Place Follicle Grp and Joint Grp on proper groups bellow
	follicle_bindSys_data = createFlcBindSys(surface=surface, ctrl_amount=bindJnt_amount, ctrl_color=ctrl_color_dic['aqua'], global_ctrl=global_ctrl_data[0], name=name)
	
	#########################################################################
	# ORGANIZING, GROUP AND HIDE SECTION ---
	wire_grp = cmds.group(crv_list, n=name + "_Wire_Grp")
	cluster_grp = cmds.group(cluster_list, n=name + "_Cluster_Grp")
	follicle_grp = cmds.group(follicle_freeSys_grp, follicle_bindSys_data[0], sine_data[4], n=name + "_Follicle_Grp")
	surface_grp = cmds.group(surface_list, n=name + "_Surface_Grp")
	joint_grp = cmds.group(fk_sys_data['joint_group'], outputSrf_jnt, follicle_bindSys_data[2], n=name + "_Jnt_Grp")
	# Create new group for deformers
	deformer_grp = cmds.group(sine_data[1], n=name + "_Def_Grp")

	# Parent ctrl groups to global control
	freeSys_ctrl_grp = cmds.group(freeSys_ctrl_list, n=name + "_FreeSys_Ctrl_Grp")
	cmds.parent(main_ctrl_list, freeSys_ctrl_grp, fk_sys_data['fk_ctrl_grp'], global_ctrl_data[0])

	hide_list = [wire_grp, cluster_grp, surface_grp, follicle_freeSys_grp, joint_grp, deformer_grp, fk_sys_data['fk_remoteCtrl_grp']]
	for w in hide_list: cmds.setAttr(w + ".visibility", 0)

	# Parent Def group to noTransform group
	noTransform_grp = cmds.group(fk_sys_data['fk_remoteCtrl_grp'], wire_grp, cluster_grp, follicle_grp, surface_grp, joint_grp, deformer_grp, n=name + "_NoTransform_Grp")
	transform_grp = cmds.group(global_ctrl_data[1], n=name + "_Transform_Grp")
	cmds.group(noTransform_grp, transform_grp, n=name + "_Bd_Ribbon_Rig_Grp")
	cmds.parent(surface, transform_grp)
	cmds.select(cl=1)


def createFKSys(ctrl_amount, curve, name, color1=(0,1,0), color2=(0.5,0.5,0.5)):
	# Declaring all function variables in dictionary
	fk_data = {
		'jnt_ctrl_list':[], 'jnt_ctrl_grp_list':[], 
		'fk_ctrl_list':[], 'fk_ctrl_grp_list':[], 
		'jnt_remoteCtrl_list':[], 'jnt_remoteCtrl_grp_list':[], 
		'fk_remoteCtrl_list':[], 'fk_remoteCtrl_grp_list':[], 
		'fk_ctrl_grp':"", 'fk_remoteCtrl_grp':"", 
		'joint_list':[], 'joint_group': "", 
		'curve':"", 'wire':"", 'base_wire':""
		}
	
	# Duplicate main curve
	fk_data['curve'] = cmds.duplicate(curve, name="{}_MainCtrl_FKDriver_Crv".format(name))[0]
	# Rebuild curve - Same as control amount - 1 linear - Convert curve to 3 cubic
	cmds.rebuildCurve(fk_data['curve'], rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=1, s=ctrl_amount, d=1, tol=0.01)
	cmds.rebuildCurve(fk_data['curve'], rpo=1, rt=0, end=1, kr=0, kcp=1, kep=1, kt=1, s=4, d=3, tol=0.01)
	cmds.reverseCurve(fk_data['curve'], ch=0, rpo=1)
	# Freeze curve transforms, Delete history, center pivot
	cmds.makeIdentity(fk_data['curve'], apply=True, t=1, r=1, s=1, n=0)
	cmds.xform(fk_data['curve'], cp=1)

	# Do joints on curve CV's
	fk_data['joint_list'] = jointsOnCVs(fk_data['curve'], name)
	
	# Do controls on joints
	jnt_ctrl_data = placeOnEach_joint(fk_data['joint_list'], type="cube", scale=1, color=color1, name=name, sufix="_Jnt_Ctrl")
	fk_data['jnt_ctrl_list'] = jnt_ctrl_data[0]
	fk_data['jnt_ctrl_grp_list'] = jnt_ctrl_data[1]
	# jnt_ctrls remote - Parent ON
	jnt_remoteCtrl_data = placeOnEach_joint(fk_data['joint_list'], type="cube", scale=1, color=color1, constraint=1, name=name, sufix="_Jnt_Remote_Ctrl")
	fk_data['jnt_remoteCtrl_list'] = jnt_remoteCtrl_data[0]
	fk_data['jnt_remoteCtrl_grp_list'] = jnt_remoteCtrl_data[1]

	# Do FK controls on controls
	fk_ctrl_data = placeOnEachSel(fk_data['jnt_ctrl_list'], type="circle", scale=2, color=color2,spaced=1, name=name, sufix="_FK_Ctrl")
	fk_data['fk_ctrl_list'] = fk_ctrl_data[0]
	fk_data['fk_ctrl_grp_list'] = fk_ctrl_data[1]
	# FK controls remote
	fk_remoteCtrl_data = placeOnEachSel(fk_data['jnt_ctrl_list'], type="circle", scale=2, spaced=1, name=name, sufix="_FK_Remote_Ctrl")
	fk_data['fk_remoteCtrl_list'] = fk_remoteCtrl_data[0]
	fk_data['fk_remoteCtrl_grp_list'] = fk_remoteCtrl_data[1]

	fk_data['fk_ctrl_grp'] = fk_data['fk_ctrl_grp_list'][-1]
	fk_data['fk_remoteCtrl_grp'] = fk_data['fk_remoteCtrl_grp_list'][-1]

	# Parent joint ctrls to FK controls
	for grp, ctrl in zip(fk_data['jnt_ctrl_grp_list'], fk_data['fk_ctrl_list']): cmds.parent(grp, ctrl)
	for grp, ctrl in zip(fk_data['jnt_remoteCtrl_grp_list'], fk_data['fk_remoteCtrl_list']): cmds.parent(grp, ctrl)
	# Parent FK controls in order
	parent_FkOrder(fk_data['fk_ctrl_list'], fk_data['fk_ctrl_grp_list'])
	parent_FkOrder(fk_data['fk_remoteCtrl_list'], fk_data['fk_remoteCtrl_grp_list'])

	# Connect controls and remote controls
	for ctrl, remote in zip(fk_data['jnt_ctrl_list'], fk_data['jnt_remoteCtrl_list']): connectTransform(ctrl, remote, t=1, ro=1, s=1)
	for ctrl, remote in zip(fk_data['fk_ctrl_list'], fk_data['fk_remoteCtrl_list']): connectTransform(ctrl, remote, t=1, ro=1, s=1)

	# Wire highRes curve to lowRes
	fk_data['wire'] = cmds.wire(curve, gw=False, en=1.0, ce=0.0, li=0.0, dds=(0, 100), w=fk_data['curve'], n="{}_FkSys_Wire_Def".format(name))[0]
	fk_data['base_wire'] = fk_data['curve'] + "BaseWire"
	# Bind joints to curve
	cmds.skinCluster(fk_data['joint_list'], fk_data['curve'])

	fk_data['joint_group'] = cmds.group(fk_data['joint_list'], n="{}_FK_Jnt_Grp".format(name))

	return fk_data

#########################################################################
# FK SYSTEM UTILITIES ---

# Joints on CVs - Select curve, run scrip
def jointsOnCVs(path_crv, name=""):
    cmds.select(cl=1)
    cv_list = cmds.getAttr(path_crv + '.cv[:]')
    joint_list = []
    
    for i, cv in enumerate(cv_list):
        joint = cmds.joint(n="{}_{}_FKSys_Jnt".format(name, i))
        cmds.xform(joint, t=cv)
        cmds.select(cl=1)
        
        joint_list.append(joint)
        
    return joint_list

# Control on each Joint selection
def placeOnEach_joint(joint_list, type="circle", scale=1, color=(1,1,1), constraint=0, name="", sufix="_Ctrl"):
	ctrl_list = []
	ctrl_grp_list = []

	for n, i in enumerate(joint_list):
		position = cmds.xform(i, q=1, t=1, ws=1)
		rotation = cmds.joint(i, q=1, o=1)

		new_ctrl = bd_buildCtrl(ctrl_type=type, name="{}_{}".format(name, n), sufix=sufix, scale=scale, spaced=1, offset=0)
		ctrl_list.append(new_ctrl[0])
		ctrl_grp_list.append(new_ctrl[1])

		setCtrlColor(new_ctrl[0], color=color)
		cmds.xform(new_ctrl[1], t=position, ro=rotation)
		
		if constraint == 1: cmds.parentConstraint(new_ctrl[0], i, mo=1)

	return ctrl_list, ctrl_grp_list

# Control on each selection
def placeOnEachSel(sel_list, type="circle", scale=1, color=(1,1,1), spaced=1, name="", sufix="_Ctrl"):
	ctrl_list = []
	ctrl_grp_list = []
	
	for n, i in enumerate(sel_list):
		position = cmds.xform(i, q=1, t=1, ws=1)
		rotation = cmds.xform(i, q=1, ro=1, ws=1)
		
		new_ctrl = bd_buildCtrl(ctrl_type=type, name="{}_{}".format(name, n), sufix=sufix, scale=scale, spaced=1, offset=0)
		ctrl_list.append(new_ctrl[0])
		ctrl_grp_list.append(new_ctrl[1])
		
		setCtrlColor(new_ctrl[0], color=color)
		cmds.xform(new_ctrl[1], t=position, ro=rotation) if spaced == 1 else cmds.xform(new_ctrl[0], t=position, ro=rotation)

	return ctrl_list, ctrl_grp_list

# Parents in FK Order - Select Ctrl Grps, Last to First
def parent_FkOrder(controls=[], groups=[]):
	for y, z in enumerate(groups):
		cmds.parent(z, controls[y+1])
		if y+1 >= len(groups)-1: break


def createFlcBindSys(surface, ctrl_amount, ctrl_color, global_ctrl, name):
	# Define crv step
	crvStep = 100 / (ctrl_amount-1) / 100
	surface_shape = cmds.listRelatives(surface[0], type="shape")
	
	follicle_list = []
	joint_list = []
	ctrl_grp_list = []
	ctrl_list = []

	for i in range(int(ctrl_amount)):
		parameter = i * crvStep
		# Create follicle
		follicle_data = createFollicle(inputSurface=surface_shape, name="{}_{}_Bind_Jnt_Ctrl_Flc".format(name, i),hide=0)
		follicle_translate = cmds.xform(follicle_data[0], q=1, t=1, ws=1)
		follicle_rotate = cmds.xform(follicle_data[0], q=1, ro=1, ws=1)

		# Create control
		bindJnt_ctrl_data = bd_buildCtrl(ctrl_type="circle", name="{}_{}_Bind_Jnt".format(name, i), sufix="_Ctrl", scale=0.5)
		setCtrlColor(bindJnt_ctrl_data[0], color=ctrl_color)
		# Parent ctrl grp to follicle
		cmds.xform(bindJnt_ctrl_data[1], t=follicle_translate, ro=follicle_rotate)
		cmds.parent(bindJnt_ctrl_data[1], follicle_data[0])
		# Set parameter U
		cmds.setAttr(follicle_data[1] + ".parameterU", parameter)

		# Create joint
		cmds.select(cl=1)
		bind_jnt = cmds.joint(n="{}_{}_Bind_Jnt".format(name, i), rad=0.3)
		# Parent constrain to ctrl - No offset
		parentConst_node = cmds.parentConstraint(bindJnt_ctrl_data[0], bind_jnt, mo=0)
		scaleConst_node = cmds.scaleConstraint(bindJnt_ctrl_data[0], bind_jnt)
		scaleConst_flc_node = cmds.scaleConstraint(global_ctrl, follicle_data[0])

		# Append follicle
		follicle_list.append(follicle_data[0])
		# Append joint
		joint_list.append(bind_jnt)
		# Append ctrl
		ctrl_list.append(bindJnt_ctrl_data[0])
		ctrl_grp_list.append(bindJnt_ctrl_data[1])
	
	# Group follicles
	follicle_grp = cmds.group(follicle_list, n="{}_Bind_Jnt_Flc_Grp".format(name))
	# Group joints
	joint_grp = cmds.group(joint_list, n="{}_Bind_Jnt_Grp".format(name))

	# Return [0]Follicle Grp, [1]Follicle List, [2]Jnt Grp, [3]Joint List, [4]Ctrl List, [5]Ctrl Grp List
	return follicle_grp, follicle_list, joint_grp, joint_list, ctrl_list, ctrl_grp_list


def createBaseCtrl(crv, surface, name, color1, color2):
	# Wire surface to curve
	wire = cmds.wire(surface, gw=False, en=1.0, ce=0.0, li=0.0, dds=(0, 100), w=crv, n=name + "_wire")[0]
	cmds.setAttr(wire + ".rotation", 0)

	# Create clusters from all cv's on curve and relative dynamic systems
	cluster_start = cmds.cluster(crv[0] + '.cv[:]', n=name + '_Start_Crv_Clst', envelope=1)
	cmds.select(crv[0], r=1)
	dynSys_start_data = tp_createDynamicClst()

	cluster_end = cmds.cluster(crv[0] + '.cv[:]', n=name + '_End_Crv_Clst', envelope=1)
	cmds.select(crv[0], r=1)
	dynSys_end_data = tp_createDynamicClst()
	
	# Adjust dynamic system ramp for start and end controls
	adjustRamp(dynSys_start_data[0], inPos=0, outPos=1, createMid=0, inColor=1, outColor=0)
	adjustRamp(dynSys_end_data[0], inPos=0, outPos=1, createMid=0, inColor=0, outColor=1)

	# Create controls - get resulting return data
	ctrl_start_data = bd_buildCtrl(ctrl_type="cube", scale=2, name=name + '_Start')
	setCtrlColor(ctrl_start_data[0], color=color1)
	ctrl_end_data = bd_buildCtrl(ctrl_type="cube", scale=2, name=name + '_End')
	setCtrlColor(ctrl_end_data[0], color=color2)

	# Get start and end point on curve positions
	# Position ctrl groups at start and end
	start_position = cmds.pointOnCurve(crv, pr=0, p=1)
	end_position = cmds.pointOnCurve(crv, pr=1, p=1)

	cmds.xform(ctrl_start_data[1], t=start_position)
	cmds.xform(ctrl_end_data[1], t=end_position)

	# Connect controls to clusters
	# Leaving X rotation out - Will be controlled by wire dropoff locators
	cmds.connectAttr(ctrl_start_data[0] + '.translate', cluster_start[1] + '.translate')
	cmds.connectAttr(ctrl_start_data[0] + '.rotate.rotateY', cluster_start[1] + '.rotate.rotateY')
	cmds.connectAttr(ctrl_start_data[0] + '.rotate.rotateZ', cluster_start[1] + '.rotate.rotateZ')

	cmds.connectAttr(ctrl_end_data[0] + '.translate', cluster_end[1] + '.translate')
	cmds.connectAttr(ctrl_end_data[0] + '.rotate.rotateY', cluster_end[1] + '.rotate.rotateY')
	cmds.connectAttr(ctrl_end_data[0] + '.rotate.rotateZ', cluster_end[1] + '.rotate.rotateZ')

	# Add interpolation control attribute to start/end control
	cmds.addAttr(ctrl_start_data[0], ln="customAttr", nn="________", at="enum", en="Custom:", keyable=True)
	cmds.setAttr(ctrl_start_data[0] + ".customAttr", lock=1)
	cmds.addAttr(ctrl_start_data[0], ln="interpolation", nn="Interpolation", at="long", min=1, max=6, dv=1, keyable=True)
	cmds.connectAttr(ctrl_start_data[0] + ".interpolation", dynSys_start_data[0] + ".interpolation")

	cmds.addAttr(ctrl_end_data[0], ln="customAttr", nn="________", at="enum", en="Custom:", keyable=True)
	cmds.setAttr(ctrl_end_data[0] + ".customAttr", lock=1)
	cmds.addAttr(ctrl_end_data[0], ln="interpolation", nn="Interpolation", at="long", min=1, max=6, dv=1, keyable=True)
	cmds.connectAttr(ctrl_end_data[0] + ".interpolation", dynSys_end_data[0] + ".interpolation")

	# Ends rotation control
		# Create dropoff locators - start end
		# Connect to controls rotation 
	cmds.select("{}.u[{}]".format(crv[0], 0), r=True)
	dropoffLoc_start = cmds.dropoffLocator(1.0, 1.0, wire)[0]
	cmds.connectAttr(ctrl_start_data[0] + ".rx", "{}.wireLocatorTwist[{}]".format(wire, 0))
	
	cmds.select("{}.u[{}]".format(crv[0], 1), r=True)
	dropoffLoc_end = cmds.dropoffLocator(1.0, 1.0, wire)[0]
	cmds.connectAttr(ctrl_end_data[0] + ".rx", "{}.wireLocatorTwist[{}]".format(wire, 1))

	# return [0] ctrl 1 transform, [1] ctrl 1 grp, [2] ctrl 2 transform, [3] ctrl 2 grps, [4] cluster 1, [5] cluster 2
	return ctrl_start_data[0], ctrl_start_data[1], ctrl_end_data[0], ctrl_end_data[1], cluster_start, cluster_end


def createCtrlSys(crv, rootCrv, surface, rootSurface, name, parameter=0.5, iteration=1):
	# Get surface shape
	crv_shape = cmds.listRelatives(crv[0], type="shape")[0]
	rootCrv_shape = cmds.listRelatives(rootCrv[0], type="shape")[0]

	surface_shape = cmds.listRelatives(surface[0], type="shape")
	rootSurface_shape = cmds.listRelatives(rootSurface[0], type="shape")

	# create wire, cluster
	wire = cmds.wire(surface, gw=False, en=1.0, ce=0.0, li=0.0, dds=(0, 1000), w=crv, n=name + "_wire")[0]
	newCluster = cmds.cluster(rootCrv[0] + '.cv[:]', n="{}_{}_FreeSys_Crv_Clst".format(name, iteration), envelope=1)
	# run dynamicClst script
	cmds.select(rootCrv[0], r=1)
	dynamicSys_data = tp_createDynamicClst()
	cmds.select(cl=1)

	# Get arc length
	rootCrv_arcLength = cmds.arclen(rootCrv)

	# Create control
	ctrl_data = bd_buildCtrl(ctrl_type="sphere", name="{}_{}".format(name, iteration), sufix="_FreeSys_Ctrl", offset=1)
	# Create follicle on surface
	follicle_data = createFollicle(inputSurface=rootSurface_shape, name=name + '_FreeSys_Ctrl_Flc',hide=0)
	# Point constraint ctrl grp
	cmds.pointConstraint(follicle_data[0], ctrl_data[1], offset=(0,0,0), weight=1)
	# Orient constroint ctrl
	cmds.orientConstraint(follicle_data[0], ctrl_data[0], mo=1, weight=1)
	# Create attributes on control - Division, Parameter, Twist, Interpotaion
	cmds.addAttr(ctrl_data[0], ln="customAttr", nn="________", at="enum", en="Custom:", keyable=True)
	cmds.setAttr(ctrl_data[0] + ".customAttr", lock=1)
	cmds.addAttr(ctrl_data[0], ln="parameter", nn="Parameter", at="double", min=0, max=rootCrv_arcLength, dv=(rootCrv_arcLength/2), keyable=True)
	cmds.addAttr(ctrl_data[0], ln="twist", nn="Twist", at="double", min=-1000, max=1000, dv=0, keyable=True)
	cmds.addAttr(ctrl_data[0], ln="interpolation", nn="Interpolation", at="long", min=1, max=6, dv=4, keyable=True)
	cmds.connectAttr(ctrl_data[0] + ".interpolation", dynamicSys_data[0] + ".interpolation")

	# Create setRange for translate conversion 0 1
	ctrl_setRange = cmds.shadingNode('setRange', au=1, n=name + '_ctrl_t_setRange')
	cmds.setAttr(ctrl_setRange + '.max.maxX', 1)
	cmds.setAttr(ctrl_setRange + '.oldMax.oldMaxX', rootCrv_arcLength)
	cmds.connectAttr(ctrl_data[0] + '.parameter', ctrl_setRange + '.value.valueX')

	# Connect ctrl translate x to follicle uVlue
	cmds.connectAttr(ctrl_setRange + '.outValue.outValueX', follicle_data[1] + '.parameterU')

	# Create set range for scale X, output max 0-1, control ramp falloff
	scale_setRange = cmds.shadingNode('setRange', au=1, n=name + '_ctrl_scaleToFalloff_setRange')
	cmds.setAttr(scale_setRange + '.oldMin.oldMinX', 0.2)
	cmds.setAttr(scale_setRange + '.oldMax.oldMaxX', 5)
	cmds.setAttr(scale_setRange + '.min.minX', 0.1)
	cmds.setAttr(scale_setRange + '.max.maxX', 1)

	cmds.connectAttr(ctrl_data[0] + '.scale.scaleX', scale_setRange + '.value.valueX')
	
	# Calcaulating start and end position
	colorStart_mpDiv = cmds.shadingNode('multiplyDivide', au=1, n=name + '_scaleInvert_mpDivide')
	colorStartEnd_plusMA = cmds.shadingNode('plusMinusAverage', au=1, n=name + '_falloffResult_plusMA')

	# Invert Scale newRange value
	cmds.setAttr(colorStart_mpDiv + '.input2.input2X', -1)
	cmds.connectAttr(scale_setRange + '.outValue.outValueX', colorStart_mpDiv + '.input1.input1X')

	# Connect to plusMinusAvarege node
	cmds.connectAttr(colorStart_mpDiv + '.output.outputX', colorStartEnd_plusMA + '.input2D[0].input2Dx')
	cmds.connectAttr(scale_setRange + '.outValue.outValueX', colorStartEnd_plusMA + '.input2D[0].input2Dy')

	cmds.connectAttr(ctrl_setRange + '.outValue.outValueX', colorStartEnd_plusMA + '.input2D[1].input2Dx')
	cmds.connectAttr(ctrl_setRange + '.outValue.outValueX', colorStartEnd_plusMA + '.input2D[1].input2Dy')
	
	# Create clamp setRange - Limiting calculation to 0 to 1
	clamp_setRenge = cmds.shadingNode('setRange', au=1, n=name + '_resultClamp_setRange')
	cmds.setAttr(clamp_setRenge + '.oldMax.oldMaxX', 1)
	cmds.setAttr(clamp_setRenge + '.max.maxX', 1)
	cmds.setAttr(clamp_setRenge + '.oldMax.oldMaxY', 1)
	cmds.setAttr(clamp_setRenge + '.max.maxY', 1)
	cmds.connectAttr(colorStartEnd_plusMA + '.output2D.output2Dx', clamp_setRenge + '.value.valueX')
	cmds.connectAttr(colorStartEnd_plusMA + '.output2D.output2Dy', clamp_setRenge + '.value.valueY')

	# Connect to ramp colors
	# Connect and configure color 1 mid
	cmds.connectAttr(ctrl_setRange + '.outValue.outValueX', dynamicSys_data[0] + '.colorEntryList[0].position')
	cmds.setAttr(dynamicSys_data[0] + '.colorEntryList[0].color', 1, 1, 1, type="double3")

	# Connect and configure color 0 start
	cmds.connectAttr(clamp_setRenge + '.outValue.outValueX', dynamicSys_data[0] + '.colorEntryList[2].position')
	cmds.setAttr(dynamicSys_data[0] + '.colorEntryList[2].color', 0, 0, 0, type="double3")

	# Connect and configure color 2 end
	cmds.connectAttr(clamp_setRenge + '.outValue.outValueY', dynamicSys_data[0] + '.colorEntryList[1].position')
	cmds.setAttr(dynamicSys_data[0] + '.colorEntryList[1].color', 0, 0, 0, type="double3")

	# Connect ctrl to cluster
	cmds.connectAttr(ctrl_data[0] + '.translate', newCluster[1] + '.translate')

	# Create and connect dropoff locators
	cmds.select("{}.u[{}]".format(crv[0], 0), r=True)
	dropoffLoc1 = cmds.dropoffLocator(1.0, 1.0, wire)[0]

	cmds.select("{}.u[{}]".format(crv[0], 0.1), r=True)
	dropoffLoc2 = cmds.dropoffLocator(1.0, 1.0, wire)[0]
	
	cmds.select("{}.u[{}]".format(crv[0], 0.2), r=True)
	dropoffLoc3 = cmds.dropoffLocator(1.0, 1.0, wire)[0]
	cmds.select(cl=1)
	
	cmds.connectAttr(ctrl_data[0] + ".twist", "{}.wireLocatorTwist[{}]".format(wire, 1))
	cmds.connectAttr(ctrl_setRange + '.outValue.outValueX', dropoffLoc2 + '.param')
	cmds.connectAttr(clamp_setRenge + '.outValue.outValueX', dropoffLoc1 + '.param')
	cmds.connectAttr(clamp_setRenge + '.outValue.outValueY', dropoffLoc3 + '.param')
	lock_hide([ctrl_data[0]], [".rx", ".ry", ".rz"])

	# Set control parameter of choice
	ctrl_tergetPosition = rootCrv_arcLength * parameter
	cmds.setAttr(ctrl_data[0] + '.parameter', ctrl_tergetPosition)

	# Group everything or pass creations to master grouper
	return newCluster[1], ctrl_data[1], follicle_data[0], ctrl_data[0]


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


def bd_buildCtrl(ctrl_type="circle", name="", sufix="_Ctrl", scale=1, spaced=1, offset=0):
	# ctrl_type - Cube, Sphere, Circle (add - square, pointer, arrow, spherev2)
	pack = []

	if ctrl_type == "cube":
		cube_coord = [
			(-1.0, 1.0, 1.0), (-1.0, 1.0, -1.0), (1.0, 1.0, -1.0),
			(1.0, 1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, -1.0, 1.0),
			(1.0, -1.0, 1.0), (1.0, -1.0, -1.0), (-1.0, -1.0, -1.0),
			(-1.0, -1.0, 1.0), (-1.0, -1.0, -1.0), (-1.0, 1.0, -1.0),
			(1.0, 1.0, -1.0), (1.0, -1.0, -1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0)]

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

	elif ctrl_type == "circle":
		c1 = cmds.circle(n=name + sufix, nr=(1, 0, 0), r=scale, ch=0)[0]
		pack.append(c1)

	shapes = cmds.listRelatives(c1, f = True, s=True)
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
	

def adjustRamp(rampNode, inPos, outPos, createMid=0, inColor=1, outColor=1):
	# set color entry list 1 position
	cmds.setAttr(rampNode + '.colorEntryList[0].color', inColor, inColor, inColor, type="double3")
	cmds.setAttr(rampNode + '.colorEntryList[0].position', inPos)
	# set color entry list 2 position
	cmds.setAttr(rampNode + '.colorEntryList[1].color', outColor, outColor, outColor, type="double3")
	cmds.setAttr(rampNode + '.colorEntryList[1].position', outPos)

	if createMid == 1:
		# calculate mid point
		midPos = (inPos + outPos) / 2.0
		# create extra point in ramp
		cmds.setAttr(rampNode + '.colorEntryList[2].color', 1, 1, 1, type="double3")
		cmds.setAttr(rampNode + '.colorEntryList[2].position', midPos)

def connectTransform(object1, object2, t=1, ro=0, s=0):
	# connect translation
	if t == 1:
		cmds.connectAttr(object1 + '.translate', object2 + '.translate', f=1)
	# connect rotation
	if ro == 1:
		cmds.connectAttr(object1 + '.rotate', object2 + '.rotate', f=1)
	# connect scale
	if s == 1:
		cmds.connectAttr(object1 + '.scale', object2 + '.scale', f=1)

def tp_createDynamicClst(interpolation='linear'):
	# Get curve information - start
	# Get shape curve shape node name
	getSel = cmds.ls(sl=1)
	shapeName = cmds.listRelatives(getSel, s=1)[0]
	clsName = cmds.listConnections(shapeName, type='cluster')

	# Get degrees and spans to calculte CV's
	curveDeg = cmds.getAttr(shapeName + ".degree")
	curveSpa = cmds.getAttr(shapeName + ".spans")
	# CV's = degrees + spans
	cvCount = curveDeg + curveSpa

	# Creates and connects ramp node
	rampNode = cmds.shadingNode('ramp', asTexture=1, n=(getSel[0] + "_" + clsName[0] + "_ramp"))
	placed2dTx = cmds.shadingNode('place2dTexture', asUtility=1)

	cmds.connectAttr(placed2dTx + ".outUV", rampNode + ".uvCoord", f=1)
	cmds.connectAttr(placed2dTx + ".outUvFilterSize", rampNode + ".uvFilterSize", f=1)

	# Creates connection lists for expression printing
	connectList = []
	for i in range(cvCount):
		connectList.append(str(clsName[0]) + ".weightList[0].weights[" + str(i) + "] = $cvValue[" + str(i) + "];\n")

	# Stores code in string for expression printing
	newExpr = "vector $exprTrigger = " + str(rampNode) + ".outAlpha; \n\
				float $cvValue[]; \n\
				// cvCount is dynamic from curve \n\
				float $cvCount = " + str(cvCount - 1) + "; \n \n\
				for ($y=0; $y<=$cvCount; $y++){ \n\
					float $j = $y; \n\
					float $pos = ($j/$cvCount); \n\
					float $value[] = `colorAtPoint -o A -u 0.5 -v $pos " + str(rampNode) + "`; \n\
					$cvValue[$y] = $value[0]; \n\
				} \n \n"

	# Creates expression
	finalExp = newExpr + ''.join(connectList)
	expNode = cmds.expression(s=finalExp, o="", n=(getSel[0] + "_" + clsName[0] + "_expr"), ae=0, uc='all')

	return rampNode, placed2dTx, expNode

# Set control color function
def setCtrlColor(ctrl, color = (1,1,1)):    
	rgb = ("R","G","B")
	cmds.setAttr(ctrl + ".overrideEnabled", 1)
	cmds.setAttr(ctrl + ".overrideRGBColors", 1)

	for channel, color in zip(rgb, color):
		cmds.setAttr("{}.overrideColor{}".format(ctrl, channel), color)


def createSineSys(base_surface, control, name):
	surface = cmds.duplicate(base_surface, n=name + '_sineDef_Srf')[0]
	guide_srf = cmds.duplicate(base_surface, n=name + '_sineGuide_Srf')[0]
	cmds.delete(surface, ch=1)
	surface_shape = cmds.listRelatives(guide_srf, type="shape")[0]

	# Add translation and rotation
	sineDef_data = nonlinearDeformer(objects=[surface], defType='sine', rotate=(0,0,90), name=name)

	# Create follicle on 0 parameter
	follicle_data = createFollicle(inputSurface=[surface_shape], uVal=0, name=name + '_Ctrl_Flc', hide=0)
	# Parent deformer position to follicle - point constraint
	cmds.pointConstraint(follicle_data[0], sineDef_data[1], mo=0)

	# GLOBAL_CTRL SINE DEFORMER ATTRIBUTES AND CONNECT SECTION ---
	# Add attributes to global control
	# Set attributes to desired initial position
	cmds.addAttr(control, ln="sineCtrl", nn="________", at="enum", en="SINE", keyable=True)
	cmds.setAttr(control + ".sineCtrl", lock=1)
	cmds.addAttr(control, ln="amplitude", nn="Amplitude", at="double", min=-4, max=5, dv=0, keyable=True)
	cmds.addAttr(control, ln="wavelength", nn="Wavelength", at="double", min=0.1, max=10, dv=1, keyable=True)
	cmds.addAttr(control, ln="offset", nn="Offset", at="double", min=-10, max=10, dv=0, keyable=True)
	cmds.addAttr(control, ln="dropoff", nn="Dropoff", at="double", min=-1, max=1, dv=0, keyable=True)
	cmds.addAttr(control, ln="lowBound", nn="Low_Bound", at="double", min=-9, max=0, dv=-1, keyable=True)
	cmds.addAttr(control, ln="highBound", nn="High_Bound", at="double", min=0, max=10, dv=1, keyable=True)
	# Translation and rotation extra attributes for sine
	cmds.addAttr(control, ln="parameter", nn="Parameter", at="double", min=0, max=1, dv=0, keyable=True)
	cmds.addAttr(control, ln="rotation", nn="Rotation", at="double", min=0, max=360, dv=0, keyable=True)

	# Connect custom attributes to sine deformer
	cmds.connectAttr(control + '.amplitude', sineDef_data[0] + '.amplitude')
	cmds.connectAttr(control + '.wavelength', sineDef_data[0] + '.wavelength')
	cmds.connectAttr(control + '.offset', sineDef_data[0] + '.offset')
	cmds.connectAttr(control + '.dropoff', sineDef_data[0] + '.dropoff')
	cmds.connectAttr(control + '.lowBound', sineDef_data[0] + '.lowBound')
	cmds.connectAttr(control + '.highBound', sineDef_data[0] + '.highBound')
	# connect parameter to follicle uValue
	cmds.connectAttr(control + '.parameter', follicle_data[1] + '.parameterU')
	cmds.connectAttr(control + '.rotation', sineDef_data[1] + '.rotate.rotateY')

	# 0 Deformer Shape, 1 Deformer Handle, 2 System Surface, 3 Guide Surface, 4 Follicle Transform
	return sineDef_data[0], sineDef_data[1], surface, guide_srf, follicle_data[0]


# GENERAL FUNCTION: CREATE A NONLINEAR DEFORMER
def nonlinearDeformer(objects=[], defType=None, lowBound=-1, highBound=1, translate=None, rotate=None, name='nonLinear'):
	# If something went wrong or the type is not valid, raise exception
	if not objects or defType not in ['bend','flare','sine','squash','twist','wave']:
		raise Exception, "function: 'nonlinearDeformer' - Make sure you specified a mesh and a valid deformer"

	# Create and rename the deformer
	nonLinDef = cmds.nonLinear(objects[0], type=defType, lowBound=lowBound, highBound=highBound)
	nonLinDef[0] = cmds.rename(nonLinDef[0], (name + '_' + defType + '_def'))
	nonLinDef[1] = cmds.rename(nonLinDef[1], (name + '_' + defType + 'Handle'))

	# If translate was specified, set the translate
	if translate:
		cmds.setAttr((nonLinDef[1] + '.translate'), translate[0], translate[1], translate[2])
	# If rotate was specified, set the rotate
	if rotate:
		cmds.setAttr((nonLinDef[1] + '.rotate'), rotate[0], rotate[1], rotate[2])

	# Return the deformer
	return nonLinDef

def lock_hide(objs, attrs):
	for obj in objs:
		for attr in attrs:
			cmds.setAttr(obj + attr, l=True, k=False, cb=False)