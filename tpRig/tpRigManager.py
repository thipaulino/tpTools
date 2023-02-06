import os
import glob

import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim

import tpControl
import tpRig.tpRigUtils as tpUtils
reload(tpUtils)
import tpRig.tpControl.tpControl as tpCtrl
reload(tpCtrl)

# Modules import section
import tpRig.tpFaceRig.tpMouth.tpMouthMuscle as tpMouthMuscle
import tpRig.tpFaceRig.tpMouth.tpMouthOutput as tpMouthOutput


class Buildable(object):

    def __init__(self):

        self.build_methods_list = []
        self.top_level_item = 'FaceRig'

        self.register_build_method('Pre-Build Utils', 'root', background_color='dark_magenta')
        self.register_build_method(self.top_level_item, 'root', background_color='dark_cyan')
        self.register_build_method('Post Build Utils', 'root', background_color='dark_green')

        # when item no parent and no method is added in register, code is breaking - improve

    def register_build_method(self,
                              action_name,
                              parent_action,
                              method=None,
                              after=None,
                              background_color=None):
        """
        Data Structure
        [{'method_name': method_name,
        'parent': parent_action_name,
        'method': self.method,
        'after': method_name to be placed after},
        {...}]

        :param action_name:
        :param parent_action:
        :param method:
        :param after:
        :param background_color:
        :return:
        """
        method_data = {
            'method_name': action_name,
            'parent': parent_action,
            'method': method,
            'after': after,
            'background_color': background_color,
            'stop_flag': False}

        self.build_methods_list.append(method_data)


class Project(Buildable):

    def __init__(self):
        super(Project, self).__init__()

        self.__user_input = None
        self.project_root_path = mc.workspace(query=True, rootDirectory=True)

        self.project_dir_dict_list = [  # holds entry order
            {'root': self.project_root_path},

            {'scripts': os.path.join(self.project_root_path, 'scripts/')},
            {'data': os.path.join(self.project_root_path, 'data/')},
            {'control_shape': os.path.join(self.project_root_path, 'data/control_shape/')},
            {'blend_shape_data': os.path.join(self.project_root_path, 'data/blend_shape/')},

            {'geo_root': os.path.join(self.project_root_path, 'assets/geo/')},
            {'model_geo': os.path.join(self.project_root_path, 'assets/geo/model/')},
            {'template_geo': os.path.join(self.project_root_path, 'assets/geo/template/')},
            {'system_geo': os.path.join(self.project_root_path, 'assets/geo/system/')},
            {'blend_shapes': os.path.join(self.project_root_path, 'assets/geo/blend_shapes/')},

            {'rig': os.path.join(self.project_root_path, 'assets/rig/')},
            {'rig_system': os.path.join(self.project_root_path, 'assets/rig/system/')},
            {'rig_template': os.path.join(self.project_root_path, 'assets/rig/template/')},
            {'rig_skeleton': os.path.join(self.project_root_path, 'assets/rig/skeleton/')},

            {'skin_clusters_root': os.path.join(self.project_root_path, 'data/skin_clusters/')},
            {'skin_clusters_model': os.path.join(self.project_root_path, 'data/skin_clusters/model/')},
            {'skin_clusters_template': os.path.join(self.project_root_path, 'data/skin_clusters/template/')},
            {'skin_clusters_system': os.path.join(self.project_root_path, 'data/skin_clusters/system/')},

            {'shader_maya': os.path.join(self.project_root_path, 'data/shader/maya_standard/')},
            {'shader_arnold': os.path.join(self.project_root_path, 'data/shader/arnold/')}
        ]

        self.project_dir_dict = {}
        for dir_data in self.project_dir_dict_list:
            self.project_dir_dict.update(dir_data)

        self.project_data_file_dict = {
            'model_geo_skin_weights': 'model_geo_skin_weights',
            'template_geo_skin_weights': 'template_geo_skin_weights',
            'system_geo_skin_weights': 'system_geo_skin_weights',
            'control_shape': 'control_shape_data'
        }

        self.not_found_dir_dict = []

        self.register_build_method('Check Project', self.top_level_item)
        self.register_build_method('Print All Directory Paths', 'Check Project',
                                   method=self._print_all_dir_paths)
        self.register_build_method('Check Directories Existence', 'Check Project',
                                   method=self._check_existence)
        self.register_build_method('Prompt User', 'Check Project',
                                   method=self._prompt_user_about_missing_dir)
        self.register_build_method('Create Missing Directories', 'Check Project',
                                   method=self._create_missing_directories)

    def _print_all_dir_paths(self):
        for dir_data in self.project_dir_dict_list:
            print('[{}] {}'.format(dir_data.keys()[0], dir_data.values()[0]))

        print('\n')

    def _check_existence(self):
        for dir_data in self.project_dir_dict_list:
            if not os.path.exists(dir_data.values()[0]):
                self.not_found_dir_dict.append({dir_data.keys()[0]: dir_data.values()[0]})

                print('[{}] Path Nonexistent'.format(dir_data.keys()[0], dir_data.values()[0]))

        if not self.not_found_dir_dict:
            print('\n')

    def _prompt_user_about_missing_dir(self):
        missing_dir_name_list = [dir_data.keys()[0] for dir_data in self.not_found_dir_dict]

        if missing_dir_name_list:
            self.__user_input = mc.confirmDialog(
                title='Check Project: Create Directories?',
                message='Missing Directories: {}'.format(missing_dir_name_list),
                button=['Yes', 'No'],
                defaultButton='Yes',
                cancelButton='No',
                dismissString='No')
        else:
            print('[Check Project] No Missing Directories \n')

    def _create_missing_directories(self):
        directory_list = [dir_data.values()[0] for dir_data in self.not_found_dir_dict]

        if self.__user_input:
            if self.__user_input == 'Yes':
                for directory in directory_list:
                    os.mkdir(directory)

        print('[Create Missing Project Directories] Done \n')

    def check_for_template_data(self):
        pass

    def check_for_template_geo(self):
        pass

    def check_for_model_geo(self):
        pass


