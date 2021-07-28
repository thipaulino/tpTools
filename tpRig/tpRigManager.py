import os
import glob

import maya.cmds as mc
import maya.mel as mel

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
        - 
"""


class Buildable(object):

    def __init__(self):

        self.build_methods_list = []
        self.top_level_item = 'FaceRig'

        # self.register_build_method('Pre-Build', 'root')
        self.register_build_method(self.top_level_item, 'root')

    def register_build_method(self, action_name, parent_action, method=None, after=None):
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
        :return:
        """
        method_data = {
            'method_name': action_name,
            'parent': parent_action,
            'method': method,
            'after': after}

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
            {'skin_clusters': os.path.join(self.project_root_path, 'data/skin_clusters/model/')},
            {'sys_skin_clusters': os.path.join(self.project_root_path, 'data/skin_clusters/system/')}
        ]

        self.project_dir_dict = {}
        for dir_data in self.project_dir_dict_list:
            self.project_dir_dict.update(dir_data)

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


class tpRig(Project):

    def __init__(self):
        super(tpRig, self).__init__()

        self.maya_project_directory = ''
        self.skin_weights_directory = ''

        self.group_hierarchy_dict = {
            'root': 'root',
            'geometry': 'geometry_grp',
            'model_geometry': 'model_geo_grp',
            'template_geometry': 'template_geo_grp',
            'rig': 'rig_grp',
            'rig_template': 'rig_template_grp',
            'module': 'module_grp',
        }

        self.build_manager = BuildMethodsManager()

        self.register_build_method('Create New Scene', self.top_level_item, self._create_new_scene)
        self.register_build_method('Setup Rig Groups', self.top_level_item, self._setup_rig_groups)
        self.register_build_method('Import Rig Template', self.top_level_item, self._import_rig_template)

        self.register_build_method('Import Template Geo', self.top_level_item, self._import_template_geo)
        self.register_build_method('Import Model Geo', self.top_level_item, self._import_model_geo)

        self.register_build_method('Setup Modules', self.top_level_item, self._setup_modules)
        self.register_build_method('Import Control Shapes', self.top_level_item, self._import_control_shapes)

    def get_registered_build_methods(self):
        return self.build_methods_list

    def get_build_manager(self):
        return self.build_manager

    # build methods
    def _create_new_scene(self):
        mc.file(new=True, force=True)
        print('[Create New Scene] Method Done')

    def _setup_rig_groups(self):
        """
        Responsible for creating the rig group hierarchy in the scene
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
        rig_template_group = mc.group(name=self.group_hierarchy_dict['rig_template'], empty=True)
        mc.parent(rig_template_group, rig_group)

        module_group = mc.group(name=self.group_hierarchy_dict['module'], empty=True)

        mc.parent(geo_group, rig_group, module_group, root_group)
        print('[Setup Rig Groups] Method Done')

    def _import_rig_template(self):
        """
        Responsible for importing the template skeleton joints into the scene
        :return:
        """
        import_file_list = glob.glob('{}*.mb'.format(self.project_dir_dict['rig_template']))

        for file in import_file_list:
            file_geo_list = import_and_return_node_type(file_path=file, node_type='joint')

            # find unique top parent nodes and append
            top_node_list = get_top_hierarchy_node(file_geo_list)

            mc.parent(top_node_list, self.group_hierarchy_dict['rig_template'])

        print('[Import Geo] Method Done')

    def _import_template_geo(self):
        import_file_list = glob.glob('{}*.mb'.format(self.project_dir_dict['template_geo']))

        for file in import_file_list:
            file_geo_list = import_and_return_node_type(file_path=file, node_type='transform')
            print(file_geo_list)

            # find unique top parent nodes and append
            top_node_list = get_top_hierarchy_node(file_geo_list)

            mc.parent(top_node_list, self.group_hierarchy_dict['template_geometry'])

        print('[Import Geo] Method Done')

    def _import_model_geo(self):
        import_file_list = glob.glob('{}*.mb'.format(self.project_dir_dict['model_geo']))

        for file in import_file_list:
            file_geo_list = import_and_return_node_type(file_path=file, node_type='transform')

            top_node_list = get_top_hierarchy_node(file_geo_list)

            mc.parent(top_node_list, self.group_hierarchy_dict['model_geometry'])

        print('[Import Geo] Method Done')

    def _setup_modules(self):
        print('[Setup Modules] Method Done')
        pass

    def _import_skin_clusters(self):
        """
        Must also be able to import maps:
        - blendshape maps
        - dual quaternion hybrid map
        :return:
        """
        pass

    def _import_control_shapes(self):
        pass

    def _lock_and_hide_attributes(self):
        pass

    # utility methods
    def _export_skin_cluster(self):
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


class BuildMethodsManager:

    def __init__(self):
        pass

    def Register_build_method(self, object_item):
        pass

    def register_top_level(self):
        pass

    def register_build_stage_title(self):
        pass

    def print_methods(self):
        pass


class BuildItem:

    def __init__(self,
                 manager,
                 action_name,
                 parent,
                 method):

        manager.register_build_method(self)
        self.name = action_name
        self.build_method = method
        self.parent = parent
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def get_name(self):
        return self.name

    def get_method(self):
        return self.build_method

    def get_parent(self):
        return self.parent


# Utility class
class SkinWeightsManager:

    def __init__(self):
        pass

    def add_root_path(self):
        pass

    def set_file_name(self):
        pass

    def skin_export(self):
        pass

    def skin_import(self):
        pass


class RigProjectManager:

    def __init__(self):
        self.project_directory = ''
        self.data_directory = ''
        self.skin_weights_directory = ''

    def get_project_directory(self):
        pass

    def get_data_directory(self):
        pass

    def get_skin_weights_directory(self):
        pass

    def save_template_geo(self):
        pass

    def _check_project(self):
        """
        looks inside current project. Check for standard TpRig folders.
        :return:
        """
        pass

    def _create_folder_structure(self):
        pass

    def _import_standard_files(self):
        """
        Imports standard skin weight files, template geo's, etc...
        :return:
        """
        pass


# Utility functions

# def get_vertex_weights(vertex_list, skin_cluster="", threshold_value=0.001):
#     """
#     Gets the skin percentage in each vertex of the mesh and
#     returns in a dictionary.
#
#     :param vertex_list:
#     :param skin_cluster:
#     :param threshold_value:
#     :return:
#     """
#     # remember to filterExpand list before passing it in
#     vertex_dict = {}
#
#     for vertex in vertex_list:
#         influence_value_list = mc.skinPercent(
#             skin_cluster,
#             vertex,
#             query=True,
#             value=True,
#             ignoreBelow=threshold_value)
#
#         influence_name_list = mc.skinPercent(
#             skin_cluster,
#             vertex,
#             transform=None,
#             query=True,
#             ignoreBelow=threshold_value)
#
#         vertex_dict[vertex] = zip(influence_name_list, influence_value_list)
#
#     return vertex_dict
#
#
# def import_weights_json(*args):
#     import_file = mc.textFieldButtonGrp("FileNameDisplay", q=1, text=1)
#     print("Accessing {0}".format(import_file))
#
#     select_geo_data = utils.geoInfo(geo=1, skinC=1)  # essentially used to get geo and skc name
#     geo_name = select_geo_data[0]
#     skin_cluster_name = select_geo_data[1]
#
#     vert_data = utils.readJsonFile(import_file)
#
#     if len(vert_data) > 0:
#
#         for key in vert_data.keys():
#             try:
#                 mc.skinPercent(skin_cluster_name, key, tv=vert_data[key], zri=1)
#             except:
#                 mc.error("Something went wrong with the skinning")
#         print("{0} vertices were set to specified values.".format(len(vert_data.keys())))
#     else:
#         mc.error("JSON File was empty ")