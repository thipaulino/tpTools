import os
import maya.cmds as cmds
import tpRig.tpRigBuilder.tpModule as tpModule
reload(tpModule)


def build_module_object(module_name='', parent_action_name='root', background_color=None):
    module_group_name = 'BlendShape Tools'
    module_name = 'BlendShape Target Invert'

    blendshape_module_object = tpModule.Module(  # Freaking confusing, must change
        module_name=module_group_name,
        module_top_item_name=parent_action_name,
        background_color=background_color)

    blendshape_tool_obj = BlendShapeWeights()

    action_list = [
        tpModule.Action(module_name, module_group_name),
        tpModule.Action('Load Geometry Selection', module_name, blendshape_tool_obj.load_geometry_selection),
        tpModule.Action('Clear Geometry Selection', module_name, blendshape_tool_obj.clear_geometry_selection),
        tpModule.Action('Clear Weights List', module_name, blendshape_tool_obj.clear_stored_weight_list),
        tpModule.Action('Invert Weights', module_name, blendshape_tool_obj.invert_weights),
        tpModule.Action('Offset Target Index +5', module_name, blendshape_tool_obj.offset_target_index_five_positive),
        tpModule.Action('Offset Target Index -5', module_name, blendshape_tool_obj.offset_target_index_five_negative),
        tpModule.Action('Get Target Weights', module_name),
        tpModule.Action('Get Target 00', 'Get Target Weights', blendshape_tool_obj.copy_target_00),
        tpModule.Action('Get Target 01', 'Get Target Weights', blendshape_tool_obj.copy_target_01),
        tpModule.Action('Get Target 02', 'Get Target Weights', blendshape_tool_obj.copy_target_02),
        tpModule.Action('Get Target 03', 'Get Target Weights', blendshape_tool_obj.copy_target_03),
        tpModule.Action('Get Target 04', 'Get Target Weights', blendshape_tool_obj.copy_target_04),
        tpModule.Action('Set Target Weights', module_name),
        tpModule.Action('Set Target 00', 'Set Target Weights', blendshape_tool_obj.set_target_00),
        tpModule.Action('Set Target 01', 'Set Target Weights', blendshape_tool_obj.set_target_01),
        tpModule.Action('Set Target 02', 'Set Target Weights', blendshape_tool_obj.set_target_02),
        tpModule.Action('Set Target 03', 'Set Target Weights', blendshape_tool_obj.set_target_03),
        tpModule.Action('Set Target 04', 'Set Target Weights', blendshape_tool_obj.set_target_04),
    ]

    blendshape_module_object.add_action_list(action_list)

    return blendshape_module_object


class BlendShapeWeights:

    def __init__(self):
        self._geometry_transform = ''
        self._geometry_vertex_count = 0
        self._target_weight_list = []
        self._blendshape_node = ''
        self._target_index_offset = 0

    def load_geometry_selection(self):
        self._geometry_transform = cmds.ls(selection=True)[0]
        self._geometry_vertex_count = cmds.polyEvaluate(self._geometry_transform, vertex=True)

        self._blendshape_node = cmds.ls(
            cmds.listHistory(self._geometry_transform, allConnections=True), type='blendShape')[0]
        if not self._blendshape_node:
            raise RuntimeError("No blendShape node found connected to the selected mesh")

    def clear_geometry_selection(self):
        self._geometry_transform = ''
        self._geometry_vertex_count = 0
        self._blendshape_node = ''

    def clear_stored_weight_list(self):
        self._target_weight_list = []

    def invert_weights(self):
        invert_weight_list = []

        for weight in self._target_weight_list:
            invert_weight_list.append(1 - weight)

        self._target_weight_list = invert_weight_list

    def offset_target_index_five_positive(self):
        self._target_index_offset = self._target_index_offset + 5
        print('[BlendShape Weights] Target Index now starts at {}'.format(self._target_index_offset))

    def offset_target_index_five_negative(self):
        if self._target_index_offset >= 5:
            self._target_index_offset = self._target_index_offset - 5
        else:
            self._target_index_offset = 0
        print('[BlendShape Weights] Target Index now starts at {}'.format(self._target_index_offset))

    def copy_target_00(self):
        target_index = 0 + self._target_index_offset
        self._target_weight_list = get_target_weights_list(
            self._blendshape_node,
            target_index,
            self._geometry_vertex_count)

    def copy_target_01(self):
        target_index = 1 + self._target_index_offset
        self._target_weight_list = get_target_weights_list(
            self._blendshape_node,
            target_index,
            self._geometry_vertex_count)

    def copy_target_02(self):
        target_index = 2 + self._target_index_offset
        self._target_weight_list = get_target_weights_list(
            self._blendshape_node,
            target_index,
            self._geometry_vertex_count)

    def copy_target_03(self):
        target_index = 3 + self._target_index_offset
        self._target_weight_list = get_target_weights_list(
            self._blendshape_node,
            target_index,
            self._geometry_vertex_count)

    def copy_target_04(self):
        target_index = 4 + self._target_index_offset
        self._target_weight_list = get_target_weights_list(
            self._blendshape_node,
            target_index,
            self._geometry_vertex_count)

    def set_target_00(self):
        target_index = 0 + self._target_index_offset
        set_target_weights_list(
            self._blendshape_node,
            target_index,
            self._target_weight_list)

    def set_target_01(self):
        target_index = 1 + self._target_index_offset
        set_target_weights_list(
            self._blendshape_node,
            target_index,
            self._target_weight_list)

    def set_target_02(self):
        target_index = 2 + self._target_index_offset
        set_target_weights_list(
            self._blendshape_node,
            target_index,
            self._target_weight_list)

    def set_target_03(self):
        target_index = 3 + self._target_index_offset
        set_target_weights_list(
            self._blendshape_node,
            target_index,
            self._target_weight_list)

    def set_target_04(self):
        target_index = 4 + self._target_index_offset
        set_target_weights_list(
            self._blendshape_node,
            target_index,
            self._target_weight_list)


def get_target_weights_list(blendshape_node, target_index, geo_vertex_count):
    target_weight_list = cmds.getAttr(
        '{}.inputTarget[0].inputTargetGroup[{}].targetWeights[0:{}]'.format(
            blendshape_node,
            target_index,
            geo_vertex_count - 1))

    return target_weight_list


def set_target_weights_list(blendshape_node, target_index, target_weights_list):
    cmds.setAttr(
        '{}.inputTarget[0].inputTargetGroup[{}].targetWeights[0:{}]'.format(
            blendshape_node,
            target_index,
            len(target_weights_list) - 1),
        *target_weights_list)

