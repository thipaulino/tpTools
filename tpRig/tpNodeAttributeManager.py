import maya.cmds as mc


class TpNodeAttributeManager:

    def __init__(self, node_name):
        """
        Used to create and manage attributes using standard mc.addAttr() flags,
        in any given maya node.
        :param node_name:
        """
        self.node_name = node_name
        self.attribute_dict = {}
        self.attribute_queue_list = []
        self.attribute_object_list = []

    def add_node(self, node):
        self.node_name = node

    def build(self):
        self.build_attribute_list()

    def build_attribute_list(self):
        if self.attribute_queue_list:
            for command in self.attribute_queue_list:
                exec(command)
        else:
            pass

    def add_attribute_boolean(self):
        pass

    def add_attribute_double(self, long_name, keyable, default_value, min_value, max_value):
        mc.addAttr(self.node_name,
                   longName=long_name,
                   keyable=keyable,
                   attributeType='double',
                   defaultValue=default_value,
                   minValue=min_value,
                   maxValue=max_value)

        self.attribute_dict.update({long_name: '{group}.{attr}'.format(group=self.node_name, attr=long_name)})

    def add_attribute(self, attribute_name, **kwargs):
        attribute_object = TpNodeAttribute(self.node_name, attribute_name)
        attribute_object.create(**kwargs)
        self.attribute_object_list.append(attribute_object)

        return attribute_object

    def add_attribute_metadata(self):
        command = 'mc.addAttr({group}, longName="metadata", dataType="string")'.format(group=self.node_name)
        self.attribute_queue_list.append(command)

    def add_attribute_division(self, attribute_name, visible_name):
        division_preset_dict = {
            'niceName': '________',
            'attributeType': 'enum',
            'enumName': visible_name,
            'keyable': True
        }

        division_attribute = self.add_attribute(attribute_name, **division_preset_dict)
        division_attribute.lock()

    def get_attribute(self, attribute_name):
        for attribute in self.attribute_object_list:
            if attribute.get_name() == attribute_name:
                return attribute

    def get_attribute_object_list(self):
        return self.attribute_object_list

    def connect_attribute_from(self, attribute, in_attribute):
        mc.connectAttr(in_attribute, self.attribute_dict[attribute], force=True)


class TpNodeAttribute:

    def __init__(self, node_name=None, attribute_name=None):
        self.node_name = node_name
        self.attribute_name = attribute_name
        self.node_dot_attribute = "{}.{}".format(node_name, attribute_name)
        self.is_division = False

        self.attribute_parameter_dict = {}

    def create(self, **kwargs):
        mc.addAttr(self.node_name, longName=self.attribute_name, **kwargs)
        self.attribute_parameter_dict = kwargs

    def connect_to(self, node_attribute):
        mc.connectAttr(self.node_dot_attribute, node_attribute)

    def connect_from(self, node_attribute):
        mc.connectAttr(node_attribute, self.node_dot_attribute)

    def set_value(self, value):
        mc.setAttr(self.get_node_dot_attribute(), value)

    def lock(self):
        mc.setAttr(self.node_dot_attribute, lock=1)

    def get_value(self):
        pass

    def get_node_name(self):
        return self.node_name

    def get_attribute_name(self):
        return self.attribute_name

    def get_node_dot_attribute(self):
        return self.node_dot_attribute

    def get_parameters_dict(self):
        return self.attribute_parameter_dict

    def get_type(self):
        return self.attribute_parameter_dict['attributeType']

