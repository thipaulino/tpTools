import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim

import tpRig.tpRigBuilder.tpModule as tpModule
import tpRig.tpRigUtils as tpUtils
reload(tpUtils)
import tpRig.tpControl.tpControl as tpCtrl
reload(tpCtrl)


class Utilities:

    def __init__(self):

        self.__selection_list = None
        self.__curve_selection = None

        self.control_object_dict = {}  # data structure: {control_name: control_object}

        self.head_model_geo = 'head_model_geo'  # why is this not variable?
        self.head_model_geo_grp = 'head_model_geo_grp'  # why not variable?

    # utilities methods
    def load_selection_list(self):
        self.__selection_list = mc.ls(selection=True)
        print(self.__selection_list)

    def lead_selection(self):
        pass

    def mirror_skeleton_joint_list(self):
        """
        Select start of chain to mirror and run.
        :return:
        """
        if self.__selection_list:
            for joint in self.__selection_list:
                mc.mirrorJoint(joint,
                               mirrorYZ=True,
                               mirrorBehavior=True,
                               searchReplace=['l_', 'r_'])
        else:
            print('[mirror_skeleton_joint_list] No Item List Loaded')

    def place_in_center_of_vertex_list(self):
        """
        Finds the center coordinate of vertex selection.

        :instructions:
        Select vertex or object to average position and run 'load selection list'
        Select object to be placed and run this method (Place Selection in Average Center)

        :return Vertex selection average:
        """
        if self.__selection_list:
            select = mc.filterExpand(self.__selection_list, sm=31)
            coord_sum = [0, 0, 0]

            for i in select:
                coord = mc.xform(i, q=1, t=1, ws=1)
                coord_sum = [axis + axis_query for axis, axis_query in zip(coord_sum, coord)]

            coord_avg = [axis / len(select) for axis in coord_sum]

            mc.xform(mc.ls(selection=True)[0],
                     worldSpace=True,
                     translation=coord_avg)

        else:
            print('[mirror_skeleton_joint_list] No Item List Loaded')

    def load_curve_selection(self):
        """
        Load single curve into variable
        :return:
        """
        self.__curve_selection = mc.ls(selection=True)[0]

        print(self.__curve_selection)

    def create_curve_from_selection_list(self):
        pass

    def create_curve_from_a_to_b(self):
        """
        Select two joints(points/objects) and run
        :return:
        """
        point_a, point_b = mc.ls(selection=True)
        curve = tpUtils.curve_from_a_to_b(point_a, point_b, name='temp_a_to_b')

        print(curve)
        return curve

    def distribute_items_on_curve(self, reverse=False):
        """
        :instructions:
        Select curve to be used for distribution and load.
        Select objects to be distributed on the curve and run this function.

        :param reverse:
        :return:
        """

        if not self.__curve_selection:
            print('Please Load Curve Selection')
            return

        items_selection = mc.ls(selection=True)
        items_len = len(items_selection)

        curve_step = 100 / (items_len - 1.0) / 100

        for index, item in enumerate(items_selection):
            current_step = curve_step * index
            point_on_curve = mc.pointOnCurve(self.__curve_selection,
                                             parameter=current_step,
                                             position=True)

            mc.xform(item, translation=point_on_curve, worldSpace=True)

    def distribute_joints_between_selection(self):
        pass

    # def import_all_shapes(self):
    #     tpUtils.import_shapes(self.project_dir_dict['blend_shapes'])

    def blend_shape_add_targets(self):
        """
        Add blendShape targets from imported geometry .mb file
        Method created specifically for Bob project, please check out hierarchy structure
        on bob blendShape template geo file.
        :return:
        """
        blend_shape_geo_grp = 'blend_shape_template_geo_grp'
        shapes_grp_list = mc.listRelatives(blend_shape_geo_grp, children=True, type='transform')
        head_model_grp_children = mc.listRelatives(self.head_model_geo_grp, children=True, type='transform')

        for index, shape_group in enumerate(shapes_grp_list):
            shape_group_children = mc.listRelatives(shape_group, children=True, type='transform')

            for shape in shape_group_children:
                for head_element_geo in head_model_grp_children:
                    if head_element_geo in shape:
                        if index == 0:
                            mc.blendShape(shape, head_element_geo,
                                          name='{}_blendShape_node'.format(head_element_geo.replace('_geo', '')))
                        else:
                            item_history_list = mc.listHistory(head_element_geo)
                            blendshape_node = mc.ls(item_history_list, type='blendShape')[0]
                            blendshape_weights_list = mc.blendShape(blendshape_node, q=True, weight=True)
                            blendshape_weights_len = len(blendshape_weights_list)

                            mc.blendShape(blendshape_node,
                                          edit=True,
                                          target=(head_element_geo,
                                                  blendshape_weights_len,
                                                  shape,
                                                  1.0))

    def connect_blend_shapes_control(self):
        """
        There is one blendShape node for each geo element of the head ex. head, eyes, eyelashes etc...
        All geo elements blendShape node has a corresponding
        Connects targets on head blendShape node to corresponding targets in all other geometry elements

        :return:
        """
        blendshape_geo_grp = 'blend_shape_template_geo_grp'
        blendshape_geo_grp_children = mc.listRelatives(blendshape_geo_grp, children=True)
        # using the imported blendShape geo grp names to recall pose name
        pose_name_list = [pose_grp.replace('_grp', '') for pose_grp in blendshape_geo_grp_children]

        # declaring information about the output model geo
        # the one receiving blendShapes
        model_geo = 'head_model_geo'
        model_geo_name_list = model_geo.split('_')
        model_geo_grp = 'head_model_geo_grp'
        model_geo_grp_children = mc.listRelatives(model_geo_grp, children=True)

        main_blendshape_node = 'head_model_blendShape_node'
        main_blendshape_weight_list = mc.blendShape(main_blendshape_node, q=True, weight=True)
        main_blendshape_target_name_list = [mc.aliasAttr('{}.w[{}]'.format(main_blendshape_node, weight), q=True)
                                            for weight in range(len(main_blendshape_weight_list))]
        main_blnd_relationship_dict = {}

        # looping through pose names to find a match in head geo blendShape targets
        for pose_name in pose_name_list:
            # the name of the target is composed of the pose + geo name
            # splitting both pose name and geo name and suming into single list
            pose_name_split_list = pose_name.split('_')
            all_names_list = pose_name_split_list + model_geo_name_list

            # Looping through head geo targets
            for main_target_name in main_blendshape_target_name_list:
                if pose_name in main_target_name:
                    # splitting current target name
                    main_target_name_list = main_target_name.split('_')

                    # removing all names that match on the target name
                    # getting either an empty list, or a list with names left
                    for name in all_names_list:
                        if name in main_target_name_list:
                            main_target_name_list.remove(name)

                    # if there is nothing left on the list, the names match
                    # target gets added to dict
                    if not main_target_name_list:
                        main_blnd_relationship_dict.update({pose_name: main_target_name})

        for model_geo_element in model_geo_grp_children:
            if model_geo_element != model_geo:
                element_name_list = model_geo_element.split('_')
                element_history_list = mc.listHistory(model_geo_element)

                blendshape_node = mc.ls(element_history_list, type='blendShape')[0]
                blendshape_weight_list = mc.blendShape(blendshape_node, q=True, weight=True)
                blendshape_target_name_list = [mc.aliasAttr('{}.w[{}]'.format(blendshape_node, weight), q=True)
                                               for weight in range(len(blendshape_weight_list))]

                for pose_name in pose_name_list:
                    pose_name_split_list = pose_name.split('_')
                    for target_name in blendshape_target_name_list:
                        target_name_list = target_name.split('_')
                        all_names_list = pose_name_split_list + element_name_list

                        if pose_name in target_name:
                            for name in all_names_list:
                                if name in target_name_list:
                                    target_name_list.remove(name)

                            if not target_name_list:
                                mc.connectAttr('{}.{}'.format(main_blendshape_node,
                                                              main_blnd_relationship_dict[pose_name]),
                                               '{}.{}'.format(blendshape_node, target_name), force=True)

    def connect_eye_shapes_to_controls(self):
        """
        The method purpose is to connect the eye look blendShape targets
        to the eye look controls via setDrivenKey
        :return:
        """
        eyes_targets_data_set = {
            'eyes_lookLeft_geo': {
                'angle': 30.0,
                'attribute': 'rotateZ'},
            'eyes_lookRight_geo': {
                'angle': -30.0,
                'attribute': 'rotateZ'},
            'eyes_lookUp_geo': {
                'angle': -22.639,
                'attribute': 'rotateY'},
            'eyes_lookDown_geo': {
                'angle': 28.677,
                'attribute': 'rotateY'}
        }

        blend_shape_node = 'head_model_geo_bld_node'
        control_name = 'eye_center_ctrl'

        for side in 'lr':
            for target in eyes_targets_data_set:
                # set control rotation to 0
                mc.setAttr(
                    '{side}_{control}.{attr}'.format(
                        side=side,
                        control=control_name,
                        attr=eyes_targets_data_set[target]['attribute']),
                    0)
                # set blendShape target weight to 0
                mc.setAttr('{}.{}_{}'.format(blend_shape_node, side, target), 0)
                # set first driven key at 0
                mc.setDrivenKeyframe(
                    '{}.{}_{}'.format(blend_shape_node, side, target),
                    currentDriver='{}_{}.{}'.format(
                        side,
                        control_name,
                        eyes_targets_data_set[target]['attribute']),
                    inTangentType='linear',
                    outTangentType='linear'
                )

                # set control rotation to angle in dictionary
                mc.setAttr(
                    '{side}_{control}.{attr}'.format(
                        side=side,
                        control=control_name,
                        attr=eyes_targets_data_set[target]['attribute']),
                    eyes_targets_data_set[target]['angle'])
                # set blendShape target to 1
                mc.setAttr('{}.{}_{}'.format(blend_shape_node, side, target), 1)
                # set driven key at value in dictionary
                mc.setDrivenKeyframe(
                    '{}.{}_{}'.format(blend_shape_node, side, target),
                    currentDriver='{}_{}.{}'.format(
                        side,
                        control_name,
                        eyes_targets_data_set[target]['attribute']),
                    inTangentType='linear',
                    outTangentType='linear'
                )

                # set control rotation to 0
                mc.setAttr(
                    '{side}_{control}.{attr}'.format(
                        side=side,
                        control=control_name,
                        attr=eyes_targets_data_set[target]['attribute']),
                    0)
                # set blendShape target weight to 0
                mc.setAttr('{}.{}_{}'.format(blend_shape_node, side, target), 0)

    def om_export_skin_weights(self,
                               geo_list=None,
                               dir_path=None,
                               file_name=None):
        """
        Open Maya method to export skin cluster weights from geometry list.
        If no list is provided, selection will be used to query the list.
        if no dir_path id provided, the method will prompt the user with a dialog to specify the path.

        :param geo_list:
        :param dir_path:
        :param file_name:
        :return:
        """
        # skinCluster node name
        if not geo_list:
            geo_list = mc.ls(selection=True)

        if not dir_path:
            # pop up file dialog and prompt user
            start_dir = mc.workspace(q=True, rootDirectory=True)
            file_path = mc.fileDialog2(dialogStyle=2,
                                       fileMode=0,
                                       startingDirectory=start_dir,
                                       fileFilter='Skin Files (*%s)' % '.json')[0]

            file_name_and_extension = file_path.split('/')[-1]
            file_name = file_name_and_extension.split('.')[0]
            dir_path = file_path.replace(file_name_and_extension, '')

        skin_data = {}

        for geometry in geo_list:
            skin_cluster_node = mel.eval('findRelatedSkinCluster "{}"'.format(geometry))

            if not skin_cluster_node:
                continue

            # defining the data dictionary
            data = {
                'weights': {},
                'blendWeights': [],
                'name': skin_cluster_node,
            }

            # get skinCluster MObject
            selection_list = OpenMaya.MSelectionList()
            selection_list.add(skin_cluster_node)
            m_object = OpenMaya.MObject()
            selection_list.getDependNode(0, m_object)
            fn_skin_cluster = OpenMayaAnim.MFnSkinCluster(m_object)

            # get dagPath and member components of skinned shape
            fn_set = OpenMaya.MFnSet(fn_skin_cluster.deformerSet())
            members = OpenMaya.MSelectionList()
            fn_set.getMembers(members, False)
            dag_path = OpenMaya.MDagPath()
            components = OpenMaya.MObject()
            members.getDagPath(0, dag_path, components)

            # get current skinCluster weights
            weights = OpenMaya.MDoubleArray()
            util = OpenMaya.MScriptUtil()
            util.createFromInt(0)
            p_u_int = util.asUintPtr()
            fn_skin_cluster.getWeights(dag_path, components, weights, p_u_int)

            # assemble final dictionary to export
            influence_paths = OpenMaya.MDagPathArray()
            num_influences = fn_skin_cluster.influenceObjects(influence_paths)
            num_components_per_influence = weights.length() / num_influences

            for ii in range(influence_paths.length()):
                influence_name = influence_paths[ii].partialPathName()

                data['weights'][influence_name] = \
                    [weights[jj * num_influences + ii] for jj in range(num_components_per_influence)]

            # add blend weights to dictionary
            blend_weights = OpenMaya.MDoubleArray()
            fn_skin_cluster.getBlendWeights(dag_path, components, blend_weights)
            data['blendWeights'] = [blend_weights[i] for i in range(blend_weights.length())]

            skin_data.update({geometry: data})

        tpUtils.export_dict_as_json(skin_data, file_name, dir_path)

    def om_import_skin_weights(self, dir_path=None, file_name=None):
        """
        Open Maya Method.
        General import skin weights method.
        If no directory and file name is provided, the script will prompt the user with a file dialog.

        :param dir_path:
        :param file_name:
        :return:
        """

        if dir_path and file_name:
            import_path_file = '{}{}.json'.format(dir_path, file_name)

        else:
            # pop up file dialog and prompt user
            start_dir = mc.workspace(q=True, rootDirectory=True)

            import_path_file_list = mc.fileDialog2(
                dialogStyle=2,
                fileMode=1,
                startingDirectory=start_dir,
                fileFilter='Skin Files (*.json)')

            if not import_path_file_list:
                print('[OM Import Skin Weights] No file was selected')
                return

            import_path_file = import_path_file_list[0]

        # defining the data dictionary
        skin_weights_file_data = tpUtils.read_json_file(import_path_file)

        for geo_name in skin_weights_file_data:
            geo_skin_data = skin_weights_file_data[geo_name]
            node = geo_skin_data['name']
            joints = geo_skin_data['weights'].keys()
            mc.skinCluster(joints,
                           geo_name,
                           toSelectedBones=True,
                           normalizeWeights=2,  # interactive
                           name=geo_skin_data['name'])

            # get skinCluster MObject
            selection_list = OpenMaya.MSelectionList()
            selection_list.add(node)
            m_object = OpenMaya.MObject()
            selection_list.getDependNode(0, m_object)
            fn = OpenMayaAnim.MFnSkinCluster(m_object)

            # get geometry components
            fn_set = OpenMaya.MFnSet(fn.deformerSet())
            members = OpenMaya.MSelectionList()
            fn_set.getMembers(members, False)
            dag_path = OpenMaya.MDagPath()
            components = OpenMaya.MObject()
            members.getDagPath(0, dag_path, components)

            # get current weights
            weights = OpenMaya.MDoubleArray()
            util = OpenMaya.MScriptUtil()
            util.createFromInt(0)
            p_u_int = util.asUintPtr()
            fn.getWeights(dag_path, components, weights, p_u_int)

            influence_paths = OpenMaya.MDagPathArray()
            num_influences = fn.influenceObjects(influence_paths)
            num_components_per_influence = weights.length() / num_influences

            # Keep track of which imported influences aren't used
            unused_imports = []

            # Keep track of which existing influences don't get anything imported
            no_match = [influence_paths[ii].partialPathName() for ii in range(influence_paths.length())]

            for imported_influence, imported_weights in geo_skin_data['weights'].items():
                for joint_index in range(influence_paths.length()):
                    influence_name = influence_paths[joint_index].partialPathName()

                    if influence_name == imported_influence:
                        # Store the imported weights into the MDoubleArray
                        for jj in range(num_components_per_influence):
                            weights.set(imported_weights[jj], jj * num_influences + joint_index)
                        no_match.remove(influence_name)
                        break
                    else:
                        unused_imports.append(imported_influence)

            influence_indices = OpenMaya.MIntArray(num_influences)

            for influence_index in range(num_influences):
                influence_indices.set(influence_index, influence_index)

            fn.setWeights(dag_path, components, influence_indices, weights, False)

            # import blend weights
            blend_weights = OpenMaya.MDoubleArray(len(skin_weights_file_data[geo_name]['blendWeights']))
            for i, w in enumerate(skin_weights_file_data[geo_name]['blendWeights']):
                blend_weights.set(w, i)

            fn.setBlendWeights(dag_path, components, blend_weights)

    def create_fk_controls(self):
        """
        Select root joint of FK chain and run function.
        :return:
        """

        fk_joint_root = mc.ls(sl=1)[0]
        fk_joint_children = mc.listRelatives(fk_joint_root, allDescendents=True, children=True)
        fk_joint_list = [fk_joint_root] + fk_joint_children

        control_hierarchy_dict = {}
        root_ctrl = None

        for jnt in fk_joint_list:
            ctrl_name = jnt.replace('_jnt', '_ctrl')
            control = tpCtrl.Control(name=ctrl_name)
            self.control_object_dict.update({ctrl_name: control})

            control.add_offset_grp()
            control.top_group_match_position(jnt, t=True, r=True)

            parent_jnt = mc.listRelatives(jnt, parent=True)

            if parent_jnt:
                parent_control = parent_jnt[0].replace('jnt', 'ctrl')
                control_hierarchy_dict.update({control: parent_control})

            if not parent_jnt:
                root_ctrl = control

        for ctrl in control_hierarchy_dict:
            mc.parent(ctrl.get_top_group(), control_hierarchy_dict[ctrl])
            ctrl.constraint_target(ctrl.get_name().replace('ctrl', 'jnt'), mo=True)

        root_ctrl.constraint_target(fk_joint_root, mo=True)


