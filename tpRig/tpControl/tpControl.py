import tpRig.tpNameConvention as tpName
import pymel.core as pm
import maya.cmds as mc
import json
import os

import tpRig.tpRigUtils as tpu


class ControlShapeLib(object):

    def __init__(self, prefix='', name='ctrlLib', index='', suffix='crv'):

        # import shapes data
        self.curve_dict = tpu.read_json_file(
            'E:/Scripts/tpTools/tpRig/tpControl/data/curve_data.json')

        # assemble name
        self.name_component_list = [item for item in [prefix, name, index, suffix] if item]
        self.name = name

        # set shape type
        self.shape_type = 'cube'  # cube defined by default

        # build shape
        self.transform = build_curve_from_data(self.curve_dict[self.shape_type], self.name)
        mc.setAttr(self.transform + ".overrideEnabled", 1)
        mc.setAttr(self.transform + ".overrideRGBColors", 1)

        self.shape_list = mc.listRelatives(self.transform, shapes=True)
        self.shape_color = get_curve_color(self.name)

        self.color_presets = {
            'yellow': (1, 1, 0),
            'green': (0, 1, 0),
            'aqua': (0, 1, 1),
            'blue': (0, 0, 1),
            'orange': (1, 0.5, 0),
            'red': (1, 0, 0),
            'magenta': (1, 0.04, 0.57),
            'purple': (0.83, 0.04, 1),
            'baby_blue': (0.28, 0.42, 0.99),
        }

    def list_available_shapes(self):
        return [shape_name for shape_name in self.curve_dict]

    def change_type(self):
        control_shape_list = mc.listRelatives(self.transform, shapes=True)
        for index, shape in enumerate(control_shape_list):
            mc.rename(shape, 'temp_control_shape_{:02d}'.format(index))

        temp_transform = build_curve_from_data(
            self.curve_dict[self.shape_type],
            self.name,
            temp=True)
        replace_shapes(self.transform, temp_transform)

    def set_name(self, name):
        self.name = name
        pm.rename(self.transform, self.name)

    def set_color_rgb(self, color):
        set_curve_color(self.name, color)
        self.shape_color = color

    def set_color_preset(self, color_name):
        set_curve_color(self.name, self.color_presets[color_name])
        self.shape_color = self.color_presets[color_name]

    def get_color_preset_list(self):
        return self.color_presets.keys()

    def get_curve_color(self):
        return self.shape_color

    def get_name(self):
        return self.name

    def get_shape_type(self):
        return self.shape_type

    def get_position_data(self, world_space=False):
        """
        Gets cv position data for each shape node in the transform, and returns a dictionary.
        Data Structure
        {"Shape_01_Name": [[cvPositionX, cvPositionY, cvPositionZ],
                           [cvPositionX, cvPositionY, cvPositionZ],
                           ...],
         "Shape_02_Name": ... }

        :param world_space:
        :return:
        """
        shape_list = mc.listRelatives(self.transform, shapes=True)
        shape_dict = {}

        for shape in shape_list:
            cv_len = len(mc.getAttr('{}.cp'.format(shape), multiIndices=True))
            # curve_deg = mc.getAttr('nurbsCircleShape1' + ".degree")
            # curve_spa = mc.getAttr('nurbsCircleShape1' + ".spans")
            # # CV's = degrees + spans
            # cv_len = (curve_deg + curve_spa) - 1
            shape_dict[shape] = []

            for cv_index in range(cv_len):
                if world_space:
                    position = mc.xform('{}.cv[{}]'.format(shape, cv_index),
                                        query=True,
                                        translation=True,
                                        worldSpace=True)
                else:
                    position = mc.xform('{}.cv[{}]'.format(shape, cv_index),
                                        query=True,
                                        translation=True)

                shape_dict[shape].append(position)

        return shape_dict

    def store_new_shape_form(self, new_form_name, transform_name):
        """
        Note - method not working for closed circle
        :param new_form_name:
        :param transform_name:
        :return:
        """

        mc.delete(self.transform)
        self.transform = transform_name

        new_form_data_dict = {new_form_name: {}}

        shape_position_dict = self.get_position_data()

        for index, shape in enumerate(shape_position_dict, 1):
            shape_rename = 'shape_{:02d}'.format(index)

            # transfer cv position data to new dictionary
            new_form_data_dict[new_form_name].update({shape_rename: {}})
            new_form_data_dict[new_form_name][shape_rename].update({"p": shape_position_dict[shape]})

            # get knots and update to dictionary
            curve_info_node = mc.createNode('curveInfo', name='temp_curve_info_node')
            mc.connectAttr('{}.local'.format(shape), '{}.inputCurve'.format(curve_info_node))
            shape_knots = mc.getAttr('{}.knots'.format(curve_info_node))[0]
            mc.delete(curve_info_node)

            new_form_data_dict[new_form_name][shape_rename].update({"k": shape_knots})

            # get shape curve degree and assign to dictionary
            curve_degree = mc.getAttr('{}.degree'.format(shape))
            new_form_data_dict[new_form_name][shape_rename].update({"d": curve_degree})

            # get either curve is periodic
            curve_periodic = False if mc.getAttr('{}.form'.format(shape)) == 0 else True
            new_form_data_dict[new_form_name][shape_rename].update({"per": curve_periodic})

        self.curve_dict.update(new_form_data_dict)
        self.export_curve_dic_to_json()

    def set_type(self, shape_type):
        self.shape_type = shape_type
        self.change_type()

    def set_type_arrow(self):
        self.shape_type = 'arrow'
        self.change_type()

    def set_type_cross(self):
        self.shape_type = 'cross'
        self.change_type()

    def set_type_crown(self):
        self.shape_type = 'crown'
        self.change_type()

    def set_type_cube(self):
        self.shape_type = 'cube'
        self.change_type()

    def set_type_cube_on_base(self):
        self.shape_type = 'cube_on_base'
        self.change_type()

    def set_type_diamond(self):
        self.shape_type = 'diamond'
        self.change_type()

    def set_type_fist(self):
        self.shape_type = 'fist'
        self.change_type()

    def set_type_foot(self):
        self.shape_type = 'foot'
        self.change_type()

    def set_type_move(self):
        self.shape_type = 'move'
        self.change_type()

    def set_type_rotation(self):
        self.shape_type = 'rotation'
        self.change_type()

    def set_type_single_rotate(self):
        self.shape_type = 'single_rotate'
        self.change_type()

    def set_type_sphere(self):
        self.shape_type = 'sphere'
        self.change_type()

    def set_shape_rotate(self, ro=(0, 0, 0)):
        temp_transform = pm.group(name='temp_transform', empty=True)
        temp_transform.setRotation(ro, ws=True)

        pm.parent(self.transform.listRelatives(shapes=True),
                  temp_transform, r=True, s=True)
        transfer_shape_obj(temp_transform, self.transform)

    def set_shape_translation(self, t=(0, 0, 0)):
        pass

    def set_shape_scale(self, s=(1, 1, 1)):
        pass

    def shape_set_position(self, **kwargs):
        pass

    def set_color_red(self):
        pass

    def set_color_green(self):
        pass

    def set_color_blue(self):
        pass

    def set_color_yellow(self):
        pass

    def set_color_purple(self):
        pass

    def get_transform_obj(self):
        return self.transform

    def get_transform_name(self):
        pass

    def get_shape_list(self):
        return self.transform.listRelatives(shapes=True)

    def get_type_data(self):
        return self.curve_dict[self.shape_type]

    def add_top_grp(self):
        pass

    def export_curve_dic_to_json(self):
        tpu.export_dict_as_json(self.curve_dict, 'curve_data', 'E:/Scripts/tpTools/tpRig/tpControl/data/')


