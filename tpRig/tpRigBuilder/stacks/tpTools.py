import maya.cmds as cmds
import random
import os
from ngSkinTools2 import api as ngst_api

import tpRig.tpRigBuilder.modules.tpUtilities as tpUtilities
import tpRig.tpRigBuilder.modules.tpProject as tpProject
import tpRig.tpRigBuilder.tpModule as tpModule
import tpRig.tpRigBuilder.tpUtilities as tpUtils

import tpRig.tpRigBuilder.modules.tpBlendshapeWeights as tpBlendShapeWeights
import tpRig.tpRigBuilder.modules.tpLocatorTools as tpLocator

reload(tpUtilities)
reload(tpProject)
reload(tpModule)
reload(tpBlendShapeWeights)
reload(tpLocator)


def build_stack():
    stack_module_obj = tpModule.Module(module_name='main_stack', module_has_top_item=False)

    utils_module_obj = tpUtilities.build_module_object(background_color='dark_green')

    center_loc_aimed = LocatorInCenterOriented()
    curve_from_selection_list = CurveFromPoints()
    create_visibility_attr = CreateVisibilityAttributes()

    blendshape_tools = tpBlendShapeWeights.build_module_object(parent_action_name='Utilities')
    multi_locator_tool = tpLocator.build_module_object(parent_action_name='Locator Tools')

    transfer_vertx_selection_tool = TransferSelection()

    action_list = [
        tpModule.Action('Set Geom Pivots to World Zero', 'Utilities', set_geom_pivots_to_world_zero),
        tpModule.Action('Locator Tools', 'Utilities'),
        tpModule.Action('BoundingBox Center VTX Selection', 'Locator Tools',
                        place_locator_in_boundingbox_center_vtx_selection),
        tpModule.Action('Average Center VTX Selection', 'Locator Tools', place_locator_in_vertex_selection_position_avg),
        tpModule.Action('Oriented Center Locator', 'Locator Tools'),
        tpModule.Action('Get vtx Selection A', 'Oriented Center Locator', center_loc_aimed.get_selection_a),
        tpModule.Action('Get vtx Selection B', 'Oriented Center Locator', center_loc_aimed.get_selection_b),
        tpModule.Action('Create Locator', 'Oriented Center Locator', center_loc_aimed.place_center_locator_oriented),
        tpModule.Action('Create Locators by segments Vtx Sel', 'Locator Tools', select_chunks_add_locator),
        tpModule.Action('Ziva Tools', 'Utilities'),
        tpModule.Action('Bones - Blendshape from Alembic', 'Ziva Tools', add_blendshape_from_selected),
        tpModule.Action('Curve From Selection List', 'Utilities'),
        tpModule.Action('Add Transform', 'Curve From Selection List', curve_from_selection_list.add_point),
        tpModule.Action('Add Transform List', 'Curve From Selection List', curve_from_selection_list.add_point_list),
        tpModule.Action('Select Transform List', 'Curve From Selection List',
                        curve_from_selection_list.select_transform_list),
        tpModule.Action('Build Curve', 'Curve From Selection List', curve_from_selection_list.create_curve),
        tpModule.Action('Skin Weight Tools', 'Utilities'),
        tpModule.Action('ngSkinTools2 Tools', 'Skin Weight Tools'),
        tpModule.Action('Selection Weights Export', 'ngSkinTools2 Tools',
                        export_ngskintools_weights_selection),
        tpModule.Action('Selection Weights Import', 'ngSkinTools2 Tools'),
        tpModule.Action('TPaulino Tools', 'Skin Weight Tools'),
        tpModule.Action('mGear Tools', 'Utilities'),
        tpModule.Action('Create Visibility Attributes', 'mGear Tools'),
        tpModule.Action('Check Visibility Control', 'Create Visibility Attributes',
                        create_visibility_attr.check_visibility_controller),
        tpModule.Action('List Rig Controls', 'Create Visibility Attributes', create_visibility_attr.list_rig_controls),
        tpModule.Action('Sort Controls', 'Create Visibility Attributes', create_visibility_attr.sort_controls_by_module),
        tpModule.Action('Create Attributes', 'Create Visibility Attributes',
                        create_visibility_attr.create_visibility_attributes),
        tpModule.Action('Mirror Vertex Selection', 'Utilities', get_mirror_vertex_selection),
        tpModule.Action('Select Guide Children', 'mGear Tools', mgear_select_guide_children),
        tpModule.Action('Transfer Vertex Selection', 'Utilities'),
        tpModule.Action('Load Source Vertices', 'Transfer Vertex Selection', transfer_vertx_selection_tool.load_source_vertex_list),
        tpModule.Action('Load Target Geo', 'Transfer Vertex Selection', transfer_vertx_selection_tool.load_target_geo),
        tpModule.Action('Transfer Selection', 'Transfer Vertex Selection', transfer_vertx_selection_tool.transfer_selection),
        tpModule.Action('Assign Random Color To Geo list', 'Utilities', assign_random_colors_to_geometry),
    ]

    utils_module_obj.add_action_list(action_list)
    utils_module_obj.add_module(blendshape_tools)
    utils_module_obj.add_module(multi_locator_tool)
    stack_module_obj.add_module(utils_module_obj)

    return stack_module_obj


