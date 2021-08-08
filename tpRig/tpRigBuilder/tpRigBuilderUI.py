import maya.cmds as mc
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui
from shiboken2 import wrapInstance

import time

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

        self.style_sheet = '''
            QTreeWidget {
                font-size: 12pt;
                background: rgba(60,60,60,255);   
            }
            QTreeWidget::Item {
                border-bottom:1px solid rgba(50,50,50,255);
                border-top:1px solid rgba(80,80,80,255);
            }
            QHeaderView::section {
                background: rgba(80,80,80,255);
                border: 1px solid rgba(50,50,50,255);
            }
            '''

        self.setWindowTitle('tpRigBuilder v1.00')
        self.setMinimumWidth(350)
        self.setMaximumWidth(400)
        self.setMinimumHeight(600)
        self.setMaximumHeight(1000)
        self.setStyleSheet("background-color: rgba(240,240,240,255);")
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

        self.tpaulino_logo = QtWidgets.QLabel()
        self.tpaulino_logo.setGeometry(QtCore.QRect(0, 0, 50, 50))
        self.logo_pixmap = QtGui.QPixmap('E:/Scripts/tpTools/tpRig/tpRigBuilder/images/tpaulino_logo.png')
        self.tpaulino_logo.setPixmap(self.logo_pixmap.scaledToHeight(40, QtCore.Qt.SmoothTransformation))
        self.tpaulino_logo.setObjectName('tpaulino_logo')

        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setStyleSheet(self.style_sheet)
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
            # item.font(18)

            if parent_item_name == 'root':  # if it is the first Item of the list - add as top level item
                parent_item.addTopLevelItem(item)
            else:
                if after:
                    item_before = self.item_hierarchy_dict[after]
                    item_before_index = parent_item.indexOfChild(item_before)
                    parent_item.insertChild(item_before_index + 1, item)
                else:
                    parent_item.addChild(item)

    def create_layouts(self):
        tree_layout = QtWidgets.QVBoxLayout()
        tree_layout.addWidget(self.builder_label)
        tree_layout.addWidget(self.tree_widget)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.tpaulino_logo, 0, QtCore.Qt.AlignRight)
        main_layout.addLayout(tree_layout)

    def create_connections(self):
        self.tree_widget.itemClicked.connect(self._print_method_docstring)
        self.tree_widget.itemDoubleClicked.connect(self.call_buildable_method)  # returns item(object), column

    def _print_method_docstring(self, item):
        item_action_name = item.text(0)
        item_data = self.get_method_data(item_action_name)

        if not item_data['method']:
            print('[Docstring] No Associated Method')
        elif item_data['method'].__doc__:
            print('[{}][Docstring]'.format(item_data['method'].__name__))
            print(item_data['method'].__doc__)
        else:
            print('[{}][Docstring]'.format(item_data['method'].__name__))
            print('\n \t \t No Docstring Available \n')

    def call_buildable_method(self, item):
        """
        Recursive method
        :param item:
        :return:
        """
        build_start_time = time.time()

        item_action_name = item.text(0)
        item_data = self.get_method_data(item_action_name)

        # if it is a parent method and it has children - Run all children
        if not item_data['method'] and item.childCount() > 0:
            for index in range(item.childCount()):
                child = item.child(index)
                child_name = child.text(0)
                child_data = self.get_method_data(child_name)

                # if child has method - run
                if child_data['method']:
                    if child.checkState(0) == 2:  # if item is checked - execute
                        print('[{}] Start'.format(child_data['method'].__name__))
                        process_start_time = time.time()

                        child_data['method']()

                        process_end_time = time.time()
                        process_time = process_end_time - process_start_time
                        print('[{}][{}] End \n'.format(
                            child_data['method'].__name__,
                            process_time))
                # else - it is a parent so run function again
                else:
                    self.call_buildable_method(child)
        else:
            if item.checkState(0) == 2:  # if item is checked - execute
                print('[{}] Start'.format(item_data['method'].__name__))
                process_start_time = time.time()

                item_data['method']()

                process_end_time = time.time()
                process_time = process_end_time - process_start_time
                print('[{}][{}] End \n'.format(
                    item_data['method'].__name__,
                    process_time))

        build_end_time = time.time()
        build_process_time = build_end_time - build_start_time
        print('[BUILD FINISHED][PROCESS TIME][{}] \n'.format(build_process_time))

    def get_method_data(self, method_name):
        data = None

        for method_data in self.buildable_methods_list:
            if method_data['method_name'] == method_name:
                data = method_data

        return data


def print_item(item, column):
    print('item clicked {}, {}, {}'.format(item, column, item.text(column)))
    return item