# top_level_action should be changed to str
# should be only the name of the parent action or root
# top item action would be created inside of this function
def build_module_object(module_name='Utilities', parent_action_name='root', background_color=None):
    utils_object = Utilities()

    utils_module_object = tpModule.Module(module_name, parent_action_name, background_color=background_color)

    action_list = [
        tpModule.Action('Load Selection List', module_name, utils_object.load_selection_list),
        tpModule.Action('Mirror Joint List', module_name, utils_object.mirror_skeleton_joint_list),
        tpModule.Action('Place Selection in Vertex Average Center', module_name,
                        utils_object.place_in_center_of_vertex_list),
        # tpModule.Action('Import Blend Shapes FBX', 'Pre-Build Utils', utils_object.import_all_shapes),
        tpModule.Action('Add BlendShape Targets', module_name, utils_object.blend_shape_add_targets),
        tpModule.Action('Connect BlendShape Controls', module_name, utils_object.connect_blend_shapes_control),
        tpModule.Action('Create Curve From A to B', module_name, utils_object.create_curve_from_a_to_b),
        tpModule.Action('Curve Distribute Tools', module_name),
        tpModule.Action('Load Curve Selection', 'Curve Distribute Tools', utils_object.load_curve_selection),
        tpModule.Action('Distribute Selection On Curve', 'Curve Distribute Tools',
                        utils_object.distribute_items_on_curve),
        tpModule.Action('Connect Eye Shapes To Controls', module_name,
                        utils_object.connect_eye_shapes_to_controls),
        tpModule.Action('Create FK Controls', module_name, utils_object.create_fk_controls)
    ]

    utils_module_object.add_action_list(action_list)

    return utils_module_object