class Utilities(Project):

    def __init__(self):
        super(Utilities, self).__init__()

        self.__selection_list = None
        self.__curve_selection = None

        self.head_model_geo = 'head_model_geo'
        self.head_model_geo_grp = 'head_model_geo_grp'

        self.register_build_method('Load Selection List', 'Pre-Build Utils', self.load_selection_list)
        self.register_build_method('Mirror Joint List', 'Pre-Build Utils', self.mirror_skeleton_joint_list)
        self.register_build_method('Place Selection in Vertex Average Center', 'Pre-Build Utils',
                                   self.place_in_center_of_vertex_list)

        self.register_build_method('Import Blend Shapes FBX', 'Pre-Build Utils', self.import_all_shapes)
        self.register_build_method('Add BlendShape Targets', 'Pre-Build Utils', self.blend_shape_add_targets)
        self.register_build_method('Connect BlendShape Controls', 'Pre-Build Utils', self.connect_blend_shapes_control)
        self.register_build_method('Create Curve From A to B', 'Pre-Build Utils', self.create_curve_from_a_to_b)

        self.register_build_method('Curve Distribute Tools', 'Pre-Build Utils')
        self.register_build_method('Load Curve Selection', 'Curve Distribute Tools', self.load_curve_selection)
        self.register_build_method('Distribute Selection On Curve',
                                   'Curve Distribute Tools', self.distribute_items_on_curve)
        self.register_build_method('Connect Eye Shapes To Controls', 'Pre-Build Utils',
                                   self.connect_eye_shapes_to_controls)

        self.register_build_method('Create FK Controls', 'Pre-Build Utils', self.create_fk_controls)

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

    def import_all_shapes(self):
        import_shapes(self.project_dir_dict['blend_shapes'])

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

        control_dict = {}
        root_ctrl = None

        for jnt in fk_joint_list:
            ctrl_name = jnt.replace('_jnt', '')
            control = tpCtrl.Control(name=ctrl_name + '_ctrl')

            control.add_offset_grp()
            control.top_group_match_position(jnt, t=True, r=True)

            parent_jnt = mc.listRelatives(jnt, parent=True)

            if parent_jnt:
                parent_control = parent_jnt[0].replace('jnt', 'ctrl')
                control_dict.update({control: parent_control})

            if not parent_jnt:
                root_ctrl = control

        for ctrl in control_dict:
            mc.parent(ctrl.get_top_group(), control_dict[ctrl])
            ctrl.constraint_target(ctrl.get_name().replace('ctrl', 'jnt'), mo=True)

        root_ctrl.constraint_target(fk_joint_root, mo=True)