def mirror_selection_to_frame(target_frame, reverse=False):
    """
    This function still needs development.
    Reverse means it multiplies by -1, which works for translation,
    but not for angles.

    :param target_frame:
    :param reverse:
    :return:
    """
    ctrl_list = cmds.ls(sl=True)
    ctrl_data = {}

    for ctrl in ctrl_list:
        ctrl_data.update({ctrl: {}})
        keyable_attr_list = cmds.listAttr(ctrl, keyable=True, visible=True)

        for attr in keyable_attr_list:
            attr_value = cmds.getAttr('{}.{}'.format(ctrl, attr))

            if cmds.keyframe(ctrl, attribute=attr, query=True, time=(3, 3)):
                ctrl_data[ctrl].update({attr: attr_value})
                print(attr, attr_value)

    for ctrl in ctrl_data:
        ctrl_split = ctrl.split(':')
        mirror_ctrl = ctrl_split[1].replace('_R', '_L')
        ctrl_join = ':'.join([ctrl_split[0], mirror_ctrl])
        print(ctrl_join)

        for attr in ctrl_data[ctrl]:
            if reverse:
                attr_val = ctrl_data[ctrl][attr] * -1
            cmds.setKeyframe(ctrl_join, attribute=attr, value=ctrl_data[ctrl][attr], time=target_frame)


def reverse_ctrl_keys():
    ctrl_list = cmds.ls(sl=True)
    current_time = cmds.currentTime(query=True)
    ctrl_data = {}

    for ctrl in ctrl_list:
        ctrl_data.update({ctrl: {}})
        keyable_attr_list = cmds.listAttr(ctrl, keyable=True, visible=True)

        for attr in keyable_attr_list:
            attr_value = cmds.getAttr('{}.{}'.format(ctrl, attr))

            if cmds.keyframe(ctrl, attribute=attr, query=True, time=(current_time, current_time)):
                ctrl_data[ctrl].update({attr: attr_value})

    for ctrl in ctrl_data:
        for attr in ctrl_data[ctrl]:
            attr_val = ctrl_data[ctrl][attr] * -1
            cmds.setKeyframe(ctrl, attribute=attr, value=attr_val, time=current_time)


def add_blendshape_from_selected():
    """
    Created to be used with Ziva Dynamics
    Once you bring in the alembic file for the bones animation, we need to blendshape,
    all the bones in the file to the ones in the muscle rig scene.

    For that we assume that the bones in the alembic have a prefix, so we:
    - Remove the prefix from the name
    - Find the bone with the same name
    - Create blenshape and target
    - Set target weight to 1

    :return:
    """
    geo_list_alembic = cmds.ls(sl=True)

    for geo in geo_list_alembic:
        target = geo.split(':')[1]
        # Create a blend shape node with an envelope of 1
        blend_shape_node = cmds.blendShape(target)[0]

        # Add the target geometry (with the same vertex count and order) to the blend shape node
        cmds.blendShape(blend_shape_node, edit=True, target=(target, 0, geo, 1))
        cmds.blendShape(blend_shape_node, edit=True, w=[(0, 1.0)])

        cmds.setKeyframe(blend_shape_node, attribute='envelope', value=0, time=1)
        cmds.setKeyframe(blend_shape_node, attribute='envelope', value=1, time=10)


