import maya.cmds as mc
import tpRigTemplate as tpt
import tpRig as Rig
import tpUtils as tpu
import tpUnit as unt

"""
Neck module plan
    fix mouth bag - DONE
    develop neck module
    develop head module
    develop RigBuild Class
    
Order of action
    rig class level
        tag created
            tag data added
        environment created
            env data added
            all data attr created
        tag - environment connection    
    
    get necessary data
    create joint sets (duplicate from template)
        output sys
        driver sys
    create offset group for driver sys
    create surface from curve from jnt positions
        create follicle on surface
        create control to attach on follicle 
            study how to expand for adjustments
        connect mid control to all joints
        bind surface to output joints
    parent output joints
    create Atlas control
    create c7 control
    connect all joints to module
    
    
Classes
    joint
    handle
    module 
"""


class NeckModule:
    """
    function breakdown:
        inherit from tpModule
        initiated by environment class
        query data from template
        create module tag
        create module group
        create joints - connect to module
        create ribbon
            draw curve from joint positions
            duplicate - loft
            bind to neck joints
            add follicle
        create controls - connect to module
            add control to follicle - ctrls c6 to c1
            add c7 control
            add c1/atlas control
    """
    def __init__(self, pointers, scale):
        # execute function
        self.module_data = build_neck_module(pointers, scale)

        # attributes
        self.module_name = ''
        self.parts_list = []
        self.bind_joint_list = []
        self.util_joint_list = []

        # unpack
        self.joint_id_list = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7']

        # load neck module data
        self.template = tpt.RigTemplate()
        self.tmp_neck_mod = self.template.load_sys_by_id('neck')
        self.mod_members = self.template.sys_members_id()

        # initialize rig class
        self.rig = Rig.Rig()
        self.module = self.rig.create_module('neck')

        self.members_data = {}
        self.members_relation = {}

    def module_name(self):
        pass

    def parts_list(self):
        pass

    def bind_joint_list(self):
        pass

    def util_joint_list(self):
        pass

    def build(self):
        pass

    def create_rig_joint(self):
        pass

    def create_rig_module(self):
        pass