class tpRig(Utilities):

    def __init__(self):
        super(tpRig, self).__init__()

        self.maya_project_directory = ''
        self.skin_weights_directory = ''

        self.skeleton_base_ctrl_object_dict = {}
        self.control_object_dict = {}

        self.group_hierarchy_dict = {
            'root': 'root',
            'geometry': 'geometry_grp',
            'model_geometry': 'model_geo_grp',
            'template_geometry': 'template_geo_grp',
            'rig': 'rig_grp',
            'control_group': 'control_grp',
            'rig_template': 'rig_template_grp',
            'skeleton': 'skeleton_grp',
            'module': 'module_grp'
        }

        self.system_mesh_weight_dict = {}

        # self.build_manager = BuildMethodsManager()

        self.register_build_method('Create New Scene', self.top_level_item, self._create_new_scene)
        self.register_build_method('Setup Rig Groups', self.top_level_item, self._setup_rig_groups)
        self.register_build_method('Add Top Group Attributes', self.top_level_item, self._add_top_group_attributes)

        self.register_build_method('Import Rig Items', self.top_level_item)
        self.register_build_method('Import Skeleton', 'Import Rig Items', self._import_rig_skeleton)
        self.register_build_method('Import Rig Template', 'Import Rig Items', self._import_rig_template)
        self.register_build_method('Import Template Geo', 'Import Rig Items', self._import_template_geo)
        self.register_build_method('Import Model Geo', 'Import Rig Items', self._import_model_geo)

        self.register_build_method('Create Global Control', self.top_level_item, self._create_global_control)
        self.register_build_method('Add Skeleton Base Controls', self.top_level_item, self._add_controls_to_skeleton)
        self.register_build_method('Constraint Skeleton to Base Controls', self.top_level_item,
                                   self._constraint_skeleton_to_base_controls)
        self.register_build_method('Build Face Controls', self.top_level_item, self._build_face_controls)
        self.register_build_method('Create Face BlendShape Node', self.top_level_item,
                                   self._create_face_blend_shape_node)
        self.register_build_method('Connect Eye Shapes to Controls', self.top_level_item,
                                   self._connect_eye_shapes_to_controls)
        self.register_build_method('Connect Face Controls to Targets', self.top_level_item,
                                   self._connect_face_controls_to_blend_shape_targets)

        self.register_build_method('Create Neck Module', self.top_level_item, self._create_neck_module)

        self.register_build_method('Import Control Shapes', self.top_level_item, self._import_control_shapes)

        self.register_build_method('Build Mouth Muscle Module', self.top_level_item, self._build_mouth_muscle_module)
        self.register_build_method('Build Mouth Output Module', self.top_level_item, self._build_mouth_output_module)
        # self.register_build_method('Build Modules', self.top_level_item, self._setup_modules)

        self.register_build_method('Import Deformer Weights', self.top_level_item)
        self.register_build_method('Import Model Geo Skin Weights', 'Import Deformer Weights',
                                   self._om_import_model_geo_skin_weights)
        self.register_build_method('Import Template Geo Skin Weights', 'Import Deformer Weights',
                                   self._om_import_template_geo_skin_weights)
        self.register_build_method('Import System Geo Skin Weights', 'Import Deformer Weights',
                                   self._om_import_system_geo_skin_weights)

        self.register_build_method('Camera View Fit', self.top_level_item, self._camera_fit_view)

    def get_registered_build_methods(self):
        return self.build_methods_list

    # build methods
    def _create_new_scene(self):
        """
        Creates new empty Maya scene.
        :return:
        """
        mc.file(new=True, force=True)
        print('[Create New Scene] Method Done')

    def _setup_rig_groups(self):
        """
        Creates the rig group hierarchy in the scene.

        Note From Rafael Vitoratti: Use cmds.createNode('trnsform', parent='prarentGroup')
        that will create the group node already parented
        :return:
        """
        # create top group
        root_group = mc.group(name=self.group_hierarchy_dict['root'], empty=True)

        # geometry groups
        geo_group = mc.group(name=self.group_hierarchy_dict['geometry'], empty=True)
        model_geo_group = mc.group(name=self.group_hierarchy_dict['model_geometry'], empty=True)
        template_geo_group = mc.group(name=self.group_hierarchy_dict['template_geometry'], empty=True)
        mc.parent(template_geo_group, model_geo_group, geo_group)

        # rig groups
        rig_group = mc.group(name=self.group_hierarchy_dict['rig'], empty=True)
        control_group = mc.group(name=self.group_hierarchy_dict['control_group'], empty=True)
        skeleton_group = mc.group(name=self.group_hierarchy_dict['skeleton'], empty=True)
        rig_template_group = mc.group(name=self.group_hierarchy_dict['rig_template'], empty=True)
        mc.parent(control_group, skeleton_group, rig_template_group, rig_group)

        module_group = mc.group(name=self.group_hierarchy_dict['module'], empty=True)

        mc.parent(geo_group, rig_group, module_group, root_group)

    def _add_top_group_attributes(self):
        """
        Add visibility attributes to top group node.
        :return:
        """
        pass

    def _import_rig_template(self):
        """
        Imports the template skeleton joints into the scene
        :return:
        """
        import_file_list = glob.glob('{}*.mb'.format(self.project_dir_dict['rig_template']))

        for file in import_file_list:
            file_geo_list = import_and_return_node_type(file_path=file, node_type='joint')

            # find unique top parent nodes and append
            top_node_list = get_top_hierarchy_node(file_geo_list)
            mc.parent(top_node_list, self.group_hierarchy_dict['rig_template'])

    def _import_template_geo(self):
        """
        Imports template geometry maya files into the scene from template_geo folder
        in project folder.
        :return:
        """
        import_file_list = glob.glob('{}*.mb'.format(self.project_dir_dict['template_geo']))

        for file in import_file_list:
            file_geo_list = import_and_return_node_type(file_path=file, node_type='transform')

            # find unique top parent nodes and append
            top_node_list = get_top_hierarchy_node(file_geo_list)
            mc.parent(top_node_list, self.group_hierarchy_dict['template_geometry'])

    def _import_model_geo(self):
        """
        Imports template geometry maya files into the scene from template_geo folder
        in project folder.
        :return:
        """
        import_file_list = glob.glob('{}*.mb'.format(self.project_dir_dict['model_geo']))

        for file in import_file_list:
            file_geo_list = import_and_return_node_type(file_path=file, node_type='transform')

            top_node_list = get_top_hierarchy_node(file_geo_list)
            mc.parent(top_node_list, self.group_hierarchy_dict['model_geometry'])

    def _import_rig_skeleton(self):
        """
        Imports rig skeleton maya file into the scene from rig/skeleton folder
        in project folder.
        :return:
        """

        import_file_list = glob.glob('{}*.mb'.format(self.project_dir_dict['rig_skeleton']))

        for file in import_file_list:
            file_skeleton_list = import_and_return_node_type(file_path=file, node_type='transform')

            top_node_list = get_top_hierarchy_node(file_skeleton_list)
            mc.parent(top_node_list, self.group_hierarchy_dict['skeleton'])

    def import_defined_items(self):
        pass

    def _create_global_control(self):
        """
        Creates control in world 0 to be the main control of the rig.
        All other controls will be parented to it.
        :return:
        """
        control_name = 'global_ctrl'
        global_control = tpCtrl.Control(name=control_name)
        global_control.add_offset_grp()
        self.control_object_dict.update({control_name: global_control})

        mc.parent(global_control.get_offset_grp_list()[0],
                  self.group_hierarchy_dict['control_group'])

    def _add_controls_to_skeleton(self):
        """
        Creates controls in all joints in the main skeleton.
        Names it after the joint that is being controlled and,
        changes sufix from _jnt to _ctrl.
        :return:
        """
        rig_skeleton_root_jnt = 'root_jnt'
        skeleton_joint_list = mc.listRelatives(rig_skeleton_root_jnt,
                                               allDescendents=True,
                                               type='joint')
        skeleton_joint_list.reverse()
        skeleton_joint_list.insert(0, rig_skeleton_root_jnt)
        root_group = None

        for index, joint in enumerate(skeleton_joint_list):
            joint_control_name = joint.replace('_jnt', '_ctrl')

            # create the control
            joint_control = tpCtrl.Control(name=joint_control_name)
            self.skeleton_base_ctrl_object_dict.update({joint: joint_control})
            self.control_object_dict.update({joint_control_name: joint_control})

            joint_control.add_offset_grp()
            control_offset_grp = joint_control.get_offset_grp_list()[0]
            mc.matchTransform(control_offset_grp, joint, position=True, rotation=True)

            if index == 0:
                root_group = control_offset_grp

            if skeleton_joint_list.index(joint) is not 0:
                joint_parent = mc.listRelatives(joint, parent=True, type='joint')[0]
                control_parent = joint_parent.replace('_jnt', '_ctrl')

                mc.parent(control_offset_grp, control_parent)

        mc.parent(root_group, self.control_object_dict['global_ctrl'].get_name())

    def _constraint_skeleton_to_base_controls(self):
        """
        Constrains all joints of the base skeleton to the created controls.
        :return:
        """
        for joint in self.skeleton_base_ctrl_object_dict:
            control_name = self.skeleton_base_ctrl_object_dict[joint].get_name()
            mc.parentConstraint(control_name, joint, maintainOffset=True)
            mc.scaleConstraint(control_name, joint)

    def _build_face_controls(self):
        """
        Builds the controls that drives the face blendShape targets.
        The controls are over the face, and uses a template joint set to define
        the positions.
        :return:
        """

        root_template_joint = 'faceControls_root_templateJnt'
        rail_curve_list = []
        rail_curve_offset_grp_list = []
        control_obj_list = []
        control_offset_group_list = []

        ctrl_template_joint_list = mc.listRelatives(
            root_template_joint,
            children=True,
            type='joint')

        for control_template_joint in ctrl_template_joint_list:
            control_template_name_split = control_template_joint.split('_')
            control_name = '_'.join(control_template_name_split[:-2])
            control_side = control_template_name_split[0]
            end_template_joint = mc.listRelatives(
                control_template_joint,
                children=True,
                type='joint')[0]

            # create rail curves
            a_b_curve = tpUtils.curve_from_a_to_b(
                control_template_joint,
                end_template_joint,
                name=control_name + '_rail')
            # curve inherits the color of the parent by default
            # setting overrideEnable so that it can maintain its own color
            mc.setAttr(a_b_curve + ".overrideEnabled", 1)
            mc.setAttr(a_b_curve + ".overrideRGBColors", 1)
            a_b_curve_shape = mc.listRelatives(a_b_curve, shapes=True)[0]
            a_b_curve_offset_group = mc.group(name=a_b_curve + '_grp', empty=True)
            mc.matchTransform(a_b_curve_offset_group, control_template_joint, position=True)
            mc.matchTransform(a_b_curve, control_template_joint, pivots=True)
            mc.parent(a_b_curve, a_b_curve_offset_group)
            mc.makeIdentity(a_b_curve, apply=True, translate=True)
            rail_curve_list.append(a_b_curve)
            rail_curve_offset_grp_list.append(a_b_curve_offset_group)

            # creates sphere controls that slide on curve rails
            control_obj = tpCtrl.Control(name=control_name)
            control_obj.set_type('sphere')
            # define sphere color based on the side in name prefix
            if control_side == 'l':
                control_obj.set_color_preset('red')
            elif control_side == 'r':
                control_obj.set_color_preset('blue')
            else:
                control_obj.set_color_preset('yellow')
            # setting the scale of the sphere and freezing
            mc.xform(control_name, scale=(0.15, 0.15, 0.15))
            mc.makeIdentity(control_name, apply=True, scale=True)
            control_obj.add_offset_grp()
            control_offset = control_obj.get_offset_grp_list()[0]
            control_obj_list.append(control_obj)
            control_offset_group_list.append(control_offset)

            attr_list = mc.listAttr(control_name, visible=True, keyable=True)
            for attr in attr_list:
                mc.setAttr(
                    '{}.{}'.format(control_name, attr),
                    keyable=False,
                    channelBox=False,
                    lock=True)

            mc.addAttr(control_name,
                       longName='parameter',
                       attributeType='double',
                       maxValue=1.0,
                       minValue=0.0,
                       keyable=True)

            mc.matchTransform(control_offset, control_template_joint, position=True)

            point_on_curve_node = mc.createNode('pointOnCurveInfo', name=control_name + '_poc_node')
            mc.connectAttr(a_b_curve_shape + '.worldSpace', point_on_curve_node + '.inputCurve')
            mc.connectAttr(control_name + '.parameter', point_on_curve_node + '.parameter')
            mc.connectAttr(point_on_curve_node + '.result.position', control_offset + '.translate')

            mc.setAttr(root_template_joint + '.visibility', 0)

        mc.parent(rail_curve_offset_grp_list, 'head_ctrl')
        face_controls_group = mc.group(control_offset_group_list, name='face_controls_grp')
        mc.parent(face_controls_group, self.group_hierarchy_dict['control_group'])

        self.control_object_list = control_obj_list

    def _create_face_blend_shape_node(self):
        """
        Creates the face blendShape node and imports the .shp file.
        :return:
        """
        head_model_geo = 'head_model_geo'
        self.face_blend_shape_node = mc.blendShape(
            head_model_geo,
            name='head_model_geo_bld_node')[0]

        mc.blendShape(
            self.face_blend_shape_node,
            edit=True,
            ip=self.project_dir_dict['blend_shape_data'] + 'head_model_geo_bs_node.shp')

    def _connect_eye_shapes_to_controls(self):
        """
        The method purpose is to connect the eye look blendShape targets
        to the eye look controls via setDrivenKey
        :return:
        """
        eyes_targets_data_set = {
            'eye_lookLeft_geo': {
                'angle': 30.0,
                'attribute': 'rotateZ'},
            'eye_lookRight_geo': {
                'angle': -30.0,
                'attribute': 'rotateZ'},
            'eye_lookUp_geo': {
                'angle': -22.639,
                'attribute': 'rotateY'},
            'eye_lookDown_geo': {
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

    def _connect_face_controls_to_blend_shape_targets(self):
        """
        Based on the control names, derives the name of the targets and attemps
        to connect. Prints a message if the target doesn't exist.
        :return:
        """
        for control_obj in self.control_object_list:
            control_name = control_obj.get_name()
            target_name = control_name.replace('_ctrl', '')

            try:
                mc.connectAttr(control_name + '.parameter',
                               '{}.{}_geo'.format(self.face_blend_shape_node, target_name))
            except RuntimeError:
                print('[{}] Target Nor Found'.format(target_name))
                continue

    def _create_neck_module(self):
        """
        Consider naming the template skeleton joints as code - n001 - and
        rename it based on dictionary data, making it easy to change the convention
        if necessary
        :return:
        """
        # get c1 to c7 joint world position
        neck_joint_list = [
            'head_jnt',
            'neck_c1_jnt',
            'neck_c2_jnt',
            'neck_c3_jnt',
            'neck_c4_jnt',
            'neck_c5_jnt',
            'neck_c6_jnt',
            'neck_c7_jnt']

        # create surface from positions
        joint_position_list = [mc.xform(joint, query=True, translation=True, worldSpace=True)
                               for joint in neck_joint_list]
        module_surface = tpUtils.surface_from_position_list(joint_position_list,
                                                            name='neck_module_system')
        module_surface_shape = mc.listRelatives(module_surface, shapes=True)[0]

        # add follicle in the middle of the surface
        follicle_transform = tpUtils.create_follicle(
            module_surface_shape,
            u_val=0.5,
            v_val=0.5,
            name='neck_main_ctrl_flc')
        mc.scaleConstraint('root_ctrl', follicle_transform)

        # create neck global control
        main_neck_control = tpCtrl.Control(name='main_neck_ctrl')
        self.control_object_dict.update({main_neck_control.get_name(): main_neck_control})
        control_offset_group = main_neck_control.add_offset_grp()
        main_neck_control.add_offset_grp(negate=True)
        # place control on follicle - constraint offset group
        mc.parentConstraint(follicle_transform, control_offset_group)
        mc.scaleConstraint(follicle_transform, control_offset_group)

        # add extra offset group to base controls
        neck_control_list = [joint.replace('_jnt', '_ctrl') for joint in neck_joint_list]
        neck_control_obj_list = [self.control_object_dict[control] for control in neck_control_list]
        offset_group_list = [control_obj.add_offset_grp() for control_obj in neck_control_obj_list]

        # create multiply divide node
        # create gear down node for mid control
        divide_node = mc.createNode('multiplyDivide')
        mc.setAttr('{}.operation'.format(divide_node), 2)
        mc.setAttr('{}.input2'.format(divide_node), -3, 3, -3)

        # connect global control to multiply node
        mc.connectAttr('{}.r'.format(main_neck_control.get_name()),
                       '{}.input1'.format(divide_node))
        # connect multiply output to base controls offset group
        for offset_group in offset_group_list:
            mc.connectAttr('{}.output'.format(divide_node),
                           '{}.r'.format(offset_group))
        # add neck global control into rig control group
        mc.group(
            module_surface,
            follicle_transform,
            control_offset_group,
            parent=self.group_hierarchy_dict['module'],
            name='neck_module_grp')

        # store module surface on class dict
        self.system_mesh_weight_dict.update({'neck_module': [module_surface]})

    def _build_mouth_muscle_module(self):
        muzzle_geo = 'muzzle_template_geo'
        skull_geo = 'skull_bone_geo'
        jaw_geo = 'jaw_bone_geo'

        self.mouth_muscle_obj = tpMouthMuscle.TpMouthMuscle(muzzle_geo, skull_geo, jaw_geo)
        self.mouth_muscle_obj.build_module()

    def _build_mouth_output_module(self):
        muzzle_geo = 'muzzle_template_geo'
        self.mouth_output_obj = tpMouthOutput.TpMouthOutput()
        self.mouth_output_obj.set_oral_geo(muzzle_geo)
        self.mouth_output_obj.build()

    def _setup_modules(self):
        pass

    def _import_skin_clusters(self):
        """
        Must also be able to import maps:
        - blendShape target maps
        - dual quaternion hybrid map
        :return:
        """
        skin_manager = tpUtils.SkinWeightsManager(self.project_dir_dict['skin_clusters_model'], [''])
        skin_manager.import_weights_from_file()

    def _om_import_model_geo_skin_weights(self):
        dir_path = self.project_dir_dict['skin_clusters_model']
        file_list = glob.glob('{dir}/*.json'.format(dir=dir_path))

        for file in file_list:
            norm_path = os.path.normpath(file)
            file_name_and_extension = norm_path.split("\\")[-1]
            file_name = file_name_and_extension.split('.')[0]

            self.om_import_skin_weights(dir_path=dir_path, file_name=file_name)

    def _om_import_template_geo_skin_weights(self):
        dir_path = self.project_dir_dict['skin_clusters_template']
        file_list = glob.glob('{dir}/*.json'.format(dir=dir_path))

        for file in file_list:
            norm_path = os.path.normpath(file)
            file_name_and_extension = norm_path.split("\\")[-1]
            file_name = file_name_and_extension.split('.')[0]

            self.om_import_skin_weights(dir_path=dir_path, file_name=file_name)

    def _om_import_system_geo_skin_weights(self):
        dir_path = self.project_dir_dict['skin_clusters_system']
        file_list = glob.glob('{dir}/*.json'.format(dir=dir_path))

        for file in file_list:
            norm_path = os.path.normpath(file)
            file_name_and_extension = norm_path.split("\\")[-1]
            file_name = file_name_and_extension.split('.')[0]

            self.om_import_skin_weights(dir_path=dir_path, file_name=file_name)

    def _camera_fit_view(self):
        mc.select(clear=True)
        mc.modelEditor('modelPanel4', e=True, dtx=True)
        mc.setAttr("hardwareRenderingGlobals.lineAAEnable", 1)
        mc.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
        mc.viewFit(animate=True)

    def _import_control_shapes(self):
        control_shape_data = tpUtils.read_json_file(
            '{}{}.json'.format(self.project_dir_dict['control_shape'],
                               self.project_data_file_dict['control_shape']))

        for control in control_shape_data:
            control_type = self.control_object_dict[control].get_shape_type()

            if control_type != control_shape_data[control]['curve_form']:
                self.control_object_dict[control].set_type(control_shape_data[control]['curve_form'])

            self.control_object_dict[control].restore_shape_position_from_data(
                control_shape_data[control]['shape_data'])
            self.control_object_dict[control].set_color_rgb(control_shape_data[control]['curve_color'])

    def _lock_and_hide_attributes(self):
        pass

    # utility methods
    def _export_skin_cluster(self):
        pass


class PostBuildUtils(tpRig):

    def __init__(self):
        super(PostBuildUtils, self).__init__()

        self.register_build_method('Control Tools', 'Post Build Utils')
        self.register_build_method('Export Control Shapes', 'Control Tools', self.export_control_shapes)
        self.register_build_method('Control Set Shape Form', 'Control Tools', self.control_set_form)
        self.register_build_method('Control Set Color Preset', 'Control Tools', self.control_set_color_preset)
        self.register_build_method('Control Mirror Selected', 'Control Tools', self.control_mirror_selected)
        self.register_build_method('Control Store New Preset Form', 'Control Tools', self.store_new_control_shape_preset)

        self.register_build_method('Skin Tools', 'Post Build Utils')
        self.register_build_method('Rename All SkinCluster Nodes', 'Skin Tools', self.rename_skin_cluster_nodes)
        self.register_build_method('OM Export Skin Weights', 'Skin Tools', self.om_export_skin_weights)
        self.register_build_method('OM Import Skin Weights', 'Skin Tools', self.om_import_skin_weights)
        self.register_build_method('OM Export Model Geo Weights', 'Skin Tools',
                                   self.om_export_model_geo_skin_weights)
        self.register_build_method('OM Export Template Geo Weights', 'Skin Tools',
                                   self.om_export_template_geo_skin_weights)
        self.register_build_method('OM Export System Weights', 'Skin Tools',
                                   self.om_export_system_skin_weights)

        self.register_build_method('Import And Assign Arnold Shaders', 'Post Build Utils', self.assign_arnold_shaders)

    # def om_export_model_geo_skin_weights(self):
    #     """
    #     Queries all geometry in 'model_geo_grp'
    #     Exports skin weights file using om_export_skin_weights.
    #     :return:
    #     """
    #     file_name = 'skin_cluster_001'  # hard coded, must be variable
    #     geo_grp = self.group_hierarchy_dict['model_geometry']
    #     all_children = mc.listRelatives(geo_grp, children=True, allDescendents=True, type='transform')
    #     geometry_list = [child for child in all_children if mc.listRelatives(child, type='shape')]
    #     skinned_geo_list = [geo for geo in geometry_list if mel.eval('findRelatedSkinCluster "{}"'.format(geo))]
    #
    #     self.om_export_skin_weights(skinned_geo_list,
    #                                 self.project_dir_dict['skin_clusters_model'],
    #                                 file_name)

    def om_export_model_geo_skin_weights(self):
        """
        Queries all geometry in 'model_geo_grp'
        Exports skin weights file using om_export_skin_weights.
        :return:
        """
        file_name = self.project_data_file_dict['model_geo_skin_weights']
        geo_grp = self.group_hierarchy_dict['model_geometry']
        all_children = mc.listRelatives(geo_grp, children=True, allDescendents=True, type='transform')
        geometry_list = [child for child in all_children if mc.listRelatives(child, type='shape')]
        skinned_geo_list = [geo for geo in geometry_list if mel.eval('findRelatedSkinCluster "{}"'.format(geo))]

        self.om_export_skin_weights(skinned_geo_list,
                                    self.project_dir_dict['skin_clusters_model'],
                                    file_name)

    def om_export_template_geo_skin_weights(self):
        """
        Queries all geometry in 'template_geo_grp'
        Exports skin weights file using om_export_skin_weights.
        :return:
        """
        file_name = self.project_data_file_dict['template_geo_skin_weights']
        geo_grp = self.group_hierarchy_dict['template_geometry']
        all_children = mc.listRelatives(geo_grp, children=True, allDescendents=True, type='transform')
        geometry_list = [child for child in all_children if mc.listRelatives(child, type='shape')]
        skinned_geo_list = [geo for geo in geometry_list if mel.eval('findRelatedSkinCluster "{}"'.format(geo))]

        self.om_export_skin_weights(skinned_geo_list,
                                    self.project_dir_dict['skin_clusters_template'],
                                    file_name)

    def om_export_system_skin_weights(self):
        """
        Export all skin weights for meshes added to self.system_mesh_weight_dict.
        Exports skin weights file using om_export_skin_weights.
        :return:
        """

        for module in self.system_mesh_weight_dict:

            file_name = '{}_weights'.format(module)
            geometry_list = self.system_mesh_weight_dict[module]
            skinned_geo_list = [geo for geo in geometry_list if mel.eval('findRelatedSkinCluster "{}"'.format(geo))]

            self.om_export_skin_weights(skinned_geo_list,
                                        self.project_dir_dict['skin_clusters_system'],
                                        file_name)


    def rename_skin_cluster_nodes(self):
        """
        Queries all skinclusters in the scene and name it according to the transform node name
        :return:
        """
        skin_cluster_list = mc.ls(type='skinCluster')

        for skin_cluster in skin_cluster_list:
            geo_name = mc.listConnections('{}.outputGeometry'.format(skin_cluster), d=True)[0]
            mc.rename(skin_cluster, '{}_skc'.format(geo_name))

    def export_control_shapes(self):
        """
        Exports controls shapes based on the control objects that have been created
        during the build process.

        Obs. 14.11.2022 - This feature should be inside of the class, or in a control manager
        class - Having it outside of the class just makes the system broken, considering that
        if we had to transfer this function to another project, this feature wouldn't be
        available.

        :return:
        """

        all_controls_data_dict = {}

        for control in self.control_object_dict:
            shape_dict = self.control_object_dict[control].get_position_data()

            control_data = {
                'curve_color': self.control_object_dict[control].get_curve_color(),
                'curve_form': self.control_object_dict[control].get_shape_type(),
                'shape_data': shape_dict
            }

            all_controls_data_dict.update({control: control_data})

        tpUtils.export_dict_as_json(all_controls_data_dict,
                                    self.project_data_file_dict['control_shape'],
                                    self.project_dir_dict['control_shape'])

        print('[File Exported] {}{}.json'.format(self.project_data_file_dict['control_shape'],
                                                 self.project_dir_dict['control_shape']))

    def control_set_form(self):
        control_list = mc.ls(selection=True)

        if not control_list:
            print('Please select controls')
            return

        # get control objects
        control_object_list = [self.control_object_dict[control_name] for control_name in control_list]
        # get type list
        shape_form_list = control_object_list[0].list_available_shapes()
        # print type list
        print(shape_form_list)
        # prompt user
        result = mc.promptDialog(
            title='Choose Shape Form',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if result == 'OK':
            shape_form = mc.promptDialog(query=True, text=True)

            for control_object in control_object_list:
                control_object.set_type(shape_form)

    def control_set_color_preset(self):
        control_list = mc.ls(selection=True)

        if not control_list:
            print('Please select controls')
            return

        # get control objects
        control_object_list = [self.control_object_dict[control_name] for control_name in control_list]
        # get type list
        color_preset_list = control_object_list[0].get_color_preset_list()
        # print type list
        print(color_preset_list)
        # prompt user
        result = mc.promptDialog(
            title='Choose Color Preset',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if result == 'OK':
            color_preset = mc.promptDialog(query=True, text=True)

            for control_object in control_object_list:
                control_object.set_color_preset(color_preset)

    def control_mirror_selected(self):
        control_selection = mc.ls(sl=True)

        for control in control_selection:
            opposite_control = control.replace('l_', 'r_')

            control_object = self.control_object_dict[control]
            opposite_control_object = self.control_object_dict[opposite_control]

            control_data = control_object.get_position_data(world_space=True)
            opposite_control_data = {}

            for shape_name in control_data:
                opposite_shape_name = shape_name.replace('l_', 'r_', 1)
                vertex_mirror_position_list = []

                for vertex_position in control_data[shape_name]:
                    mirror_position = [vertex_position[0]*-1, vertex_position[1], vertex_position[2]]
                    vertex_mirror_position_list.append(mirror_position)
                opposite_control_data.update({opposite_shape_name: vertex_mirror_position_list})

            opposite_control_object.restore_shape_position_from_data(opposite_control_data, world_space=True)

    def store_new_control_shape_preset(self):
        curve_transform = mc.ls(sl=True)

        result = mc.promptDialog(
            title='New Control Form Preset Name',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

        if result == 'OK':
            control_preset_name = mc.promptDialog(query=True, text=True)

            new_preset_control_obj = tpCtrl.Control(name='temp_control_curve')
            new_preset_control_obj.store_new_shape_form(control_preset_name, curve_transform)

    def assign_arnold_shaders(self):
        mesh_shader_dict = {
            'head_model_geo': 'head_model_geo_aiMat',
            'eye_ball_lens_left_geo': 'eye_cornea_aiMat',
            'eye_ball_lens_right_geo': 'eye_cornea_aiMat',
            'eye_ball_real_time_left_geo': 'eye_iris_aiMat',
            'eye_ball_real_time_right_geo': 'eye_iris_aiMat',
            'teeth_geo': 'teeth_geo_aiMat',
            'tongue_geo': 'tongue_geo_aiMat'
        }
        shader_path = glob.glob('{}*.mb'.format(self.project_dir_dict['shader_arnold']))[0]
        mc.file(shader_path, i=True)

        for geo in mesh_shader_dict:
            mc.select(geo, replace=True)
            mc.hyperShade(assign=mesh_shader_dict[geo])

    def import_arnold_light_set(self):
        pass


def get_top_hierarchy_node(item_list):
    top_node_list = []

    for node in item_list:
        node_full_path = mc.ls(node, long=True)[0]
        top_parent_node = node_full_path.split('|')[1]

        if top_parent_node not in top_node_list:
            top_node_list.append(top_parent_node)

    return top_node_list


def import_and_return_node_type(file_path, node_type):
    """
    Imports a file and return all nodes of 'type'
    :param file_path:
    :param node_type:
    :return:
    """
    name_space = 'file_import'
    mc.file(file_path, i=True, namespace=name_space)

    node_type_list_namespace = mc.ls('{}:*'.format(name_space), type=node_type)
    node_type_list = [node.replace('{}:'.format(name_space), '') for node in node_type_list_namespace]

    mc.namespace(removeNamespace=name_space, mergeNamespaceWithRoot=True)

    return node_type_list


def import_shapes(folder_path):
    """
    Specific to project - Goes though every shape folder and imports shapes
    Path Structure - main folder / shape folder / OBJ /
    :param folder_path:
    :return:
    """
    folder_list = glob.glob("{}*".format(folder_path))
    mesh_list = []

    for folder in folder_list:
        shape_folder = os.path.basename(os.path.normpath(folder))
        shape_name = '_'.join(shape_folder.split('_')[1:])
        file_list = glob.glob('{}/OBJ/*.OBJ'.format(folder))
        pose_node_list = []

        for file in file_list:
            node_list = mc.file(
                file,
                i=True,
                type='OBJ',
                ignoreVersion=True,
                mergeNamespacesOnClash=False,
                options='so=0',
                returnNewNodes=True,
                removeDuplicateNetworks=True)
            pose_node_list.extend(node_list)

        mc.group(pose_node_list, name='{}_grp'.format(shape_name))
        # mesh = mc.listRelatives('grp_{}'.format(shape_name))[0]
        # mc.rename(mesh, 'geo_{}'.format(shape_name))
        # mesh_list.append(mesh)

    return mesh_list


"""
Module Description

    the class will be the parent of all other classes, such as the modules

    Ideally, instead of copying attributes from module to module until it surfaces on the rig top group,
    by inheriting this class, we should be able to add the necessary attributes directly to the rig
    top group, and avoid creating loops or complex solutions to attribute creation.


Development list

    UI Dev
        - stop UI from refreshing when double click DONE
            - QtreeView.setExpandsOnDoubleClick()
                - Also creating a black box in front of tree
        - check if 'check' is true in other to run the function DONE
        - add a stop marker/button 
            - Allow the user to mark one the functions with the stop, so that the build
            stops at that point
        - ability to save presets
            - if the user unchecks buildable items on the list
            - he is then able to save this changes


    Functions Dev
        - Builder files
            - Check if maya is set to a project
                - if no - promp user - please set your project
            - Check if we have the rig builder script in the project files
                - if there are no build scripts
                    - prompt user - would to add the build script to the project?
                    - prompt the user with the options of build script available
                        - face, biped, quadruped, etc...
            - Check if rigBuilder folder structure is inside of the project
                - geo dir
                - template dir
                - data dir
                    - skincluster
                    - vertex position data
                    - template positions data



        - Project  class
        - Checking for skincluster data
        - Checking for geo dir
            - How to organize geo
            - where to place it in the project
            - should the geo be all in one single file or are we able to
                have multiple goe files (.mb)
            - should I have a .json conteining the information about which geo
                should be imported?
            - What other kinds of geo could we have?
                - template geo
                - model geo
                - 

Project Development
    - clean shaders from geo - DONE 
    - Add basic shader to head_model_geo - DONE
    - Adjust the geo skeleton - rib cage - cervical - DONE 
    - Skeleton 
        - Joint Skeleton - finish adding all joints
            - Add leg joints - or  just flip
            - Add feet joints
            - Add arm joints
            - Add tongue joints
                # all joints must be parented to main skeleton 
        - rename all joints
        - orient joints
    - rigBuilder
        - Change font size
        - Add function to create custom template for project
        - Read build script from local project
        
"""