def set_geom_pivots_to_world_zero():
    """
    Sets the pivot to world zero in all selected transform nodes.

    :return:
    """
    geo_list = cmds.ls(selection=True)

    for geo in geo_list:
        cmds.xform(geo, piv=(0, 0, 0), worldSpace=True)


def place_locator_in_boundingbox_center_vtx_selection():
    """
    Places a locator in the center of the bounding box of the vertex selection.

    :return:
    """

    # Get the selected vertices
    # selected_vertices = cmds.ls(selection=True, flatten=True)  # 31 corresponds to vertex selection type
    selected_vertices = cmds.filterExpand(sm=31)

    if not selected_vertices:
        cmds.warning("No vertices selected.")
    else:
        # Get the bounding box of the selected vertices
        bounding_box = cmds.polyEvaluate(selected_vertices, boundingBoxComponent=True)

        # Calculate the center point
        center_x = (bounding_box[0][0] + bounding_box[0][1]) / 2.0
        center_y = (bounding_box[1][0] + bounding_box[1][1]) / 2.0
        center_z = (bounding_box[2][0] + bounding_box[2][1]) / 2.0

        # volume_dimensions_avg = [sum(boundingbox_2d_axis)/2.0 for boundingbox_2d_axis in bounding_box]

        # Create an empty group to represent the center
        center_locator = cmds.ls(cmds.spaceLocator(name='center_locator')[0], long=True)[0]

        # Move the center group to the calculated center point
        cmds.xform(center_locator, translation=[center_x, center_y, center_z], worldSpace=True)

        # Select the center group
        cmds.select(center_locator)

        return center_locator


def place_locator_in_vertex_selection_position_avg():
    select = cmds.filterExpand(sm=31)
    coord_sum = [0, 0, 0]

    for vtx in select:
        coord = cmds.xform(vtx, query=True, translation=True, worldSpace=True)
        coord_sum = [axis + axis_query for axis, axis_query in zip(coord_sum, coord)]

    coord_avg = [axis / len(select) for axis in coord_sum]

    locator = cmds.ls(cmds.spaceLocator(name='center_locator')[0], long=True)[0]
    cmds.xform(locator, worldSpace=True, translation=coord_avg)

    return locator


class LocatorInCenterOriented:

    def __init__(self):
        self._selection_list_a = []
        self._selection_list_b = []

    def get_selection_a(self):
        self._selection_list_a = cmds.filterExpand(sm=31)

        if not self._selection_list_a:
            cmds.warning('No Vertices Selection Stored')

    def get_selection_b(self):
        self._selection_list_b = cmds.filterExpand(sm=31)

        if not self._selection_list_b:
            cmds.warning('No Vertices Selection Stored')

    def place_center_locator_oriented(self):
        # Locator A
        coord_sum_a = [0, 0, 0]

        for vtx in self._selection_list_a:
            coord = cmds.xform(vtx, query=True, translation=True, worldSpace=True)
            coord_sum_a = [axis + axis_query for axis, axis_query in zip(coord_sum_a, coord)]

        coord_avg = [axis / len(self._selection_list_a) for axis in coord_sum_a]

        locator_a = cmds.spaceLocator(name='center_locator')[0]
        cmds.xform(locator_a, worldSpace=True, translation=coord_avg)

        # Locator B
        coord_sum_b = [0, 0, 0]

        for vtx in self._selection_list_b:
            coord = cmds.xform(vtx, query=True, translation=True, worldSpace=True)
            coord_sum_b = [axis + axis_query for axis, axis_query in zip(coord_sum_b, coord)]

        coord_avg = [axis / len(self._selection_list_b) for axis in coord_sum_b]

        locator_b = cmds.spaceLocator(name='aim_locator')[0]
        cmds.xform(locator_b, worldSpace=True, translation=coord_avg)

        # Constraint and delete
        aim_constraint = cmds.aimConstraint(locator_b, locator_a, maintainOffset=False)
        cmds.delete(aim_constraint, locator_b)

        return locator_a