class Control(ControlShapeLib):

    def __init__(self, **kwargs):
        super(Control, self).__init__(**kwargs)

        # define name
        # self.name = kwargs['name']
        # self.scale = kwargs['scale']
        # self.prefix = kwargs['prefix']
        # self.suffix = kwargs['suffix']
        # self.index = kwargs['index']
        # self.type = kwargs['type']
        # self.child = kwargs['child']

        self.offset_grp_list = []

    def cast_control(self):
        """
        In future update, creating the control object won't create it immidiatly.
        Cast control will be used to create the control in the scene, once setup is done.
        The intention is to implement the idea of loading a control from the scene.
        :return:
        """

    def control(self):
        """
        :return control name:
        """

        shape = ControlShapeLib()
        # shape.arrow()
        return shape

    def transform_match_position(self, target, **kwargs):
        if 't' in kwargs:
            target_translate = mc.xform(target, query=True, translation=True, worldSpace=True)
            mc.xform(self.transform, t=target_translate, worldSpace=True)

        if 'r' in kwargs:
            target_rotate = mc.xform(target, query=True, rotation=True, worldSpace=True)
            mc.xform(self.transform, rotation=target_rotate, worldSpace=True)

        if 's' in kwargs:
            target_scale = mc.xform(target, query=True, scale=True, worldSpace=True)
            mc.xform(self.transform, scale=target_scale, worldSpace=True)

    def top_group_match_position(self, target, **kwargs):
        if 't' in kwargs:
            target_translate = mc.xform(target, query=True, translation=True, worldSpace=True)
            mc.xform(self.offset_grp_list[-1], t=target_translate, worldSpace=True)

        if 'r' in kwargs:
            target_rotate = mc.xform(target, query=True, rotation=True, worldSpace=True)
            mc.xform(self.offset_grp_list[-1], rotation=target_rotate, worldSpace=True)

        if 's' in kwargs:
            target_scale = mc.xform(target, query=True, scale=True, worldSpace=True)
            mc.xform(self.offset_grp_list[-1], scale=target_scale, worldSpace=True)

    def shape_match_position(self, target, **kwargs):
        temp_transform = mc.group(name='temp_transform', empty=True)
        shapes = self.shapes_list()

        mc.parent(shapes, temp_transform, r=True, s=True)

        if 't' in kwargs:
            target_position = mc.xform(target, query=True, translation=True, worldSpace=True)
            mc.xform(temp_transform, translation=target_position, worldSpace=True)
        if 'r' in kwargs:
            target_rotation = mc.xform(target, query=True, rotation=True, worldSpace=True)
            mc.xform(temp_transform, rotation=target_rotation, worldSpace=True)
        if 's' in kwargs:
            target_scale = mc.xform(target, query=True, scale=True, worldSpace=True)
            mc.xform(temp_transform, scale=target_scale, worldSpace=True)

        for shape in shapes:
            transfer_shape(shape, self.transform)

        mc.delete(temp_transform)

    def set_position(self, translation_list):
        mc.xform(self.transform, translation=translation_list, worldSpace=True)

    def restore_shape_position_from_data(self, shape_data_dict, world_space=False):
        """
        Data Structure
        {"Shape_01_Name": [[cvPositionX, cvPositionY, cvPositionZ],
                           [cvPositionX, cvPositionY, cvPositionZ],
                           ...],
         "Shape_02_Name": ... }

        :param shape_data_dict:
        :param world_space:
        :return:
        """

        for shape in shape_data_dict:
            for index, cv_position in enumerate(shape_data_dict[shape]):
                if world_space:
                    mc.xform('{}.cv[{}]'.format(shape, index), translation=cv_position, worldSpace=True)
                else:
                    mc.xform('{}.cv[{}]'.format(shape, index), translation=cv_position)

    def top_offset_grp_set_position(self):
        pass

    def set_shape_type(self, shape_type):
        """
        :return:
        """
        pass

    def shapes_list(self):
        shapes = mc.listRelatives(self.transform, shapes=True)
        return shapes

    def constraint_target(self, target, **kwargs):
        mc.parentConstraint(self.transform, target, mo=kwargs['mo'])

    def set_shape_position(self, pointer):
        pass

    def shape_type(self):
        pass

    def add_index(self, n):
        pass

    def change_index(self):
        pass

    def change_prefix(self):
        pass

    def offset_grp(self):
        pass

    def add_offset_grp(self, negate=False):
        index = 1 if not self.offset_grp_list else len(self.offset_grp_list) + 1

        if index == 1:
            new_group = mc.group(self.transform,
                                 name='{}_{:02d}_grp'.format(self.transform, index))
        else:
            new_group = mc.group(
                empty=True,
                name='{}_{:02d}_grp'.format(self.transform, index),
                parent=self.offset_grp_list[0])
            mc.parent(self.transform, new_group)

        self.offset_grp_list.append(new_group)

        if negate:
            translation_divide_node = mc.createNode(
                'multiplyDivide',
                name='{}_translation_negate_divide_node'.format(self.transform))
            mc.connectAttr(self.transform + '.translate', translation_divide_node + '.input1')
            mc.connectAttr(translation_divide_node + '.output', new_group + '.translate')
            mc.setAttr(translation_divide_node + '.input2', -1, -1, -1)

            rotate_divide_node = mc.createNode(
                'multiplyDivide',
                name='{}_translation_negate_divide_node'.format(self.transform))
            mc.connectAttr(self.transform + '.rotate', rotate_divide_node + '.input1')
            mc.connectAttr(rotate_divide_node + '.output', new_group + '.rotate')
            mc.setAttr(rotate_divide_node + '.input2', -1, -1, -1)

        return new_group

    def get_offset_grp_list(self):
        return self.offset_grp_list

    def get_top_group(self):
        return self.offset_grp_list[-1]

    def negate_grp(self):
        pass

    @property
    def position(self):
        return

    @position.setter
    def position(self, value):
        pass

    def constraint_to(self):
        pass

    def constraint_as_master(self):
        pass

    def connect(self):
        pass

    def transform_node(self):
        pass


