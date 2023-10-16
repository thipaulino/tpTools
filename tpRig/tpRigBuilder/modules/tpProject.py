import os
import maya.cmds as mc
import tpRig.tpRigBuilder.tpModule as tpModule
reload(tpModule)


class Project:

    def __init__(self):

        self.__user_input = None
        self.project_root_path = mc.workspace(query=True, rootDirectory=True)

        self.project_dir_dict_list = [  # holds entry order | turn this into class attributes
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

    def print_all_dir_paths(self):
        for dir_data in self.project_dir_dict_list:
            print('[{}] {}'.format(dir_data.keys()[0], dir_data.values()[0]))

        print('\n')

    def check_existence(self):
        for dir_data in self.project_dir_dict_list:
            if not os.path.exists(dir_data.values()[0]):
                self.not_found_dir_dict.append({dir_data.keys()[0]: dir_data.values()[0]})

                print('[{}] Path Nonexistent'.format(dir_data.keys()[0], dir_data.values()[0]))

        if not self.not_found_dir_dict:
            print('\n')

    def prompt_user_about_missing_dir(self):
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

    def create_missing_directories(self):
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


def build_module_object(module_name='Project', parent_action_name='root', background_color=None):
    project_object = Project()

    project_module_object = tpModule.Module(module_name, parent_action_name, background_color=background_color)

    action_list = [
        tpModule.Action('Print All Directory Paths', 'Project', method=project_object.print_all_dir_paths),
        tpModule.Action('Check Directories Existence', 'Project', method=project_object.check_existence),
        tpModule.Action('Prompt User', 'Project', method=project_object.prompt_user_about_missing_dir),
        tpModule.Action('Create Missing Directories', 'Project', method=project_object.create_missing_directories)
    ]

    project_module_object.add_action_list(action_list)

    return project_module_object



