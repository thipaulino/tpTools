import tpRig.tpNameConvention as tpName
import tpRig.tpNodeAttributeManager as tpAttr
import maya.cmds as mc


class TpModule(object):

    def __init__(self, name=None, side=None):
        """
        The main function of the module is to:
        - Standardize groups across the system
        - Create the module top group
        - Create and manage top group attributes
        - Manage module data
        - Group and organize all created nodes

        :param name:
        :param side:
        """
        self.tp_name = tpName.NameConvention()
        self.module_attribute_manager = None

        self.module_name = name
        self.module_side = side

        self.module_group_list = []
        self.module_top_group = None
        self.module_data = None
        self.module_control_node = None
        self.module_control_attribute_list = []

        self.module_group_dict = {
            'joint': [],
            'rig_joint': [],  # utility_joint
            'bind_joint': [],
            'geometry': [],
            'rig_geometry': [],
            'surface': [],
            'locator': [],
            'utility': [],
            'follicle': [],
            'curve': [],
            'module': [],
            'sub_module': []
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
        self.sub_module_list = []

        # module component groups
        self.joint_group = None
        self.follicle_group = None
        self.utility_group = None

        self.handle_list = []

        self.parent_joint = None
        self.children_joint = None

        # module attributes
        self.locator_scale = 0.2
        self.joint_radius = 0.2

        self.module_pre_build_list = [  # not implemented
            self._create_module_top_group
        ]

        self.module_build_list = [
            self._create_module_top_group
        ]

        self.module_post_build_list = [  # not implemented
            self._pack_and_ship,
            self._create_sub_module_mirror_attributes
        ]

    def build_module(self):
        self.module_build_list.extend([
            self._pack_and_ship,
            self._create_sub_module_mirror_attributes
        ])

        for function in self.module_build_list:
            print('[{}][{}] Starting...'.format(self.__class__.__name__, function.__name__))
            function()
            print('[{}][{}] Done'.format(self.__class__.__name__, function.__name__))

    def build_module_beta(self):  # not implemented
        for pre_build_function in self.module_pre_build_list:
            pre_build_function()

        for build_function in self.module_build_list:
            build_function()

        for post_build_function in self.module_post_build_list:
            post_build_function()

    def register_module_build_method(self, method):  # not implemented
        self.module_build_list.append(method)

    def set_name(self, name):
        self.module_name = name

    def set_side(self, side):
        self.module_side = side

    def add_to_module_metadata(self):
        pass

    # getters
    def get_module_attribute_manager(self):
        return self.module_attribute_manager

    def get_module_attribute_object_list(self):
        return [attribute for attribute in self.module_attribute_manager.get_attribute_object_list()]

    def get_module_metadata(self):
        pass

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

    def get_sub_module_list(self):
        pass

    # multi purpose
    def list_available_data(self):
        pass

    def get_sub_module_top_group_list(self):
        return [sub_module.get_module_top_group() for sub_module in self.sub_module_list]

    def parent_under(self, parent):
        mc.parent(self.module_top_group, parent)

    def append_to_module(self):
        pass

    def _create_module_top_group(self):
        self.module_top_group = mc.group(empty=True,
                                         name=self.tp_name.build(name=self.module_name,
                                                                 side=self.module_side,
                                                                 node_type='module',
                                                                 group=True))

        self.module_attribute_manager = tpAttr.TpNodeAttributeManager(self.module_top_group)

    def _create_module_top_group_attributes(self):
        # hard code - create CONTROL division
        pass

    def _create_sub_module_mirror_attributes(self):
        """
        If there are sub_modules on the list, gets attribute managers
        :return:
        """
        # hard code - create SUB_MODULE division
        if self.sub_module_list:
            for n, sub_module in enumerate(self.sub_module_list, 1):
                # get sub_module naming information
                sub_module_name = sub_module.get_module_name()
                sub_module_side = sub_module.get_module_side()

                # TODO: fix submodule attribute division issue
                # add division
                # remove - division being registered and conflicting in top modules
                # or just do not register the division
                # self.module_attribute_manager.add_attribute_division('subMod' + str(n),
                #                                                      'subMod' + str(n))
                mc.addAttr(sub_module.get_module_top_group(),
                           longName='subMod' + str(n),
                           niceName='________',
                           attributeType='enum',
                           enumName='subMod' + str(n),
                           keyable=True)

                # get attribute object list
                sub_module_attribute_manager = sub_module.get_module_attribute_manager()
                sub_module_attribute_list = sub_module_attribute_manager.get_attribute_object_list()

                if sub_module_attribute_list:
                    for attribute in sub_module_attribute_list:
                        # transfers a single attribute from sub_module to module
                        attribute_name = attribute.get_attribute_name()
                        parameters_dict = attribute.get_parameters_dict()

                        module_attribute = self.module_attribute_manager.add_attribute(
                            attribute_name,
                            **parameters_dict)

                        module_attribute.connect_to(attribute.get_node_dot_attribute())

    def _connect_sub_module_attributes(self):
        if self.sub_module_list:
            for sub_module in self.sub_module_list:
                pass

    def _lock_and_hide_attributes(self):
        pass

    def _build_module_attributes(self):
        pass

    def _lock_and_hide(self):
        pass

    def _set_module_locator_scale(self):
        if self.module_group_dict['locator']:
            for locator in self.module_group_dict['locator']:
                for axis in 'XYZ':
                    mc.setAttr('{}.localScale{}'.format(locator, axis), self.locator_scale)

    def _set_module_joint_radius(self):
        if self.module_group_dict['joint']:
            for locator in self.module_group_dict['locator']:
                for axis in 'XYZ':
                    mc.setAttr('{}.localScale{}'.format(locator, axis), self.locator_scale)

    def _pack_and_ship(self):
        """
        Used to create and parent each component category to it's group.
        Also parents the groups under the module top group
        """
        for component_type in self.module_group_dict:
            if self.module_group_dict[component_type]:
                group = mc.group(self.module_group_dict[component_type],
                                 name=self.tp_name.build(name=self.module_name,
                                                         side=self.module_side,
                                                         node_type=component_type,
                                                         group=True))
                self.module_group_list.append(group)

        mc.parent(self.module_group_list, self.module_top_group)


# class TpModuleGroupManager:
#
#     def __init__(self):
#         pass
#
#     def add_group(self):
#         pass
#
#     def get_by_type(self):
#         pass
#
#
# class TpModuleGroup:
#
#     def __init__(self, name, side, component_type):
#         self.group_name = name
#         self.group_side = side
#         self.group_component_type = component_type
#
#         self.item_list = []
#         self.attribute_dict = {}
#         self.attribute_queue_list = []
#
#     def build(self):
#         # do group
#         self.do_group()
#         self.build_attribute_list()
#         # add items
#         # parent under
#         pass
#
#     def do_group(self):
#         pass
#
#     def get_name(self):
#         return self.group_name
#
#     def get_component_type(self):
#         return self.group_component_type
#
#     def set_component_type(self):
#         pass
#
#     def group_type(self):
#         pass
#
#     def add_item(self, item):
#         self.item_list.append(item)
#
#     def add_item_list(self, item_list):
#         self.item_list.extend(item_list)
#
#     def parent_under(self, parent):
#         mc.parent(self.group_name, parent)
#
#     def add_attribute(self):
#         pass
#
#     def build_attribute_list(self):
#         if self.attribute_queue_list:
#             for command in self.attribute_queue_list:
#                 exec(command)
#         else:
#             pass
#
#     def add_attribute_boolean(self):
#         pass
#
#     def add_attribute_double(self, long_name, keyable, default_value, min_value, max_value):
#         mc.addAttr(self.group_name,
#                    longName=long_name,
#                    keyable=keyable,
#                    attributeType='double',
#                    defaultValue=default_value,
#                    minValue=min_value,
#                    maxValue=max_value)
#
#         self.attribute_dict.update({long_name: '{group}.{attr}'.format(group=self.group_name, attr=long_name)})
#
#     def add_attribute_float(self):
#         pass
#
#     def add_attribute_sting(self):
#         pass
#
#     def add_attribute_metadata(self):
#         command = 'mc.addAttr({group}, longName="metadata", dataType="string")'.format(group=self.group_name)
#         self.attribute_queue_list.append(command)
#
#     def add_attribute_division(self):
#         pass
#
#     def connect_attribute_from(self, attribute, in_attribute):
#         mc.connectAttr(in_attribute, self.attribute_dict[attribute], force=True)

