import maya.cmds as mc
import tpRigTemplate as tpt
import tpRig as Rig
import tpUtils as tpu
import tpUnit as unt

"""
Neck module plan
    fix mouth bag - DONE
    develop neck module - 
    develop head module
    develop RigBuild Class
    
    prototype
        eyebrow prototype
        orbicularis oculi prototype
        eye 2.0 prototype
        ear prototype
    
    connect to rig hub
    
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
    def __init__(self, pointer_list, scale):
        self.guide_pointers = pointer_list
        self.module_scale = scale
        # execute function
        self.module_data = {}

        # attributes
        self.module_name = 'neck'
        self.module_group = ''
        self.groups = {}
        self.module_tag = ''
        self.parts_list = []
        self.bind_joint_list = []
        self.driver_joint_list = []
        self.joint_data = {}

        self.controls_data = {}
        self.c1_ctrl_data = {}
        self.mid_ctrl_data = {}
        self.c7_ctrl_data = {}

        # unpack
        self.joint_id_list = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7']

        # load neck module data
        # self.template = tpt.RigTemplate()
        # self.tmp_neck_mod = self.template.load_sys_by_id('neck')
        # self.mod_members = self.template.sys_members_id()

        # initialize rig class
        # self.rig = Rig.Rig()
        # self.module = self.rig.create_module('neck')

        # self.members_data = {}
        # self.members_relation = {}

    def store_pointers(self, pointer_list):
        self.guide_pointers = mc.ls(sl=True)

    def set_scale(self, value):
        self.module_scale = value

    def build(self):
        if self.guide_pointers:
            self.module_data = build_neck_module(self.guide_pointers, self.module_scale)
            self.unpack_data()
        else:
            mc.warning('No pointers have been stored')

    def unpack_data(self):
        data = self.module_data

        self.groups = data['groups']
        self.module_group = data['groups']['module']
        self.joint_data = data['joints']
        self.bind_joint_list = [joint['bind'] for joint in data['joints']]
        self.driver_joint_list = [joint['driver'] for joint in data['joints']]
        self.controls_data = data['controls']
        self.c1_ctrl_data = data['controls']['c1']
        self.mid_ctrl_data = data['controls']['mid']
        self.c7_ctrl_data = data['controls']['c7']
        pass

    def module_name(self):
        pass

    def part_list(self):
        pass

    def bind_joint_list(self):
        pass

    def util_joint_list(self):
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
        dict{joints: c1...c7: bind
                              driver
                              driver_00_offset
                              driver_01_offset
            control: mid, c1, c7: control
                                  control_grp
            follicle: mid, c1, c7: transform
                                   shape
            groups: module
                    joint
                    follicle
                    surface
                    control}
    """
    # declare function variables
    module_name = 'neck'
    names_list = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7']
    points_position_list = []
    bind_joint_list = []
    module_data = {}
    joint_data = {}

    # JOINTS SETUP SECTION ________________________________________________________________________

    # create joint driver/bind joint sets and offset groups
    for name, pointer in zip(names_list, pointer_list):
        # creating dict item for each name
        joint_data[name] = {}
        # get the pointer position into list
        position = mc.xform(pointer, q=True, t=True, ws=True)
        points_position_list.append(position)

        # create bind joint for each pointer
        mc.select(cl=1)
        bind_joint = mc.joint(name='{}_bind_jnt'.format(name), radius=scale)
        mc.xform(bind_joint, t=position, ws=True)
        joint_data[name].update({'bind': bind_joint})
        bind_joint_list.append(bind_joint)

        # create driver joint for each pointer
        mc.select(cl=1)
        driver_joint = mc.joint(name='{}_driver_jnt'.format(name), radius=scale)
        # Create offset groups for driver joints
        driver_offset_grp = mc.group(driver_joint, name='{}_offset_00_grp'.format(driver_joint))

        # if c1 or c7 create extra offset
        if name == names_list[0] or name == names_list[-1]:
            driver_offset_01_grp = mc.group(driver_joint, name='{}_offset_01_grp'.format(driver_joint))
            joint_data[name].update({'driver_01_offset': driver_offset_01_grp})

        mc.xform(driver_offset_grp, t=position, ws=True)
        joint_data[name].update({'driver': driver_joint,
                                  'driver_00_offset': driver_offset_grp})

        mc.parentConstraint(driver_joint, bind_joint, mo=True)

    # parent driver joints in FK order
    for index, item in enumerate(names_list):
        # if last item - exit loop
        if item == names_list[-1]:
            break
        # get parent and child in data dict
        parent = joint_data[names_list[index + 1]]['driver']
        self = joint_data[item]['driver_00_offset']
        # parent self offset group to parent driver joint
        mc.parent(self, parent)

    # parent bind joints in fk order
    tpu.parent_in_order(bind_joint_list, reverse=True)

    # add joint data to module data
    module_data['joints'] = joint_data

    # SURFACE SETUP SECTION ________________________________________________________________________

    # build surface from pointers
    loft_surface = tpu.surface_from_pointers(pointer_list, scale=scale, name=module_name)
    # get surface shape
    surface_shape = mc.listRelatives(loft_surface, s=True)
    # bind surface to bind joints
    mc.skinCluster(bind_joint_list, loft_surface)

    # CONTROLS SETUP SECTION ________________________________________________________________________

    # define controls/follicles uv position
    module_data['controls'] = {}
    module_data['follicles'] = {}

    ctrl_setup_data = {
        'mid': 0.5,
        'c1': 0,
        'c7': 1}

    # create controls on follicles
    for ctrl in ctrl_setup_data:
        flc_data = tpu.create_follicle(surface_shape, u_val=ctrl_setup_data[ctrl],
                                       v_val=0.5, name='{}_ctrl_flc'.format(ctrl))
        module_data['follicles'].update({ctrl: flc_data})

        control_data = tpu.build_ctrl(ctrl_type='circle', scale=scale*10, normal=(0, 1, 0), name=ctrl)
        module_data['controls'][ctrl] = control_data

        flc_position = mc.xform(flc_data['transform'], q=True, t=True, ws=True)
        mc.xform(control_data['group'], t=flc_position, ws=True)
        # constraint controls
        mc.parentConstraint(flc_data['transform'], control_data['group'], mo=True)

    # create gear down node for mid control
    divide_node = mc.createNode('multiplyDivide')
    mc.setAttr('{}.operation'.format(divide_node), 2)

    for n in 'XYZ':
        mc.setAttr('{}.input2{}'.format(divide_node, n), 3)

    mc.connectAttr('{}.r'.format(module_data['controls']['mid']['control']),
                   '{}.input1'.format(divide_node))

    # list all offset groups
    offset_grp_list = [joint_data[item]['driver_00_offset'] for item in names_list]
    # connect mid control to all offset groups
    for item in offset_grp_list:
        # stop on c6, not connecting c7
        if item == offset_grp_list[-1]:
            break
        mc.connectAttr('{}.output'.format(divide_node),
                       '{}.r'.format(item))

    # connect c1 control to start offset group
    mc.connectAttr('{}.r'.format(module_data['controls']['c1']['control']),
                   '{}.r'.format(joint_data['c1']['driver_01_offset']))
    # connect c7 control to end offset group
    mc.connectAttr('{}.r'.format(module_data['controls']['c7']['control']),
                   '{}.r'.format(joint_data['c7']['driver_00_offset']))

    # GROUP AND ORGANIZE SECTION ________________________________________________________________________

    joint_grp = mc.group(joint_data['c7']['bind'],
                         joint_data['c7']['driver_00_offset'],
                         name='{}_jnt_grp'.format(module_name))

    surface_grp = mc.group(loft_surface, name='{}_srf_grp'.format(module_name))

    follicle_list = [module_data['follicles'][flc]['transform'] for flc in module_data['follicles']]
    follicle_grp = mc.group(follicle_list, name='{}_flc_grp'.format(module_name))

    controls_list = [module_data['controls'][ctrl]['group'] for ctrl in module_data['controls']]
    control_grp = mc.group(controls_list, name='{}_ctrl_grp'.format(module_name))

    module_grp = mc.group(
        joint_grp,
        surface_grp,
        follicle_grp,
        control_grp,
        name='{}_module_grp'.format(module_name))

    # add groups to module data
    module_data['groups'] = {
        'module': module_grp,
        'joint': joint_grp,
        'surface': surface_grp,
        'follicle': follicle_grp,
        'control': control_grp}

    return module_data