def build_neck_module(pointer_list, scale=1):
    """
    Provided neck vertebras pointers in order C1 to C7
    creates neck system
    :param pointer_list:
    :param scale:
    :return sys_data:
    """
    module_name = 'neck'
    names_list = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7']
    points_position_list = []
    bind_joint_list = []
    sys_data = {}

    # JOINTS SETUP SECTION ________________________________________________________________________

    # create joint sets and offset groups
    for name, pointer in zip(names_list, pointer_list):
        # creating dict item for each name
        sys_data[name] = {}
        # get the pointer position into list
        position = mc.xform(pointer, q=True, t=True, ws=True)
        points_position_list.append(position)

        # create bind joint for each pointer
        mc.select(cl=1)
        bind_joint = mc.joint(name='{}_bind_jnt'.format(name), radius=scale)
        mc.xform(bind_joint, t=position, ws=True)
        sys_data[name].update({'bind': bind_joint})
        bind_joint_list.append(bind_joint)

        # create driver joint for each pointer
        mc.select(cl=1)
        driver_joint = mc.joint(name='{}_driver_jnt'.format(name), radius=scale)
        # Create offset groups for driver joints
        driver_offset_grp = mc.group(driver_joint, name='{}_offset_00_grp'.format(driver_joint))
        # if c1 or c7 create extra offset
        if name == names_list[0] or name == names_list[-1]:
            driver_offset_01_grp = mc.group(driver_joint, name='{}_offset_01_grp'.format(driver_joint))
            sys_data[name].update({'driver_01_offset': driver_offset_01_grp})

        mc.xform(driver_offset_grp, t=position, ws=True)
        sys_data[name].update({'driver': driver_joint,
                               'driver_00_offset': driver_offset_grp})

        mc.parentConstraint(driver_joint, bind_joint, mo=True)

    # parent driver joints in FK order
    for index, item in enumerate(names_list):
        # if last item - exit loop
        if item == names_list[-1]:
            break
        # get parent and child in data dict
        parent = sys_data[names_list[index + 1]]['driver']
        self = sys_data[item]['driver_00_offset']
        # parent self offset group to parent driver joint
        mc.parent(self, parent)

    # parent bind joints in fk order
    tpu.parent_in_order(bind_joint_list, reverse=True)

    # SURFACE SETUP SECTION ________________________________________________________________________

    # draw curve from pointers
    loft_base_crv = mc.curve(point=points_position_list, degree=3, ws=True, name='neck_mod_loft_base_crv')
    mc.rebuildCurve(loft_base_crv, ch=False, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=6, d=3, tol=0.01)
    # del history
    mc.delete(loft_base_crv, ch=True)

    # duplicate curve
    loft_start_crv = mc.duplicate(loft_base_crv, name='loft_01_crv')
    loft_end_crv = mc.duplicate(loft_base_crv, name='loft_02_crv')
    # offset curves position
    mc.xform(loft_start_crv, t=(scale, 0, 0), ws=True)
    mc.xform(loft_end_crv, t=(scale*-1, 0, 0), ws=True)
    # loft curves
    loft_surface = mc.loft(loft_start_crv, loft_end_crv, ch=False,
                           u=0, c=0, ar=1, d=3, ss=1, rn=0, po=0, rsn=True,
                           name='{}_01_srf'.format(module_name))
    surface_shape = mc.listRelatives(loft_surface, s=True)
    # delete guide curves
    mc.delete(loft_base_crv, loft_start_crv, loft_end_crv)

    # bind surface to bind joints
    surface_skin_cluster = mc.skinCluster(bind_joint_list, loft_surface)

    # CONTROLS SETUP SECTION ________________________________________________________________________

    # define controls/follicles uv position
    sys_data['controls'] = {
        'mid': 0.5,
        'c1': 0,
        'c7': 1}

    sys_data['follicles'] = {}

    # create controls on follicles
    for ctrl in sys_data['controls']:
        flc = tpu.create_follicle(surface_shape, u_val=sys_data['controls'][ctrl],
                                  v_val=0.5, name='{}_ctrl_flc'.format(ctrl))
        sys_data['follicles'].update({ctrl: flc})

        control = tpu.build_ctrl(ctrl_type='circle', scale=scale*10, normal=(0, 1, 0), name=ctrl)
        sys_data['controls'][ctrl] = control

        flc_position = mc.xform(flc[0], q=True, t=True, ws=True)
        mc.xform(control[1], t=flc_position, ws=True)
        # constraint controls
        mc.parentConstraint(flc[0], control[1], mo=True)

    # create gear down node for mid control
    divide_node = mc.createNode('multiplyDivide')
    mc.setAttr('{}.operation'.format(divide_node), 2)
    for n in 'XYZ':
        mc.setAttr('{}.input2{}'.format(divide_node, n), 3)
    mc.connectAttr('{}.r'.format(sys_data['controls']['mid'][0]),
                   '{}.input1'.format(divide_node))

    # connect mid control to all offset groups
    offset_grp_list = [sys_data[item]['driver_00_offset'] for item in names_list]

    for item in offset_grp_list:
        # stop on c6, not connecting c7
        if item == offset_grp_list[-1]:
            break
        mc.connectAttr('{}.output'.format(divide_node),
                       '{}.r'.format(item))

    # connect c1 control to start offset group
    mc.connectAttr('{}.r'.format(sys_data['controls']['c1'][0]),
                   '{}.r'.format(sys_data['c1']['driver_01_offset']))
    # connect c7 control to end offset group
    mc.connectAttr('{}.r'.format(sys_data['controls']['c7'][0]),
                   '{}.r'.format(sys_data['c7']['driver_00_offset']))

    # GROUP AND ORGANIZE SECTION ________________________________________________________________________

    joint_grp = mc.group(sys_data['c7']['bind'],
                         sys_data['c7']['driver_00_offset'],
                         name='{}_jnt_grp'.format(module_name))

    surface_grp = mc.group(loft_surface, name='{}_srf_grp'.format(module_name))

    follicle_list = [sys_data['follicles'][flc][0] for flc in sys_data['follicles']]
    follicle_grp = mc.group(follicle_list, name='{}_flc_grp'.format(module_name))

    controls_list = [sys_data['controls'][ctrl][1] for ctrl in sys_data['controls']]
    control_grp = mc.group(controls_list, name='{}_ctrl_grp'.format(module_name))

    module_grp = mc.group(
        joint_grp,
        surface_grp,
        follicle_grp,
        control_grp,
        name='{}_module_grp'.format(module_name))

    # return
    # bind joints
    # rig joints
    # controls
    # surface
    # groups

    return sys_data











