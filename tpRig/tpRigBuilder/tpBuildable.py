

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