def replace_shapes(target_transform_obj, temp_transform_obj):
    """
    Removes shapes from target transform and replaces it with provided shapes list
    :param target_transform_obj:
    :param temp_transform_obj:
    :return:
    """
    target_shapes = mc.listRelatives(target_transform_obj, shapes=True)
    mc.delete(target_shapes)

    shapes = mc.listRelatives(temp_transform_obj, shapes=True)
    mc.parent(shapes, target_transform_obj, r=True, shape=True)
    mc.delete(temp_transform_obj)


def replace_shapes_pymel(target_transform_obj, temp_transform_obj):
    """
    Removes shapes from target transform and replaces it with provided shapes list
    :param target_transform_obj:
    :param temp_transform_obj:
    :return:
    """
    target_shapes = target_transform_obj.listRelatives(s=1)
    pm.delete(target_shapes)

    shapes = temp_transform_obj.listRelatives(shapes=True)
    pm.parent(shapes, target_transform_obj, r=True, shape=True)
    pm.delete(temp_transform_obj)


def transfer_shape(shape, new_parent):
    """
    Transfers shape to new transform parent maintaining the shape offset
    :param shape:
    :param new_parent:
    :return:
    """
    # Store CV World Position
    cv_name_list = mc.getAttr(shape + '.cp', multiIndices=True)
    cv_position_list = []

    for cv_name in cv_name_list:
        cv_position = mc.xform('{}.cp[{}]'.format(shape, cv_name),
                               query=True, translation=True, worldSpace=True)
        cv_position_list.append(cv_position)

    # Parent the shapeNode
    mc.parent(shape, new_parent, r=True, s=True)

    # Restore the world position
    for cv_name in cv_name_list:
        mc.xform('{}.cp[{}]'.format(shape, cv_name), a=True,
                 worldSpace=True, t=cv_position_list[cv_name])


