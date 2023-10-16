import os
import glob

import maya.cmds as cmds
import math

import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim

# modules import section
import tpControl
import tpRig.tpFaceRig.tpMouth.tpMouthMuscle as tpMouthMuscle
import tpRig.tpFaceRig.tpMouth.tpMouthOutput as tpMouthOutput

import tpRig.tpRigUtils as tpUtils
reload(tpUtils)
import tpRig.tpControl.tpControl as tpCtrl
reload(tpCtrl)

import tpRig.tpFaceRig.tpMouth.tpMouthSlide as tpMouthSlide
import tpRig.tpRigBuilder.tpUtilities as tpUtilities
reload(tpUtilities)


class tpRig(tpUtilities.Utilities):

    def __init__(self):
        super(tpRig, self).__init__()

        self.maya_project_directory = ''
        self.skin_weights_directory = ''

        self.skeleton_base_ctrl_object_dict = {}

        # defining all groups in the rig hierarchy
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

        self.register_build_method('Create Face Muscle FK Controls', self.top_level_item,
                                   self._create_face_muscle_fk_controls)

        self.register_build_method('Import Control Shapes', self.top_level_item, self._import_control_shapes)

        self.register_build_method('Import Deformer Weights', self.top_level_item)
        self.register_build_method('Import Model Geo Skin Weights', 'Import Deformer Weights',
                                   self._om_import_model_geo_skin_weights)
        self.register_build_method('Import Template Geo Skin Weights', 'Import Deformer Weights',
                                   self._om_import_template_geo_skin_weights)
        self.register_build_method('Import System Geo Skin Weights', 'Import Deformer Weights',
                                   self._om_import_system_geo_skin_weights)

        self.register_build_method('Camera View Fit', self.top_level_item, self._camera_fit_view)

    # def get_registered_build_methods(self):
    #     return self.build_methods_list

    # SCENE SETUP METHODS ________________________________

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

    # RIG BUILDING METHODS ______________________________________

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

    def _create_main_face_control(self):
        pass

    def _create_face_settings_control(self):
        pass

    def _create_remote_fk_controls_on_system_skeletons(self):
        pass

    def _create_face_muscle_fk_controls(self):
        remote_control_list = [
            'l_masseter_sysD_ctrl',
            'l_temporalis_sysD_ctrl',
            'l_cheekRaiser_sysD_ctrl',
            'r_masseter_sysD_ctrl',
            'r_depressorSupercili2_sysA_ctrl',
            'r_cheek_puff_sysA_ctrl',
            'r_bottom_lip_puff_sysA_ctrl',
            'r_depressorSupercili1_sysA_ctrl',
            'l_top_lip_puff_sysA_ctrl',
            'r_temporalis_sysD_ctrl',
            'r_cheekRaiser_sysD_ctrl',
            'subMaxilar_sysA_ctrl',
            'l_cheek_puff_sysA_ctrl',
            'l_depressorSupercili1_sysA_ctrl',
            'r_top_lip_puff_sysA_ctrl',
            'r_ear_sysA_ctrl',
            'l_ear_sysA_ctrl',
            'l_bottom_lip_puff_sysA_ctrl',
            'l_depressorSupercili2_sysA_ctrl',
            'l_noiseRaiser_sysB_ctrl',
            'l_outerBrowRaiser_sysB_ctrl',
            'l_innerBrowRaiser_sysB_ctrl',
            'r_innerBrowRaiser_sysB_ctrl',
            'r_outerBrowRaiser_sysB_ctrl',
            'r_noiseRaiser_sysB_ctrl']

        control_grp = mc.group(name="muscle_ctrl_grp", empty=True)

        for control in remote_control_list:
            name_split = control.split("_")
            del name_split[-2]

            control_name = '_'.join(name_split)
            user_control = tpCtrl.Control(name=control_name)
            user_control.set_type('arrow')
            user_control.add_offset_grp()
            user_control.top_group_match_position(control, t=True, r=True)

            mc.parent(user_control.get_top_group(), control_grp)

            for attr in ".t,.rotate,.s".split(','):
                mc.connectAttr(user_control.get_name() + attr, control + attr, force=True)

            self.control_object_dict.update({user_control.get_name(): user_control})

    def _mouth_slide_build_system(self):
        pass

    def _mouth_slide_parent_controls(self):
        pass

    def _mouth_slide_parent_mouth_bind_joints(self):
        pass

    # CLOSE UP METHODS _____________________________

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

        self.register_build_method('Transfer Weights Set B to A', 'Skin Tools', self.weights_from_set_b_to_a)
        self.register_build_method('Register Set A', 'Transfer Weights Set B to A', self.register_set_a)
        self.register_build_method('Register Set B', 'Transfer Weights Set B to A', self.register_set_b)
        self.register_build_method('Transfer Missing Weights', 'Transfer Weights Set B to A', self.add_missing_influences)

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

    def weights_from_set_b_to_a(self):
        weights_from_list_b_to_a_closest(self.vertex_set_b, self.vertex_set_a)

    def register_set_a(self):
        self.vertex_set_a = mc.ls(sl=True)

    def register_set_b(self):
        self.vertex_set_b = mc.ls(sl=True)

    def add_missing_influences(self):
        add_unexisting_influences_a_to_b(self.vertex_set_b, self.vertex_set_a)


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


