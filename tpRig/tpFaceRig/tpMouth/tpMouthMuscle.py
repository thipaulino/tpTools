import tpRig.tpModule as mod
import tpRig.tpRigUtils as tpu
import tpRig.tpNameConvention as tpName
import tpVertexCatalogue.tpVertexCatalogue_logic as tpv
import tpRig.tp2dDistribute as tpDist
import maya.cmds as mc
reload(mod)

"""
DEVELOPMENT PLAN
- consider creating individual build class for each muscle
    - avoid complexity on generalizing loop for all muscles

- problem
    - how to organize cataloged points to create the muscle
    - how to get points on the right order, given they are in multiple surfaces
    
- possible solutions
    - re work vertex catalog to be vertex centric (vertex as an object containing information)
    - assemble muscle points individually (a method each) to get correct orders
        - approach advantage is that all of this could be improved without much loss
        - keep the muscle set and muscle generic, make vertex catalog better later
        
- muscle point dictionary ideal structure
    - muscle name
        - point list in built order - start to end
        - side
        - joint amount
        - limit start
        - limit end
        
- action list
    - 
    

"""


class TpMouthMuscle(mod.TpModule):

    def __init__(self):
        super(TpMouthMuscle, self).__init__()
        """
        Assembles the entire muscle based system
        """

        self.module_name = 'mouth_muscle'
        self.skull_base_geo = ''
        self.jaw_base_geo = ''
        self.muzzle_base_geo = ''

        self.tpName = tpName.NameConvention()
        self.rig_module_root_path = "E:/Scripts/tpTools"

        self.template_oral_geo = None
        self.output_oral_geo = None
        self.output_oral_geo_grp = None

        self.vtx_cat = tpv.TpVertexCatalogue()
        self.vtx_cat_dict = {}
        self.vtx_cat_directory = "{}/tpRig/tpFaceRig/tpMouth/mouthData/".format(self.rig_module_root_path)
        self.vtx_cat_file_name = 'tp_muzzleSurface_vtx_catalogue.json'
        self.vtx_cat_file_path = '{}{}'.format(self.vtx_cat_directory, self.vtx_cat_file_name)

        self.joint_radius = 0.1

        self.follicle_dict = {}
        self.joint_dict = {}

        self.muscle_list = ['levatorLabiiSuperiorisAN',
                            'LevatorNasi',
                            'levatorAnguliOris',
                            'zygomaticusMinor',
                            'depressorLabiiInferioris',
                            'levatorLabiiSuperioris',
                            'zygomaticusMajor',
                            'risorius',
                            'depressorAnguliOris',
                            'buccinator',
                            'mentalis']
        self.muscle_point_dict = {}
        self.muscle_object_dict = {}

        self.skull_vtx_cat = None
        self.jaw_vtx_cat = None
        self.muzzle_vtx_cat = None
        self.master_vtx_cat = {}

        self.muscle_set_module_object_list = []

        self.module_build_list.extend([
            self.__assign_catalogue_classes,
            self.__assemble_skull_rooted_points,
            self.__assemble_jaw_rooted_points,
            self.__merge_dictionaries,
            self.__create_muscle_set_module_list,
            self.__build_muscle_set_list,
        ])

    def __assign_catalogue_classes(self):
        # get skull vertex cat data
        skull_json_dir = 'tpRig/tpFaceRig/tpMouth/mouthData/tp_skull_vtx_catalogue.json'
        self.skull_vtx_cat = tpv.TpVertexCatalogue()
        self.skull_vtx_cat.import_json_from_dir(skull_json_dir)
        self.skull_vtx_cat.set_geo(self.skull_base_geo)

        # get jaw vertex cat data
        jaw_json_dir = 'tpRig/tpFaceRig/tpMouth/mouthData/tp_jaw_vtx_catalogue.json'
        self.jaw_vtx_cat = tpv.TpVertexCatalogue()
        self.jaw_vtx_cat.import_json_from_dir(jaw_json_dir)
        self.jaw_vtx_cat.set_geo(self.jaw_base_geo)

        # get surface vertex cat data
        muzzle_json_dir = 'tpRig/tpFaceRig/tpMouth/mouthData/tp_muzzleSurface_vtx_catalogue.json'
        self.muzzle_vtx_cat = tpv.TpVertexCatalogue()
        self.muzzle_vtx_cat.import_json_from_dir(muzzle_json_dir)
        self.muzzle_vtx_cat.set_geo(self.muzzle_base_geo)

    def assemble_master_catalogue(self):
        # get only not empty labels in all catalogues
        muzzle_cat = self.muzzle_vtx_cat.get_catalogue()
        for label in muzzle_cat:
            for side in muzzle_cat[label]:
                if side:
                    pass

    def __assemble_skull_rooted_points(self):
        # get active dict skull
        # get active dict muzzle
        # separate right and left ?
        # merge dictionaries
        self.skull_vtx_dict = {}
        pass

    def __assemble_jaw_rooted_points(self):
        self.jaw_vtx_dict = {}
        pass

    def __assemble_exception_points(self):
        pass

    def __merge_dictionaries(self):
        self.master_vtx_dict = {}
        pass

    def __create_muscle_set_module_list(self):
        for module_name in self.master_vtx_dict:
            muscle_module_object = TpMuscleSet(name=module_name)
            self.muscle_set_module_object_list.append(muscle_module_object)

            muscle_module_object.add_surface(self.muzzle_base_geo)

            for muscle_side in self.master_vtx_dict[module_name]:
                muscle_module_object.add_muscle(
                    point_list=self.master_vtx_dict[muscle_side],
                    side=muscle_side,
                    joint_amount=5,
                    limit_start=0.6,
                    limit_end=1)

    def __build_muscle_set_list(self):
        for muscle_set_module in self.muscle_set_module_object_list:
            muscle_set_module.build_module()

    def __create_top_group_attributes(self):
        for muscle in self.muscle_set_module_object_list:
            mc.addAttr(self.module_control_node,
                       longName='{muscle_name}_pull'.format(muscle_name=muscle.get_module_name()),
                       keyable=True,
                       attributeType='double',
                       defaultValue=0,
                       minValue=0,
                       maxValue=1)

    # def __connect_muscles_to_control_hub(self):
    #     for muscle_obj in self.muscle_object_dict.values():
    #         name = muscle_obj.get_module_name()
    #         muscle_obj.muscle_control_attribute_connect_from('{}.{}'.format(self.module_control_node, name))

    def __assign_module_data(self):
        pass


