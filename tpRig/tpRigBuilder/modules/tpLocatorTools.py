import maya.cmds as cmds
import maya.api.OpenMaya as om2
import tpRig.tpRigBuilder.tpModule as tpModule
reload(tpModule)


# Create ActionStack class responsible for creating a node on the scene
# that is then connected to all groups created by the tools and
# keeps track of what is related to the software

def build_module_object(module_name='', parent_action_name='root', background_color=None):
    module_name = 'Multi Locator Tool'

    locator_module_object = tpModule.Module(  # Freaking confusing, must change
        module_name=module_name,
        module_top_item_name=parent_action_name,
        background_color=background_color)

    locator_tool_obj = MultiLocator()

    action_list = [
        tpModule.Action('Create Locators From Selection', module_name),
        tpModule.Action('Load Selection', 'Create Locators From Selection', locator_tool_obj.load_selection),
        tpModule.Action('Create Locators', 'Create Locators From Selection', locator_tool_obj.create_locators_on_selection),
        tpModule.Action('Create Connection Curve', 'Create Locators From Selection', locator_tool_obj.create_connection_curve),
        tpModule.Action('Select Locators', module_name, locator_tool_obj.select_locators),
        tpModule.Action('Select Associates', module_name, locator_tool_obj.select_associations),
        tpModule.Action('Association Match Transform', module_name, locator_tool_obj.association_match_transform),
        tpModule.Action('Association Match Position', module_name, locator_tool_obj.association_match_position),
        tpModule.Action('Locator Match Transform', module_name, locator_tool_obj.locator_match_transform),
        tpModule.Action('Constrain Association', module_name, locator_tool_obj.constrain_association_to_locator),
        tpModule.Action('Delete Constraint', module_name, locator_tool_obj.delete_constraints),
        tpModule.Action('Delete Locators', module_name, locator_tool_obj.delete_locators),
    ]

    locator_module_object.add_action_list(action_list)

    return locator_module_object


class Locator:

    def __init__(self, transform):
        """
        The class represents a single locator and its associated transform.
        The scope of the class is limited to a single locator and storing data
        about its operations in relation to the associated transform.


        :param transform:
        """
        # Getting association and locator
        self._association = transform

        self._locator = cmds.spaceLocator(name=self._association + '_tpLocator')[0]
        locator_shape_node = cmds.listRelatives(self._locator, shapes=True)[0]
        cmds.setAttr(locator_shape_node + '.overrideEnabled', 1)
        cmds.setAttr(locator_shape_node + '.overrideColor', 13)  # Color index for red

        # Create a text curve for the label
        annotation_tag = cmds.annotate(self._locator, text=self._locator)
        cmds.setAttr(annotation_tag + '.overrideEnabled', 1)
        cmds.setAttr(annotation_tag + '.overrideColor', 13)  # Color index for red
        # List all the visible attributes on the node
        annotation_transform = cmds.listRelatives(annotation_tag, parent=True)[0]
        visible_attributes = cmds.listAttr(annotation_transform, keyable=True)
        for attr in visible_attributes:
            # Lock the attribute
            cmds.setAttr(
                "{}.{}".format(annotation_transform, attr),
                lock=True,
                keyable=False,
                channelBox=False)

        cmds.move(0.2, 0.2, 0, annotation_tag, relative=True)
        cmds.parent(annotation_transform, self._locator)
        # add .associate attribute to be connected via message

        # Using the DAG Path of both to track them on the scene
        # This way they can be grouped and moved and we wont lose track
        om2_selection_list = om2.MSelectionList()
        om2_selection_list.add(self._association)
        self._associate_dag_path = om2_selection_list.getDagPath(0)
        om2_selection_list.clear()

        om2_selection_list.add(self._locator)
        self._locator_dag_path = om2_selection_list.getDagPath(0)
        om2_selection_list.clear()

        # Matching the position of the association
        cmds.matchTransform(self._locator_dag_path.fullPathName(), self._associate_dag_path.fullPathName())

        self._parent_constraint_node = None
        self._connection_curve_dag_path = None
        self._cluster_dag_path_list = []

    def __str__(self):
        return self._locator_dag_path.fullPathName()

    @property
    def association(self):
        return self._association

    @property
    def display_curve(self):
        return self._connection_curve_dag_path.fullPathName()

    @property
    def position(self):
        return cmds.xform(self._locator_dag_path.fullPathName(), query=True, worldSpace=True, translation=True)

    def create_association(self, associate):
        """
        Develop
        :param associate:
        :return:
        """
        pass

    def create_display_connection(self):
        """
        Creating a linear 2 cv curve that links the locator to the
        associated transform. One cluster is created for each cv and
        parented to the locator and the transform.
        :return:
        """
        # Get locator position
        locator_position = cmds.xform(
            self._locator_dag_path.fullPathName(),
            query=True,
            translation=True,
            worldSpace=True)
        # Get transform position
        associate_position = cmds.xform(
            self._associate_dag_path.fullPathName(),
            query=True,
            translation=True,
            worldSpace=True)
        # Create the curve with each cv on queried positions
        connection_curve = cmds.curve(
            d=True,
            p=[locator_position, associate_position],
            name='{}_connection_crv'.format(self._association))
        # Set the curve to template to avoid selection
        cmds.setAttr(connection_curve + '.overrideEnabled', 1)
        cmds.setAttr(connection_curve + '.overrideDisplayType', 1)
        # Get DAG path to get the name safely
        om2_selection_list = om2.MSelectionList()
        om2_selection_list.add(connection_curve)
        self._connection_curve_dag_path = om2_selection_list.getDagPath(0)

        # Create clusters for each cv
        for cv, item in enumerate([self._locator, self.association]):
            cluster = cmds.cluster(
                '{}.cv[{}]'.format(self._connection_curve_dag_path.fullPathName(), cv),
                name='{}_{}_cls'.format(item, cv))[1]
            cmds.setAttr(cluster + '.visibility', 0)
            cmds.parent(cluster, item)

    def delete_display_connection(self):
        cmds.delete(self._connection_curve_dag_path.fullPathName())
        self._cluster_dag_path_list = []
        self._connection_curve_dag_path = None

    def constrain_as_driver(self):
        """
        Parent constrains the associated transform to the locator.
        :return:
        """
        if self._parent_constraint_node is None:
            self._parent_constraint_node = cmds.parentConstraint(
                self._locator_dag_path.fullPathName(),
                self._associate_dag_path.fullPathName(),
                maintainOffset=True
            )
        else:
            cmds.warning(
                '[tpLocator] {} is already constrained to Locator {}'.format(self._association, self._locator))

    def association_match_position(self):
        cmds.matchTransform(
            self._associate_dag_path.fullPathName(),
            self._locator_dag_path.fullPathName(),
            position=True)

    def association_match_transform(self):
        cmds.matchTransform(
            self._associate_dag_path.fullPathName(),
            self._locator_dag_path.fullPathName())

    def locator_match_transform(self):
        cmds.matchTransform(
            self._locator_dag_path.fullPathName(),
            self._associate_dag_path.fullPathName())

    def parent_under(self, parent):
        cmds.parent(self._locator_dag_path.fullPathName(), parent)

    def delete_constraint(self):
        cmds.delete(self._parent_constraint_node)

    def delete_self(self):
        cmds.delete(self._locator_dag_path.fullPathName())

        if self._connection_curve_dag_path is not None:
            cmds.delete(self._connection_curve_dag_path.fullPathName())
            self._cluster_dag_path_list = []
            self._connection_curve_dag_path = None