def find_closest_vertex(reference_vertex, vertex_list):
    """
    Finds closest vertex to reference vertex in provided list

    :reference_vertex: vertex to be compared to all vertex in provided list
    :vertex_list: list to compare with reference_vertex

    :return: vertex with smallest distance from reference_vertex from provided vertex_list
    """

    vertex_distance_dict = {}
    # get reference vertex position
    ref_vert_pos = cmds.xform(reference_vertex, query=True, translation=True, worldSpace=True)

    for vertex in vertex_list:
        # gets the position of correct vertex in list
        position = cmds.xform(vertex, query=True, translation=True, worldSpace=True)
        # finds euclidean distance between the two points
        distance = math.sqrt((ref_vert_pos[0] - position[0]) ** 2 + (ref_vert_pos[1] - position[1]) ** 2 + (
                    ref_vert_pos[2] - position[2]) ** 2)

        # updates dictionary with information
        vertex_distance_dict.update({distance: vertex})

    # finds smallest value on listed distances
    closest_distance = min(vertex_distance_dict.keys())

    return vertex_distance_dict[closest_distance]


def weights_from_list_b_to_a_closest(list_a, list_b):
    """
    Loops through all vertices in list A, finds the closest vertex in list B
    and copies the weights from B to A.

    Both vertex list must be in the same mesh.

    :list_a: List of vertices to get new skin weights
    :list_b: List of vertices to provide the skinning information
    """

    for vertex in list_a:
        closest_in_b = find_closest_vertex(vertex, list_b)

        cmds.select(closest_in_b, r=True)
        mel.eval('artAttrSkinWeightCopy')

        cmds.select(vertex, r=True)
        mel.eval('artAttrSkinWeightPaste')

    print("[Copy Skin Weights From List A to B] Process Completed - Success")


# vert_list_a = cmds.ls(selection=True, flatten=True)
# vert_list_b = cmds.ls(selection=True, flatten=True)

# weights_from_list_b_to_a_closest(vert_list_a, vert_list_b)


def add_unexisting_influences_a_to_b(vert_list_a, vert_list_b):
    influence_list_b = []
    for vertex in vert_list_b:
        skincluster = mel.eval('findRelatedSkinCluster {};'.format(vertex.split('.')[0]))
        influence_query_list = cmds.skinPercent(skincluster, vertex, query=True, transform=None)

        for influence in influence_query_list:
            if influence not in influence_list_b:
                influence_list_b.append(influence)

    influence_list_a = []
    for vertex in vert_list_a:
        skincluster = mel.eval('findRelatedSkinCluster {};'.format(vertex.split('.')[0]))
        influence_query_list = cmds.skinPercent(skincluster, vertex, query=True, transform=None)

        for influence in influence_query_list:
            if influence not in influence_list_a:
                influence_list_a.append(influence)

    unexisting_influences = [influence for influence in influence_list_a if influence not in influence_list_b]

    print(
        "[add_unexisting_influences_a_to_b] Adding Unexistent Influences to '{}'".format(vert_list_b[0].split('.')[0]))

    b_skin_cluster = mel.eval('findRelatedSkinCluster {};'.format(vert_list_b[0].split('.')[0]))
    for influence in unexisting_influences:
        cmds.skinCluster(
            b_skin_cluster,
            edit=True,
            useGeometry=True,
            dropoffRate=4,
            polySmoothness=0,
            nurbsSamples=10,
            lockWeights=True,
            weight=0,
            addInfluence=influence)

    print("[add_unexisting_influences_a_to_b] Process Successful")

    return unexisting_influences

# add_unexisting_influences_a_to_b(vert_list_b, vert_list_a)

# cmds.skinPercent('Cbody1aOSDM_EnvFilter', cmds.ls(sl=1)[0], query=True, transform=None)
# cmds.select(vert_list_a)

# jnt_list = cmds.ls(sl=1)
# for i in jnt_list:
#	if i == jnt_list[-1]:
#		print('{}'.format(i))
#	else:
#		print('{},'.format(i))