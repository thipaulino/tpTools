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
            'bind_joint': [],
            'geometry': [],
            'rig_geometry': [],
            'surface': [],
            'locator': []
        }

        # module component lists
        self.follicle_list = None
        self.joint_list = None
        self.joint_rig_list = None
        self.joint_bind_list = None
        self.deformer_list = None
        self.curve_list = None
        self.geometry_list = None
        self.surface_list = None
        self.locator_list = None

        # module component groups
        self.joint_group = None
        self.follicle_group = None
        self.utility_group = None

        self.handle_list = None

        self.parent_joint = None
        self.children_joint = None

        self.module_build_list = [
            self.__create_module_control_node,
            self.__create_module_top_group
        ]

    def build_module(self):
        for function in self.module_build_list:
            function()

    def pack_and_ship(self):
        for group in self.module_group_dict:
            if self.module_group_dict[group]:


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
        self.module_top_group = mc.group(empty=True)

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


class TpModuleGroup:

    def __init__(self, name, component_type):
        self.group_name = name
        self.group_component_type = component_type
        self.item_list = []
        self.attribute_dict = {}

    def build(self):
        # do group
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