class TpMuscleSet(mod.TpModule):

    def __init__(self, name=None, side=None):
        """
        Responsible for creating a

        MODULE DEV
            how to create the control attribute for each module on top group
            how to register created attributes to be queried
                how to register attribute type and restrictions
            should a nodeAttribute class be created to handle this?

        action list
            resolve how to create and store attributes
            create function that detects, creates and connects attributes from sub-module

        :param name:
        :param side:
        """
        super(TpMuscleSet, self).__init__(name, side)

        self.muscle_list = []
        self.base_surface = None
        self.module_surface = None

        self.module_build_list.extend([  # could be done with a super on the method
            self.__duplicate_surface,
            self.__build_muscle_list,
            # self.__create_module_control_attributes,
            self.__connect_controls
        ])

    # setup methods
    def add_surface(self, surface):
        self.base_surface = surface

    def add_muscle(self, point_list, side, joint_amount, limit_start, limit_end):
        muscle_object = TpFaceMuscle(name=self.module_name, side=side)
        muscle_object.add_point_list(point_list)
        muscle_object.set_joint_amount(joint_amount)
        muscle_object.set_limit_start(limit_start)  # muscle length will be 0.4
        muscle_object.set_limit_end(limit_end)

        self.muscle_list.append(muscle_object)
        self.sub_module_list.append(muscle_object)

    # build methods
    def __duplicate_surface(self):
        self.module_surface = mc.duplicate(self.base_surface, name='')[0]

    def __build_muscle_list(self):
        for muscle in self.muscle_list:
            muscle.build_module()

    # def __create_module_control_attributes(self):
    #     # for module in list
    #     #   get module name
    #     #   get module control attribute names
    #     #   create division with module name
    #     #   create attribute with module prefix
    #
    #     for muscle in self.muscle_list:
    #         mc.addAttr(self.module_top_group,
    #                    longName=None,
    #                    keyable=True,
    #                    attributeType='double',
    #                    defaultValue=0,
    #                    minValue=0,
    #                    maxValue=1)

    def __connect_controls(self):
        pass


