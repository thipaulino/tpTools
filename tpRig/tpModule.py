import tpRig.tpNameConvention as tpName
import maya.cmds as mc


class TpModule(object):

    def __init__(self, name=None, side=None):
        self.tp_name = tpName.NameConvention()

        self.module_name = name
        self.module_side = side

        self.module_group_list = []
        self.module_top_group = None
        self.module_data = None
        self.module_control_node = None

        self.module_group_dict = {
            'joint': [],
            'rig_joint': [],
            # 'utility_joint': [],
            'bind_joint': [],
            'geometry': [],
            'rig_geometry': [],
            'surface': [],
            'locator': [],
            'utility': [],
            'follicle': [],
            'curve': []
        }

        # module component lists
        self.follicle_list = []
        self.joint_list = []
        self.joint_rig_list = []
        self.util_joint_list = []
        self.joint_bind_list = []
        self.deformer_list = []
        self.curve_list = []
        self.geometry_list = []
        self.surface_list = []
        self.locator_list = []

        # module component groups
        self.joint_group = None
        self.follicle_group = None
        self.utility_group = None

        self.handle_list = []

        self.parent_joint = None
        self.children_joint = None

        self.module_build_list = [
            self.__create_module_top_group
        ]

    def build_module(self):
        self.module_build_list.append(self.__pack_and_ship)

        for function in self.module_build_list:
            function()

    def __pack_and_ship(self):
        for component_type in self.module_group_dict:
            if self.module_group_dict[component_type]:
                group = mc.group(self.module_group_dict[component_type],
                                 name=self.tp_name.build(name=self.module_name,
                                                         side=self.module_side,
                                                         node_type=component_type,
                                                         group=True))
                self.module_group_list.append(group)

        mc.parent(self.module_group_list, self.module_top_group)

    def __create_module_control_node(self):
        """
        The control node holds the muscle_pull attribute, which will be used
        to drive the system
        """
        self.module_control_node = mc.createNode('controller', name=self.tp_name.build(name=self.module_name,
                                                                                       side=self.module_side,
                                                                                       node_type='controller'))
        mc.addAttr(self.module_control_node, longName='metadata', dataType='string')

    def __create_module_top_group(self):
        self.module_top_group = mc.group(empty=True,
                                         name=self.tp_name.build(name=self.module_name,
                                                                 side=self.module_side,
                                                                 node_type='module',
                                                                 group=True))

        # self.module_top_group = TpModuleGroup(name=self.module_name,
        #                                       side=self.module_side,
        #                                       component_type='module')
        # self.module_top_group.add_attribute_metadata()
        # self.module_top_group.build()

    def get_module_top_group(self):
        return self.module_top_group

    def get_module_name(self):
        return self.module_name

    def get_module_side(self):
        return self.module_side

    def get_surface_list(self):
        return self.surface_list

    def get_follicle_list(self):
        return self.follicle_list

    def get_joint_list(self):
        return self.joint_list

    def list_available_data(self):
        pass

    def parent_under(self, parent):
        mc.parent(self.module_top_group, parent)

    def append_to_module(self):
        pass


class TpModuleGroupManager:

    def __init__(self):
        pass

    def add_group(self):
        pass

    def get_by_type(self):
        pass


class TpModuleGroup:

    def __init__(self, name, side, component_type):
        self.group_name = name
        self.group_component_type = component_type
        self.group_side = side
        self.item_list = []
        self.attribute_dict = {}
        self.attribute_queue_list = []

    def build(self):
        # do group
        self.do_group()
        self.build_attribute_list()
        # add items
        # parent under
        pass

    def do_group(self):
        pass

    def get_name(self):
        return self.group_name

    def get_component_type(self):
        return self.group_component_type

    def set_component_type(self):
        pass

    def group_type(self):
        pass

    def add_item(self, item):
        self.item_list.append(item)

    def add_item_list(self, item_list):
        self.item_list.extend(item_list)

    def parent_under(self, parent):
        mc.parent(self.group_name, parent)

    def add_attribute(self):
        pass

    def build_attribute_list(self):
        if self.attribute_queue_list:
            for command in self.attribute_queue_list:
                exec(command)
        else:
            pass

    def add_attribute_boolean(self):
        pass

    def add_attribute_double(self, long_name, keyable, default_value, min_value, max_value):
        mc.addAttr(self.group_name,
                   longName=long_name,
                   keyable=keyable,
                   attributeType='double',
                   defaultValue=default_value,
                   minValue=min_value,
                   maxValue=max_value)

        self.attribute_dict.update({long_name: '{group}.{attr}'.format(group=self.group_name, attr=long_name)})

    def queue_add_attribute_double(self, long_name, keyable, default_value, min_value, max_value):
        command = 'mc.addAttr({group}, longName={long_name}, keyable={keyable}, attributeType="double", ' \
                  'defaultValue={def_value}, minValue={min}, maxValue={max})'.format(group=self.group_name,
                                                                                     long_name=long_name,
                                                                                     keyable=keyable,
                                                                                     def_value=default_value,
                                                                                     min=min_value,
                                                                                     max=max_value)
        self.attribute_queue_list.append(command)

    def add_attribute_float(self):
        pass

    def add_attribute_sting(self):
        pass

    def add_attribute_metadata(self):
        command = 'mc.addAttr({group}, longName="metadata", dataType="string")'.format(group=self.group_name)
        self.attribute_queue_list.append(command)

    def add_attribute_division(self):
        pass

    def connect_attribute_from(self, attribute, in_attribute):
        mc.connectAttr(in_attribute, self.attribute_dict[attribute], force=True)

