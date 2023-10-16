import tpRig.tpRigBuilder.tpModule as tpModule


class ModuleBuilder:

    def __init__(self):
        self.action_list = []
        pass

    def add_action(self,
                   action_name='',
                   parent_action='',
                   method=None,
                   after=None,
                   background_color=None,
                   stop_flag=False):

        new_action_obj = tpModule.Action(action_name,
                                         parent_action,
                                         method,
                                         after,
                                         background_color,
                                         stop_flag)
        self.action_list.append(new_action_obj)

    def build_module(self):

        pass

