# from dataclasses import dataclass, field
# import dataclasses
# from typing import Callable

"""
The module class will be created to represent the stages
such as the Pre-Build Utils, FaceRig, etc
So that they become compartimentalized, independent,
and the actions are detached from the abstract module class

The user should be able to use the module class to create
their desired actions, and communicating with other modules by
querying information.
"""

# The Stack needs to be able to get both Actions and modules
# Actions are single functions to be added to the hierarchy
# modules are multiple actions nested under a item
# modules can have submodules
# The Stack can create root items
#   Or no? Should it only be created by the module?
#   Does it need to restrict to modules?


# @dataclass  - Dataclasses does not work with the current version of maya (2020) :/
# class Action:
#
#     action_name: str
#     parent_action: str
#     method: Callable = field(default=None)  # Callable
#     after: None = field(default=None)
#     background_color: None = field(default=None)
#     stop_flag: False = field(default=False)


class Action(object):

    def __init__(self,
                 action_name='my_action',
                 parent_action='root',
                 method=None,
                 after=None,
                 background_color=None,
                 stop_flag=False):

        self._action_name = action_name
        self._parent_action = parent_action
        self._method = method
        self._after = after
        self._background_color = background_color
        self._stop_flag = stop_flag

    def as_dict(self):
        return {
            'method_name': self._action_name,
            'parent': self._parent_action,
            'method': self._method,
            'after': self._after,
            'background_color': self._background_color,
            'stop_flag': self._stop_flag
        }

    # Property ____________________
    @property
    def action_name(self):
        return self._action_name

    @property
    def parent_action(self):
        return self._parent_action

    @property
    def method(self):
        return self._method

    @property
    def after(self):
        return self._after

    @property
    def background_color(self):
        return self._background_color

    @property
    def stop_flag(self):
        return self._stop_flag

    # Setter ____________________
    @action_name.setter
    def action_name(self, value):
        self._action_name = value

    @parent_action.setter
    def parent_action(self, value):
        self._parent_action = value

    @method.setter
    def method(self, value):
        self._method = value

    @after.setter
    def after(self, value):
        self._after = value

    @background_color.setter
    def background_color(self, value):
        self._background_color = value

    @stop_flag.setter
    def stop_flag(self, value):
        self._stop_flag = value


class Module:
    """
    This module class does not need to hold complex date structures,
    you can create another class called say "Project" where all the
    data would be encapsulated, and just add the object methods to this class.

    This way you always know what to expect from that module if you pass it along
    and you can easily query data, without having to store it in this module and
    having to be prepared for all sorts of data type.
    """
    def __init__(self,
                 module_name='ActionStack_Module',
                 module_has_top_item=True,
                 module_top_item_name='root',
                 background_color=None):

        self.module_name = module_name

        if module_has_top_item:
            self.module_top_item = Action()

            self.module_top_item.action_name = module_name
            self.module_top_item.parent_action = module_top_item_name
            self.module_top_item.background_color = background_color

            self._action_object_list = [self.module_top_item]
        else:
            self._action_object_list = []

        self.action_dict_list = []

    @property
    def action_object_list(self):
        return self._action_object_list

    @action_object_list.setter  # Can be used to append action objs directly to the list
    def action_object_list(self, action_object_list):
        self._action_object_list = action_object_list

    def get_action_object_list(self):
        return self._action_object_list

    def add_action(self, action_object):
        self._action_object_list.append(action_object)

    def add_action_list(self, action_object_list):
        self._action_object_list.extend(action_object_list)

    def add_module(self, module_object):
        self._action_object_list.extend(module_object.action_object_list)

    def add_engine_module_obj(self, engine_object):
        pass

    def get_action_dict_list(self):
        action_dict_list = [action_obj.as_dict() for action_obj in self._action_object_list]
        return action_dict_list


# class Hierarchy:
#
#     def __init__(self):
#         pass
#
#     def add_module(self, module_object):
#         pass
#
#
# class ModuleBuilder:
#
#     def __init__(self):
#         pass
#
#
# class Project:
#     """
#     Controls all that is necessary on the project side:
#     - folders
#     - Creating unexisting folders
#
#     """
#
#     def __init__(self):
#         pass




