import maya.cmds as mc
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import tpRig.tpRigBuilder.tpRigBuilderLogic as builderLogic
reload(builderLogic)

"""
DEVELOPMENT PLAN
- Ability to register methods to execute
- Ability to execute other classes methods
- Ability to change arguments parameters
    - Therefore able to read method arguments and reproduce them
- Execute methods in sequence


Action Plan
- have a tree built
- click the first item and have all the items in the hierarchy print their names

"""


def maya_main_window():
    """
    Return the main window widget as a python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


class TpRigBuilderUI(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(TpRigBuilderUI, self).__init__(parent)

        self.setWindowTitle('tpRigBuilder v1.00')
        self.setMinimumWidth(350)
        self.setMaximumWidth(400)
        self.setMaximumHeight(400)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.builder_logic_obj = builderLogic.TpRigBuilderLogic()
        self.buildable_methods_list = self.builder_logic_obj.get_buildable_methods()

        self.item_hierarchy_dict = {}

        # initialize layout
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        self.builder_label = QtWidgets.QLabel("RIG BUILDER")

        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setHeaderLabels(['RigBuildTree'])
        self.tree_widget.setExpandsOnDoubleClick(False)

        self.item_hierarchy_dict.update({'root': self.tree_widget})

        # create all items objects
        for method_data in self.buildable_methods_list:
            method_name = method_data['method_name']

            item = QtWidgets.QTreeWidgetItem([method_name])
            item.setCheckState(0, QtCore.Qt.CheckState.Checked)
            self.item_hierarchy_dict.update({method_name: item})

        # hierarchy setup
        for index, method_data in enumerate(self.buildable_methods_list):
            # data digest
            method_name = method_data['method_name']
            parent_item_name = method_data['parent']
            parent_item = self.item_hierarchy_dict[parent_item_name]
            method = method_data['method']
            after = method_data['after']

            item = self.item_hierarchy_dict[method_name]

            if index == 0:  # if it is the first Item of the list - add as top level item
                parent_item.addTopLevelItem(item)
            else:
                if after:
                    item_before = self.item_hierarchy_dict[after]
                    item_before_index = parent_item.indexOfChild(item_before)
                    parent_item.insertChild(item_before_index + 1, item)
                else:
                    parent_item.addChild(item)

    def create_layouts(self):
        tree_layout = QtWidgets.QVBoxLayout(self)
        tree_layout.addWidget(self.builder_label)
        tree_layout.addWidget(self.tree_widget)

    def create_connections(self):
        self.tree_widget.itemDoubleClicked.connect(self.call_buildable_method)  # returns item(object), column

    def call_buildable_method(self, item):
        """
        Recursive method
        :param item:
        :return:
        """
        item_action_name = item.text(0)
        item_data = self.get_method_data(item_action_name)

        if not item_data['method'] and item.childCount() > 0:
            for index in range(item.childCount()):
                child = item.child(index)
                child_name = child.text(0)
                child_data = self.get_method_data(child_name)

                if child_data['method']:
                    if child.checkState(0) == 2:  # if item is checked - execute
                        child_data['method']()
                else:
                    self.call_buildable_method(child)
        else:
            if item.checkState(0) == 2:  # if item is checked - execute
                item_data['method']()

    def get_method_data(self, method_name):
        data = None

        for method_data in self.buildable_methods_list:
            if method_data['method_name'] == method_name:
                data = method_data

        return data


def print_item(item, column):
    print('item clicked {}, {}, {}'.format(item, column, item.text(column)))
    return item