def transfer_shape_obj(temp_transform, target_transform):
    """
    Transfers shape to new transform parent maintaining the shape world position
    :param temp_transform:
    :param target_transform:
    :return:
    """
    temp_transform_shapes = temp_transform.listRelatives(shapes=True)
    shapes_data_dict = {}

    # stores all shapes cp translation data
    for shape in temp_transform_shapes:
        control_points = pm.getAttr(shape.cp, multiIndices=True)
        shapes_data_dict[shape] = {'cp': control_points,
                                   'cp_translate': {}}
        for cp in shapes_data_dict[shape]['cp']:
            cp_translate = pm.xform(shape.cp[cp], q=True, t=True, ws=True)
            shapes_data_dict[shape]['cp_translate'].update({cp: cp_translate})

    # Parent the shapeNode
    pm.parent(temp_transform_shapes, target_transform, r=True, s=True)
    pm.delete(temp_transform)

    # Restore shapes world position
    for shape in temp_transform_shapes:
        for cp in shapes_data_dict[shape]['cp']:
            pm.xform(shape.cp[cp], a=True, ws=True,
                     t=shapes_data_dict[shape]['cp_translate'][cp])


def build_curve_from_data(curve_data, name, temp=False):
    """
    Creates multiple shapes based on data and parents under one curve transform
    :param curve_data: dictionary with date to build multiple shape curve
    :key 'shapes': Iterable, dictionary with data to build one curve
    :key 'p': Used by curve cmds, list of all points to compose one curve
    :key 'per': boolean - Periodic, used by curve cmds
    :key 'd': int - Degrees, used by curve command
    :key 'k': list - Knots, used by curve command
    :param name:
    :temp True if transform node should get temporary name:
    :return curve transform: multi shape curve
    """
    transform_list = []
    shape_list = []

    for shape_data in curve_data:
        curve = mc.curve(point=curve_data[shape_data]['p'],
                         periodic=curve_data[shape_data]['per'],
                         degree=curve_data[shape_data]['d'],
                         knot=curve_data[shape_data]['k'])
        shapes = mc.listRelatives(curve, shapes=1)[0]
        transform_list.append(curve)
        shape_list.append(shapes)

    transform_name = name if temp is False else 'temp_control_name'
    output_transform = mc.group(name=transform_name, empty=True)
    mc.parent(shape_list, output_transform, r=True, shape=True)

    for index, curve_shape in enumerate(shape_list):
        mc.rename(curve_shape, '{}_{:02d}_Shape'.format(name, index))

    mc.delete(transform_list)
    mc.select(clear=True)

    return output_transform