class TpFaceMuscle(mod.TpModule):

    def __init__(self, name='tpMuscle', side='center'):
        super(TpFaceMuscle, self).__init__()
        """
        Creates a single muscle module
        :param name:
        :param side:
        """
        self.module_name = name
        self.module_side = side

        self.limit_start = 0.5
        self.limit_end = 1  # its now 1 to 0, change to 0 to 1

        self.point_list = []
        self.degree = None
        self.curve = None

        self.parameter_list = None

        self.joint_amount = 5
        self.joint_radius = 0.2
        self.fk_joint_list = []

        self.bind_joint = None
        self.bind_joint_group = None

        self.ik_handle = None
        self.ik_handle_effector = None
        self.ik_handle_curve = None
        self.root_cluster = None

        self.pci_node = None  # point on curve info node
        self.pci_set_range = None

        self.muscle_control_attribute = None
        self.control_locator = None  # connected to pci_node, drives ik_handle

        self.module_build_list.extend([
            self._build_curve,
            self._get_parameter_distribution,
            self._create_point_on_curve_info_node,
            self._create_driver_locator,
            self._create_set_range_node,
            self._create_module_top_group_attributes,  # new - using object to keep track of attributes
            self._build_fk_chain,
            self._create_ik_spline,
            self._create_root_cv_control_cluster,
            self._create_bind_joint,
        ])

    # control methods
    # def muscle_control_attribute_connect_from(self, in_plug):
    #     mc.connectAttr(in_plug, '{top_group}.{attribute}'.format(top_group=self.module_top_group,
    #                                                              attribute=self.muscle_control_attribute))

    # def get_control_plug(self):
    #     return "{top_group}.{attribute}".format(
    #         top_group=self.module_top_group,
    #         attribute=self.muscle_control_attribute)

    def get_control_attribute(self):
        return self.muscle_control_attribute

    # setup methods
    def add_point_list(self, point_list):
        self.point_list = point_list

    def add_point(self, point):
        self.point_list.append(point)

    def set_joint_amount(self, amount):
        self.joint_amount = amount

    def set_limit_start(self, limit):
        self.limit_start = limit

    def set_limit_end(self, limit):
        self.limit_end = limit

    def set_degree(self, degree):
        self.degree = degree

    def set_joint_radius(self, radius):
        self.joint_radius = radius

    def set_reverse_direction(self):
        pass

    # assemble methods
    def _build_curve(self):
        """
        Using the provided point list - Creates a curve on the point list order
        :return:
        """
        self.degree = 3 if len(self.point_list) >= 4 else 1
        self.curve = mc.curve(degree=self.degree,
                              point=self.point_list,
                              name=self.tp_name.build(name=self.module_name + '_path',
                                                      side=self.module_side,
                                                      node_type='curve'))

        curve_shape = mc.listRelatives(self.curve, shapes=1)[0]
        curve_degree = mc.getAttr(curve_shape + ".degree")
        curve_spans = mc.getAttr(curve_shape + ".spans")

        # rebuild stage added to guarantee the curve parameter is 0 to 1
        mc.rebuildCurve(self.curve,
                        constructionHistory=False,
                        replaceOriginal=True,
                        rebuildType=0,  # int - uniform
                        endKnots=1,  # int - multiple end knots
                        keepRange=0,  # int - re parameterize the resulting curve from 0 to 1
                        keepControlPoints=False,
                        keepEndPoints=True,
                        keepTangents=True,
                        spans=curve_spans,
                        degree=curve_degree,
                        tolerance=0.01)

        self.curve_list.append(self.curve)
        self.module_group_dict['curve'].append(self.curve)

    def _get_parameter_distribution(self):
        """
        Given the amount of desired segments on a curve, it will return
        a list of respective parameters
        """
        distribution = tpDist.Tp2dDistribute()
        distribution.set_amount(self.joint_amount)
        distribution.set_limit_start(self.limit_start)  # chain starts in the middle of the curve
        distribution.set_limit_end(self.limit_end)

        self.parameter_list = distribution.get_parameter_list()

    def _create_point_on_curve_info_node(self):
        self.pci_node = mc.createNode('pointOnCurveInfo',
                                      name=self.tp_name.build(name=self.module_name,
                                                              side=self.module_side,
                                                              node_type='pointOnCurveInfo'))
        mc.connectAttr(self.curve + ".worldSpace", self.pci_node + ".inputCurve")

    def _create_driver_locator(self):
        """
        The locator will slide along the curve using the PCI node
        and pull the root CV on the IK splice curve
        """
        self.control_locator = mc.spaceLocator(name=self.tp_name.build(name=self.module_name,
                                                                       side=self.module_side,
                                                                       node_type='locator'))[0]
        mc.setAttr(self.pci_node + ".parameter", self.parameter_list[0])
        mc.connectAttr(self.pci_node + ".position", self.control_locator + ".t")

        self.module_group_dict['locator'].append(self.control_locator)

    def _create_set_range_node(self):
        """
        Remaps the input value from 0 to 1, to the parameter range on the curve
        to create muscle pull
        """
        self.pci_set_range = mc.createNode('setRange',
                                           name=self.tp_name.build(name=self.module_name,
                                                                   side=self.module_side,
                                                                   node_type='setRange'))
        mc.setAttr(self.pci_set_range + '.oldMin.oldMinX', 0)
        mc.setAttr(self.pci_set_range + '.oldMax.oldMaxX', 1)
        mc.setAttr(self.pci_set_range + '.min.minX', self.limit_start)
        mc.setAttr(self.pci_set_range + '.max.maxX', 0)

        # connect to point on curve info node
        mc.connectAttr(self.pci_set_range + '.outValue.outValueX', self.pci_node + '.parameter')

    def _create_module_top_group_attributes(self):
        self.module_attribute_manager.add_attribute_division('module_ctrl', 'CONTROLS')

        pull_attribute = self.module_attribute_manager.add_attribute(
            'muscle_pull',
            keyable=True,
            attributeType='double',
            defaultValue=0,
            minValue=0,
            maxValue=1)

        pull_attribute.connect_to(self.pci_set_range + '.value.valueX')

    def _build_fk_chain(self):
        """
        Based on defined parameter list, creates joint chain using a curve for position.
        :return:
        """
        for n, parameter in enumerate(self.parameter_list):
            position = mc.pointOnCurve(self.curve, parameter=parameter)
            mc.select(clear=True)
            joint = mc.joint(radius=self.joint_radius,
                             name=self.tp_name.build(name=self.module_name,
                                                     side=self.module_side,
                                                     index=n+1,
                                                     node_type='joint'))
            mc.xform(joint, translation=position, worldSpace=True)
            self.fk_joint_list.append(joint)

        tpu.parent_in_list_order(self.fk_joint_list)

        # orient joints
        for joint in self.fk_joint_list:
            mc.joint(joint, edit=True, orientJoint="xyz", secondaryAxisOrient="yup",
                     children=True, zeroScaleOrient=True)

        self.module_group_dict['joint'].append(self.fk_joint_list[0])

    def _create_ik_spline(self):
        ik_handle_data = mc.ikHandle(startJoint=self.fk_joint_list[0],
                                     endEffector=self.fk_joint_list[-1],
                                     solver="ikSplineSolver",
                                     name=self.tp_name.build(name=self.module_name,
                                                             side=self.module_side,
                                                             node_type='ikHandle'))
        self.ik_handle = ik_handle_data[0]
        self.ik_handle_effector = ik_handle_data[1]
        self.ik_handle_curve = mc.rename(ik_handle_data[2],
                                         self.tp_name.build(name=self.module_name + '_ik',
                                                            side=self.module_side,
                                                            node_type='curve'))

        self.module_group_dict['curve'].append(self.ik_handle_curve)
        self.module_group_dict['utility'].append(self.ik_handle)

    def _create_root_cv_control_cluster(self):
        """
        The muscle is pulled backwards by a cluster on te first CV
        on the IK spline curve. This method creates the cluster
        :return:
        """
        self.root_cluster = mc.cluster(self.ik_handle_curve + '.cv[0]',
                                       name=self.tp_name.build(name=self.module_name,
                                                               side=self.module_side,
                                                               node_type='cluster'))[1]
        mc.parentConstraint(self.control_locator, self.root_cluster, maintainOffset=False)

        self.module_group_dict['utility'].append(self.root_cluster)

    def _create_bind_joint(self):
        """
        Bind joint will be place and parented to the last joint on the Ik spline
        """
        mc.select(clear=True)
        self.bind_joint = mc.joint(radius=self.joint_radius,
                                   name=self.tp_name.build(name=self.module_name,
                                                           side=self.module_side,
                                                           index=1,
                                                           node_type='bind_joint'))
        self.bind_joint_group = mc.group(self.bind_joint,
                                         name=self.tp_name.build(name=self.module_name,
                                                                 side=self.module_side,
                                                                 index=1,
                                                                 node_type='bind_joint',
                                                                 group=True))
        mc.parentConstraint(self.fk_joint_list[-1], self.bind_joint_group, maintainOffset=False)

        self.module_group_dict['bind_joint'].append(self.bind_joint_group)
