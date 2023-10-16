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
TO DO LIST

    - Create a folder in the tpRigBuilder directory to hold all of the script variations
    - The UI will then list all of the modules in the directory, and list in drop down
    - Once the user chooses, the UI updates the action stack
    
    - currently the root of the script is the RigBuilderLogic module  # Which doesn't make much sense tbh
    - All file paths in the script must be varible - or comeing from a Project class
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
            QComboBox {
                font-size: 10pt;
                background: rgba(80,80,80,255);   
            }
            QTreeWidget {
                font-size: 12pt;
                background: rgba(60,60,60,255);   
            }
            QHeaderView::section {
                background: rgba(80,80,80,255);
                border: 1px solid rgba(50,50,50,255);
            }
            '''

        self.qt_color_dict = {
            'dark_green': QtCore.Qt.darkGreen,
            'dark_blue': QtCore.Qt.darkBlue,
            'dark_magenta': QtCore.Qt.darkMagenta,
            'dark_cyan': QtCore.Qt.darkCyan,
        }

        self.buildable_item_list = []
        self.progress_bar_step = None

        self.setWindowTitle('tpRigBuilder v1.00')
        self.setMinimumWidth(400)
        self.setMaximumWidth(600)
        self.setMinimumHeight(800)
        self.setMaximumHeight(1000)
        self.setStyleSheet("background-color: rgba(240,240,240,255);")
        self.setWindowOpacity(0.9)
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

        self.actionstack_logo = QtWidgets.QLabel()
        self.actionstack_logo_pixmap = QtGui.QPixmap(
            'E:/Scripts/tpTools/tpRig/tpRigBuilder/images/action_stack_logo_v01.png')
        self.actionstack_logo.setPixmap(self.actionstack_logo_pixmap.scaledToHeight(
            30, QtCore.Qt.SmoothTransformation))
        self.actionstack_logo.setObjectName('actionstack_logo')

        self.stop_pixmap = QtGui.QPixmap('E:/Scripts/tpTools/tpRig/tpRigBuilder/images/stop_90_90.png')
        self.progress_pixmap = QtGui.QPixmap('E:/Scripts/tpTools/tpRig/tpRigBuilder/images/progress_90_90.png')

        self.stack_combobox = QtWidgets.QComboBox()
        self.stack_combobox.setStyleSheet(self.style_sheet)
        self.stack_pushbutton = QtWidgets.QPushButton('Load')
        # add logic to get scripts and add to the list
        # also add logic to reload the different scripts
        # self.stack_combobox.addItems(['test item'])

        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.installEventFilter(self)
        self.tree_widget.setStyleSheet(self.style_sheet)
        self.tree_widget.setHeaderLabels(['RigBuildTree'])
        self.tree_widget.setExpandsOnDoubleClick(False)
        self.tree_widget.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)

        self.item_hierarchy_dict.update({'root': self.tree_widget})

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(100000)
        self.progress_bar.setValue(0)

        # action report labels
        self.action_report_style = 'QLabel { color : rgba(80,80,80,255); }'
        self.action_label = QtWidgets.QLabel('Current Action:')
        self.total_execution_time_label = QtWidgets.QLabel('Total Execution Time:')
        self.action_dynamic_label = QtWidgets.QLabel('--')
        self.total_execution_dynamic_label = QtWidgets.QLabel('--:--')

        self.action_label.setStyleSheet(self.action_report_style)
        self.total_execution_time_label.setStyleSheet(self.action_report_style)
        self.action_dynamic_label.setStyleSheet(self.action_report_style)
        self.total_execution_dynamic_label.setStyleSheet(self.action_report_style)

        # self.progress_chart = QtCharts.QtCharts.QBarSeries()

        # create all items objects
        for method_data in self.buildable_methods_list:
            method_name = method_data['method_name']

            item = QtWidgets.QTreeWidgetItem([method_name])
            item.setCheckState(0, QtCore.Qt.CheckState.Checked)
            if method_data['background_color']:
                item.setBackground(0, QtGui.QBrush(self.qt_color_dict[method_data['background_color']]))
            # item.setIcon(0, self.logo_pixmap)

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

            # if it is the first Item of the list - add as top level item
            if parent_item_name == 'root':
                parent_item.addTopLevelItem(item)
            else:
                if after:
                    item_before = self.item_hierarchy_dict[after]
                    item_before_index = parent_item.indexOfChild(item_before)
                    parent_item.insertChild(item_before_index + 1, item)
                else:
                    parent_item.addChild(item)

    def create_layouts(self):
        branding_layout = QtWidgets.QHBoxLayout()
        branding_layout.addWidget(self.actionstack_logo)
        branding_layout.addWidget(self.tpaulino_logo, 0, QtCore.Qt.AlignRight)

        stack_dropdown_vbox = QtWidgets.QVBoxLayout()
        stack_dropdown_hbox = QtWidgets.QHBoxLayout()
        stack_dropdown_hbox.addWidget(self.stack_combobox, 4)
        stack_dropdown_hbox.addWidget(self.stack_pushbutton, 1)
        stack_dropdown_vbox.addLayout(stack_dropdown_hbox)

        tree_layout = QtWidgets.QVBoxLayout()
        tree_layout.addWidget(self.builder_label)
        tree_layout.addWidget(self.tree_widget)

        action_report_layout = QtWidgets.QHBoxLayout()
        action_report_layout.addWidget(self.action_label)
        action_report_layout.addWidget(self.action_dynamic_label)

        execution_time_layout = QtWidgets.QHBoxLayout()
        execution_time_layout.addWidget(self.total_execution_time_label)
        execution_time_layout.addWidget(self.total_execution_dynamic_label)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(branding_layout)
        main_layout.addLayout(stack_dropdown_vbox)
        main_layout.addLayout(tree_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(action_report_layout)
        main_layout.addLayout(execution_time_layout)

    def create_connections(self):
        self.tree_widget.itemClicked.connect(self._print_method_docstring)
        # returns item(object), column
        self.tree_widget.itemDoubleClicked.connect(self.call_buildable_from_double_click)

    def _print_method_docstring(self, item):
        """
        When item is clicked in the build tree, the docstring will be printed in
        the script editor to help understand the action purpose.
        :param item:
        :return:
        """
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

    def call_buildable_from_double_click(self, item):
        self.call_buildable_method([item])

    def call_buildable_method(self, item_list):
        """
        Executes all active buildable methods in the stack based on item clicked.
        Also updated the progress bar, calculated execution times and prints action names
        :param item_list:
        :return:
        """
        # clearing the buildable item list to populate again
        self.buildable_item_list = []
        # listing all active buildable items under selection
        self.list_all_active_buildable(item_list)
        # getting buildable list length
        progress_bar_division_factor = len(self.buildable_item_list)
        self.progress_bar_step = int(self.progress_bar.maximum() / progress_bar_division_factor)
        # zeroing out progress bar
        self.progress_bar.setValue(0)
        # clear all green progress flags if they exist - leaves stop
        self.reset_all_flags()

        build_start_time = time.time()

        for active_item in self.buildable_item_list:
            item_name = active_item.text(0)
            method_data = self.get_method_data(item_name)

            if method_data['stop_flag']:
                break

            else:
                self.action_dynamic_label.setText(item_name)
                print('[{}] Start'.format(method_data['method'].__name__))
                process_start_time = time.time()

                # execute action method
                method_data['method']()
                # adds green progress circle to item
                active_item.setIcon(0, self.progress_pixmap)

                process_end_time = time.time()
                process_time = process_end_time - process_start_time
                print('[{}][{}] End \n'.format(method_data['method'].__name__, process_time))

                # update progress bar
                self.progress_bar.setValue(self.progress_bar.value() + self.progress_bar_step)

        # sets progress bar to 100 - due to decimals, sometimes stops at 99
        # self.progress_bar.setValue(self.progress_bar.maximum())

        # calculate full process execution time
        build_end_time = time.time()
        build_process_time = build_end_time - build_start_time
        self.total_execution_dynamic_label.setText(time.strftime('%H:%M:%S', time.gmtime(build_process_time)))

        self.action_dynamic_label.setText('BUILD FINISHED')
        print('[BUILD FINISHED][PROCESS TIME][{}] \n'.format(build_process_time))
        # clears all progress green circles
        self.reset_all_flags()

    def list_all_active_buildable(self, item_list):
        """
        Recursive method (runs itself)

        Purpose: Create a list of active, executable items
        Goes though all items and item children and children children and so on,
        and creates a list of all active items
        :param item_list:
        :return:
        """
        for item in item_list:
            item_action_name = item.text(0)
            item_data = self.get_method_data(item_action_name)

            # if it is a parent method and it has children and is checked - Run all children
            if not item_data['method'] and item.childCount() > 0 and item.checkState(0) == 2:
                for index in range(item.childCount()):
                    child_item_obj = item.child(index)
                    child_name = child_item_obj.text(0)
                    child_data = self.get_method_data(child_name)

                    # if child has method - run
                    if child_data['method']:
                        if child_item_obj.checkState(0) == 2:  # if item is checked - execute
                            self.buildable_item_list.append(child_item_obj)

                    else:
                        if child_item_obj.checkState(0) == 2:
                            self.list_all_active_buildable([child_item_obj])

            else:  # if it is an item and it has a method associated
                if item.checkState(0) == 2:  # if item is checked - execute
                    self.buildable_item_list.append(item)

        return len(self.buildable_item_list)

    def reset_all_flags(self):
        for item in self.buildable_item_list:
            method_data = self.get_method_data(item.text(0))

            if not method_data['stop_flag']:
                clean_icon = QtGui.QPixmap()
                item.setIcon(0, clean_icon)

    def get_method_data(self, method_name):
        """
        Since we are using a list to store dictionaries to keep the order of registration,
        it is not possible to get the method data by name
        Therefore, it is necessary to loop across all dictionaries in the list
        and find the one that matches the name of the current method_name.

        The function then returns the matching data for method_name.
        :param method_name:
        :return:
        """
        data = None

        for method_data in self.buildable_methods_list:
            if method_data['method_name'] == method_name:
                data = method_data

        return data

    def get_method_index(self, method_name):
        method_data_index = None

        for index, method_data in enumerate(self.buildable_methods_list):
            if method_data['method_name'] == method_name:
                method_data_index = index

        return method_data_index

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.ContextMenu and source is self.tree_widget:
            menu = QtWidgets.QMenu()
            run = menu.addAction('Run')
            stop = menu.addAction('Add Stop Flag')
            remove = menu.addAction('Remove Stop Flag')

            menu.triggered.connect(self.menu_action)

            menu.exec_(event.globalPos())

            return True
        # return super().eventFilter(source, event)

    def menu_action(self, action):
        action_dict = {
            'Run': self.menu_action_run,
            'Add Stop Flag': self.menu_action_stop,
            'Remove Stop Flag': self.menu_action_remove_stop
        }

        action_dict[action.text()]()

    def menu_action_run(self):
        item_list = self.tree_widget.selectedItems()
        self.call_buildable_method(item_list)

    def menu_action_stop(self):
        item_list = self.tree_widget.selectedItems()

        for item in item_list:
            item.setIcon(0, self.stop_pixmap)
            method_data = self.get_method_data(item.text(0))
            method_data_index = self.get_method_index(item.text(0))

            method_data['stop_flag'] = True
            self.buildable_methods_list[method_data_index] = method_data

    def menu_action_remove_stop(self):
        clean_icon = QtGui.QPixmap()
        item_list = self.tree_widget.selectedItems()

        for item in item_list:
            item.setIcon(0, clean_icon)
            method_data = self.get_method_data(item.text(0))
            method_data_index = self.get_method_index(item.text(0))

            method_data['stop_flag'] = False
            self.buildable_methods_list[method_data_index] = method_data

    def get_stack_scripts_in_folder(self):
        directory_path = ''
        file_list = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        pass