class CurveFromPoints:

    def __init__(self):
        self._curve_name = 'from_point_crv'
        self._transform_list = []
        self._point_list = []

    def select_transform_list(self):
        cmds.select(self._transform_list)

    def add_point(self):
        transform_selection = cmds.ls(selection=True)[0]
        transform_position = cmds.xform(transform_selection, query=True, translation=True, worldSpace=True)

        self._point_list.append(transform_position)
        self._transform_list.append(transform_selection)

    def add_point_list(self):
        transform_selection = cmds.ls(selection=True)
        self._transform_list.extend(transform_selection)

        for transform in transform_selection:
            transform_position = cmds.xform(transform, query=True, translation=True, worldSpace=True)
            self._point_list.append(transform_position)

    def create_curve(self):
        # create curve
        bridge_curve = cmds.curve(degree=3, point=self._point_list, name=self._curve_name)
        cmds.rebuildCurve(
            bridge_curve,
            constructionHistory=False,
            replaceOriginal=True,
            rebuildType=0,  # uniform
            endKnots=1,  # uniform end knots
            keepRange=0,  # re-parameterize the resulting curve from 0 to 1
            keepControlPoints=False,
            keepEndPoints=True,
            keepTangents=False,
            spans=0,
            degree=3,
        )
        cmds.delete(bridge_curve, constructionHistory=True)
        self._transform_list = []
        self._point_list = []


class CreateVisibilityAttributes:

    def __init__(self):
        self._visibility_controller = ''
        self._ctrl_list = []
        self._module_dict = {}

    def add_transforms(self):
        pass

    def check_if_guides_deleted(self):
        pass

    def add_visibility_controller(self):
        self._visibility_controller = cmds.ls(selection=True)[0]

    def check_visibility_controller(self):
        # self._visibility_controller = cmds.ls(selection=True)[0]
        self._visibility_controller = 'visibility_C0_ctl'

        if not cmds.objExists(self._visibility_controller):
            print('[{}] Visibility Controls Does Not Exist'.format(self.__class__.__name__))
            cmds.warning('Visibility Controls Does Not Exist')
            return

        node_name = self._visibility_controller

        # List all the visible attributes on the node
        visible_attributes = cmds.listAttr(node_name, keyable=True)

        if visible_attributes:
            for attr in visible_attributes:
                # Lock the attribute
                cmds.setAttr(
                    "{}.{}".format(node_name, attr),
                    lock=True,
                    keyable=False,
                    channelBox=False)
                print('[{}][{}] Attribute Locked: {}'.format(
                    self.__class__.__name__,
                    self.check_visibility_controller.__name__,
                    self._visibility_controller + '.' + attr))

    def list_rig_controls(self):  # Do we need individual ctrl vis attrs? Module vis might be enough
        tag_list = cmds.ls(type='controller')
        exclude_ctrl_list = ['world', 'global', 'local', 'visibility', 'UI']
        print('[{}] Listing Rig Controls:'.format(self.__class__.__name__))

        for tag in tag_list:
            if tag:
                ctrl_list = cmds.listConnections(tag + '.controllerObject')
                if ctrl_list:
                    ctrl = ctrl_list[0]
                    excluded_check = [ctrl_match for ctrl_match in exclude_ctrl_list if ctrl_match in ctrl]
                    if not excluded_check:
                        self._ctrl_list.append(ctrl)
                        print('[{}] {}'.format(self.__class__.__name__, ctrl))
                else:
                    continue
            else:
                continue

    def sort_controls_by_module(self):
        print('[{}] Sorting Modules and Ctrl Types:'.format(self.__class__.__name__))

        for ctrl in self._ctrl_list:
            component_root = cmds.listConnections(ctrl + '.compRoot')[0]
            if component_root not in self._module_dict:
                if '_fk' in ctrl:
                    self._module_dict.update({component_root: {'fk': [ctrl], 'ik': []}})
                if '_ik' in ctrl:
                    self._module_dict.update({component_root: {'fk': [], 'ik': [ctrl]}})
            else:
                if '_fk' in ctrl:
                    self._module_dict[component_root]['fk'].append(ctrl)
                if '_ik' in ctrl:
                    self._module_dict[component_root]['ik'].append(ctrl)

    def sort_ik_fk_controls(self):
        pass

    def create_visibility_attributes(self):
        # Sort keys alphabetically
        sorted_module_dict = sorted(self._module_dict)

        # Lets separate the attributes in ik fk
        for ctrl_role in ['ik', 'fk']:
            # Create the top "label" attribute - ik or fk
            cmds.addAttr(
                self._visibility_controller,
                longName='{}_visibility'.format(ctrl_role),
                niceName="________",
                attributeType="enum",
                enumName=ctrl_role.upper(),
                keyable=True)
            # lock attribute
            cmds.setAttr(
                '{}.{}_visibility'.format(self._visibility_controller, ctrl_role),
                lock=True)

            # Loop through all queried components/modules in the rig
            for component in sorted_module_dict:
                component_attr_name = component.replace('_root', '')
                component_attr_name_role = component_attr_name + '_' + ctrl_role

                cmds.addAttr(
                    self._visibility_controller,
                    longName=component_attr_name_role + '_visibility',
                    niceName=component_attr_name_role,
                    attributeType="bool",
                    min=0,
                    max=1,
                    defaultValue=1,
                    keyable=True)

                for ctrl in self._module_dict[component][ctrl_role]:
                    print('Connecting Attributes: {} -> {}'.format('{}.{}{}'.format(
                        self._visibility_controller, component_attr_name_role, '_visibility'),
                        ctrl + '.visibility'))

                    cmds.setAttr(ctrl + '.visibility', lock=0)
                    cmds.connectAttr(
                        '{}.{}{}'.format(
                            self._visibility_controller,
                            component_attr_name_role, '_visibility'),
                        ctrl + '.visibility',
                        force=True)