class MultiLocator:

    def __init__(self):
        self._tool_top_group = None
        self._selection_list = []
        self._locator_obj_list = []

    def load_selection(self):
        self._selection_list = cmds.ls(selection=True)

    def load_locators_from_scene(self):
        """
        locators created by the class will contain all the information stored
        in attributes in the locator

        all locators created by the system must also be connected to a tag node
        so that they can be retrieved on a new session

        :return:
        """

    def create_locators_on_selection(self):
        if self._tool_top_group is None:
            self._tool_top_group = cmds.group(name='tp_multi_locator_grp', empty=True, world=True)

        for transform in self._selection_list:
            locator_obj = Locator(transform)
            self._locator_obj_list.append(locator_obj)
            locator_obj.parent_under(self._tool_top_group)

    def create_connection_curve(self):
        curve_grp = cmds.group(name='tp_display_crv_grp', empty=True, world=True)
        for locator in self._locator_obj_list:
            locator.create_display_connection()
            cmds.parent(locator.display_curve, curve_grp)
        cmds.parent(curve_grp, self._tool_top_group)

    def delete_connection_curve(self):
        for locator in self._locator_obj_list:
            locator.delete_display_connection()

    def select_locators(self):
        cmds.select(clear=True)
        cmds.select(self._locator_obj_list)

    def select_associations(self):
        cmds.select(clear=True)
        for locator in self._locator_obj_list:
            cmds.select(locator.association, add=True)

    def association_match_position(self):
        for locator in self._locator_obj_list:
            locator.association_match_position()

    def association_match_transform(self):
        for locator in self._locator_obj_list:
            locator.association_match_transform()

    def locator_match_transform(self):
        for locator in self._locator_obj_list:
            locator.locator_match_transform()

    def constrain_association_to_locator(self):
        for locator in self._locator_obj_list:
            locator.constrain_as_driver()

    def delete_constraints(self):
        for locator in self._locator_obj_list:
            locator.delete_constraint()

    def delete_locators(self):
        for locator in self._locator_obj_list:
            locator.delete_self()
            self._locator_obj_list = []

        cmds.delete(self._tool_top_group)
        self._tool_top_group = None


# tools should require:
class toolClass:

    def __init__(self, data_obj, tools_grp_obj, project_obj):
        pass


def get_dag_path(node_name):
    # Create a selection list
    selection_list = om2.MSelectionList()
    selection_list.add(node_name)

    # Get the first (or only) item as an MDagPath object
    try:
        dag_path = selection_list.getDagPath(0)
        print("DAG Path: ", dag_path.fullPathName())
        return dag_path

    except RuntimeError:
        print("Node not found or is not a DAG node.")