def build_curve_from_data_pymel(curve_data, name):
    """
    Creates multiple shapes based on data and parents under one curve transform
    :param curve_data: dictionary with date to build multiple shape curve
    :key 'shapes': Iterable, dictionary with data to build one curve
    :key 'p': Used by curve cmds, list of all points to compose one curve
    :key 'per': boolean - Periodic, used by curve cmds
    :key 'd': int - Degrees, used by curve command
    :key 'k': list - Knots, used by curve command
    :param name:
    :return curve transform: multi shape curve
    """
    transform_list = []
    shape_list = []

    for shape_data in curve_data:
        curve = pm.curve(p=curve_data[shape_data]['p'], per=curve_data[shape_data]['per'],
                         d=curve_data[shape_data]['d'], k=curve_data[shape_data]['k'])
        shapes = curve.listRelatives(shapes=1)
        transform_list.append(curve)
        shape_list.append(shapes)

    output_transform = pm.group(n=name, em=1)
    pm.parent(shape_list, output_transform, relative=True, shape=True)
    pm.delete(transform_list)
    pm.select(clear=True)

    return output_transform


def pm_set_curve_color(curve, color=(1, 1, 1)):
    shapes = curve.listRelatives(shapes=True)

    for shape in shapes:
        pm.setAttr(shape.overrideEnabled, 1)
        pm.setAttr(shape.overrideRGBColors, 1)

        for channel, color in zip('RGB', color):
            pm.setAttr("{}.overrideColor{}".format(curve, channel), color)


def decompose_curve_to_data(target):
    transform = pm.PyNode(target)
    shapes = transform.listRelatives(shapes=True)
    return shapes


def set_curve_color(ctrl, color=(1, 1, 1)):
    """
    Set control color function
    :param ctrl:
    :param color:
    :return:
    """

    rgb = ("R", "G", "B")
    mc.setAttr(ctrl + ".overrideEnabled", 1)
    mc.setAttr(ctrl + ".overrideRGBColors", 1)

    for channel, color in zip(rgb, color):
        mc.setAttr("{}.overrideColor{}".format(ctrl, channel), color)


def get_curve_color(curve):
    return [mc.getAttr("{}.overrideColor{}".format(curve, channel)) for channel in 'RGB']