def export_ngskintools_weights_selection(file_path=''):

    if not file_path:
        # pop up file dialog and prompt user
        start_dir = cmds.workspace(q=True, rootDirectory=True)
        file_path = cmds.fileDialog2(dialogStyle=2,
                                     fileMode=0,
                                     startingDirectory=start_dir,
                                     fileFilter='Skin Files (*%s)' % '.json')[0]

    file_name_and_extension = file_path.split('/')[-1]
    file_name = file_name_and_extension.split('.')[0]
    dir_path = file_path.replace(file_name_and_extension, '')

    source_geometry = cmds.ls(selection=True)[0]

    output_file_name = os.path.join(dir_path, file_name + '.json')
    ngst_api.export_json(source_geometry, file=output_file_name)


def export_ngskintools_weights_selection_list():  # incomplete - but you get the idea
    """
    mGears skinPack approach might be interesting in this case,
    since we cannot store the data for all meshes into one single file,
    it might be better to create a different file to tell which file belongs to each mesh.

    I feel like this is silly though. Maybe just naming the file the same as the mesh,
    and deriving the import from that.
    :return:
    """
    mesh_list = cmds.ls(selection=True)

    # pop up file dialog and prompt user
    start_dir = cmds.workspace(q=True, rootDirectory=True)
    file_path = cmds.fileDialog2(dialogStyle=2,
                                 fileMode=0,
                                 startingDirectory=start_dir,
                                 fileFilter='Skin Files (*%s)' % '.json')[0]

    for mesh in mesh_list:
        pass
    pass


def import_ngskintools_weights():
    pass


def select_chunks_add_locator(locator_set_name='',
                              selected_vertices=None,
                              num_segments=None,
                              axis=None):
    """
    Select a group of vertices in a mesh and run the script.
    The script will split the vertex selection in segments of the chosen axis,
    and using the bounding box of the vertices in that segment, place a locator
    at the center.
    :param locator_set_name:
    :param selected_vertices:
    :param num_segments:
    :param axis:
    :return:
    """

    locator_list = []

    # Prompt user for required information
    if not selected_vertices:
        selected_vertices = cmds.ls(selection=True, flatten=True)

    if not locator_set_name:
        result = cmds.promptDialog(
            title='Enter Set Name',
            message='Please enter set name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel'
        )

        if result == 'OK':
            # Get the user's input as a string
            locator_set_name = cmds.promptDialog(query=True, text=True)
            print('User entered: {}'.format(locator_set_name))
        else:
            print('Operation canceled.')

    if not axis:
        result = cmds.promptDialog(
            title='Enter axis',
            message='Please enter axis:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel'
        )

        if result == 'OK':
            # Get the user's input as a string
            axis = cmds.promptDialog(query=True, text=True)
            print('User entered: {}'.format(axis))
        else:
            print('Operation canceled.')

    if not num_segments:
        result = cmds.promptDialog(
            title='Enter number of segments',
            message='Please enter number of segments:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel'
        )

        if result == 'OK':
            try:
                # Get the user's input as a string
                user_input = cmds.promptDialog(query=True, text=True)

                # Convert the string to an integer
                num_segments = int(user_input)

                # Now you have the integer in the 'user_int' variable
                print('User entered: {}'.format(num_segments))
            except ValueError:
                print('Invalid input. Please enter an integer.')
        else:
            print('Operation canceled.')

    # Making sure the vertices are indeed selected
    # Otherwise polyEvaluate does not work
    cmds.select(selected_vertices, replace=True)

    # Get the bounding box of the selected vertices
    bbox = cmds.polyEvaluate(boundingBoxComponent=True)

    # Calculate the z-axis range for each segment.
    axis_bbox_dict = {
        'x': bbox[0],
        'y': bbox[1],
        'z': bbox[2]}
    axis_dict = {
        'x': 0,
        'y': 1,
        'z': 2}
    axis_min, axis_max = axis_bbox_dict[axis]
    axis_step = (axis_max - axis_min) / num_segments

    locator_set_group = cmds.group(name='{}_loc_grp'.format(locator_set_name), world=True, empty=True)

    solved_vertices = []
    # Create locators at the middle of each segment.
    for i in range(num_segments):
        # selected_vertices = [vtx for vtx in selected_vertices if vtx not in solved_vertices]
        # clean selected vertices list
        # print(len(selected_vertices))
        # print(selected_vertices)
        # print(len(solved_vertices))

        # Calculate the z-range for the current segment.
        axis_start = axis_min + i * axis_step
        axis_end = axis_start + axis_step
        print('[step] {}'.format(axis_step))

        # Iterate through vertices and apply the Z-axis constraint
        contained_vertices = []
        for n, vtx in enumerate(selected_vertices):
            vtx_position = cmds.pointPosition(vtx, w=True)

            if axis_start <= vtx_position[axis_dict[axis]] <= axis_end:
                contained_vertices.append(vtx)
                solved_vertices.append(vtx)
                # del selected_vertices[n]

        # Get the bounding box of the segment contained vertices
        cmds.select(contained_vertices, replace=True)
        bounding_box = cmds.polyEvaluate(boundingBoxComponent=True)

        # Calculate the center point
        center_x = (bounding_box[0][0] + bounding_box[0][1]) / 2.0
        center_y = (bounding_box[1][0] + bounding_box[1][1]) / 2.0
        center_z = (bounding_box[2][0] + bounding_box[2][1]) / 2.0

        # Create an empty group to represent the center
        center_locator = cmds.ls(cmds.spaceLocator(name="{}_center_locator".format(locator_set_name))[0], long=True)[0]
        locator_list.append(center_locator)

        # Move the center group to the calculated center point
        cmds.xform(
            center_locator,
            translation=(center_x, center_y, center_z),
            worldSpace=True)

        cmds.select(clear=1)
        cmds.parent(center_locator, locator_set_group)

    cmds.select(locator_set_group, replace=True)

    return locator_list


from math import sqrt


def calculate_distance(locator1, locator2):
    # Query the world space position of the first locator
    pos1 = cmds.xform(locator1, query=True, worldSpace=True, translation=True)

    # Query the world space position of the second locator
    pos2 = cmds.xform(locator2, query=True, worldSpace=True, translation=True)

    # Calculate the distance using the Pythagorean theorem
    distance = sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2 + (pos1[2] - pos2[2]) ** 2)

    return distance


def get_to_closest_distance():
    loca = 'locator1000'
    locb = 'locator1001'

    distance_dict = {}

    for i in range(500):
        distance = calculate_distance(loca, locb)

        if distance_dict:
            min_dist = min(distance_dict.keys())
            if distance_dict[min_dist] <= i:
                direction = -1
        else:
            min_dist = distance
            direction = 1

        distance_dict.update({distance: i})
        speed = (distance / 2) * direction

        loca_x = cmds.getAttr(loca + '.translateX')
        locb_x = cmds.getAttr(locb + '.translateX')
        cmds.setAttr(loca + '.translateX', loca_x + speed)
        cmds.setAttr(locb + '.translateX', locb_x + speed)


def get_mirror_vertex_selection():
    """
        Mirror vertex selection using closestPointOnMesh node - not the fastest.
        Use Open Maya 2.0 in the future.
        :return mirror vertex list:
    """
    # Get node names
    selection = cmds.filterExpand(sm=31)
    geo = selection[0].split('.')[0]
    geo_shape = cmds.listRelatives(geo, type='shape')[0]

    # Create closestPointOnMesh node and make connections
    closest_point_node = cmds.createNode("closestPointOnMesh")
    cmds.connectAttr(geo_shape + ".worldMesh[0]", closest_point_node + ".inMesh")

    # Create list
    mirror_vert_list = []

    for vert in selection:
        position = cmds.xform(vert, query=True, translation=True, worldSpace=True)
        cmds.setAttr(closest_point_node + '.inPosition', position[0] * -1, position[1], position[2])

        mirror_vert_index = cmds.getAttr(closest_point_node + ".closestVertexIndex")
        mirror_vert = "{}.vtx[{}]".format(geo, mirror_vert_index)
        mirror_vert_list.append(mirror_vert)

    cmds.select(mirror_vert_list)
    cmds.delete(closest_point_node)

    return mirror_vert_list


class TransferSelection:

    def __init__(self):
        self.source_vtx_list = []
        self.target_mesh = ''

    def load_source_vertex_list(self):
        self.source_vtx_list = cmds.filterExpand(sm=31)

    def load_target_geo(self):
        self.target_mesh = cmds.ls(sl=True)[0]

    def transfer_selection(self):
        selection_transfer_closest_point(self.source_vtx_list, self.target_mesh)


def selection_transfer_closest_point(source_geo_vtx_list, target_geo):
    """
    Transfers selection from mesh A to mesh B based on the closest point
    to each vertex.
    :return:
    """
    # Get node names
    source_vtx_list_expanded = cmds.filterExpand(source_geo_vtx_list, sm=31)
    source_geo = source_vtx_list_expanded[0].split('.')[0]
    source_geo_shape = cmds.listRelatives(source_geo, type='shape')[0]

    # Create closestPointOnMesh node and make connections
    target_geo_shape = cmds.listRelatives(target_geo, type='shape')[0]
    closest_point_node = cmds.createNode("closestPointOnMesh")
    cmds.connectAttr(target_geo_shape + ".worldMesh[0]", closest_point_node + ".inMesh")

    # Create list
    closest_vert_list = []

    for vert in source_vtx_list_expanded:
        position = cmds.xform(vert, query=True, translation=True, worldSpace=True)
        cmds.setAttr(closest_point_node + '.inPosition', position[0], position[1], position[2])

        closest_vert_index = cmds.getAttr(closest_point_node + ".closestVertexIndex")
        closest_vert = "{}.vtx[{}]".format(target_geo, closest_vert_index)
        closest_vert_list.append(closest_vert)

    cmds.select(closest_vert_list)
    cmds.delete(closest_point_node)


def mgear_select_guide_children():
    guide_parent = cmds.ls(selection=True)[0]
    all_children_list = cmds.listRelatives(guide_parent, children=True, allDescendents=True, type='transform')
    guide_children_list = [control for control in all_children_list if control.endswith(('_loc', '_root'))]
    guide_children_list.append(guide_parent)
    guide_children_list.reverse()

    cmds.select(clear=True)
    cmds.select(guide_children_list)

    print('[mgear_guide_guide_children] Guide hierarchy selected: {}'.format(guide_children_list))

    return guide_children_list


def assign_random_colors_to_geometry():
    # Get the currently selected geometries
    selected_geometries = cmds.ls(selection=True, dag=True, type='mesh')

    for geo in selected_geometries:
        # Create a new shader
        shader_name = cmds.shadingNode('lambert', asShader=True)
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)

        # Connect the shader to the shading group
        cmds.connectAttr('{}.outColor'.format(shader_name), '{}.surfaceShader'.format(shading_group), force=True)

        # Assign a random color to the shader
        random_color = [random.random(), random.random(), random.random()]
        cmds.setAttr('{}.color'.format(shader_name), *random_color, type='double3')

        # Assign the shading group to the geometry
        cmds.sets(geo, edit=True, forceElement=shading_group)


