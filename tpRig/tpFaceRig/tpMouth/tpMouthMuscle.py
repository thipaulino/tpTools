import tpRig.tpModule as mod
reload(mod)
import tpRig.tpRigUtils as tpu
import tpVertexCatalogue.tpVertexCatalogue_logic as tpv
import tpRig.tp2dDistribute as tpDist
import maya.cmds as mc
import traceback

"""
DEVELOPMENT PLAN

Current Issues
- attribute creation on the top module group is conflicting 
    - the top module is creating the subModules division
    - the sub module also have subModule divisions registered
    - when the top module copies the subModule divisions
        - the names are the same for the divisions
        - the code crashes and it is unable to proceed

"""


class TpMouthMuscle(mod.TpModule):

    def __init__(self, muzzle_geo, skull_geo, jaw_geo):
        super(TpMouthMuscle, self).__init__()
        """
        Assembles the entire muscle based system
        - we already have the dictionary with all positions        
        """

        self.module_name = 'mouth_muscle'
        self.skull_base_geo = skull_geo
        self.jaw_base_geo = jaw_geo
        self.muzzle_base_geo = muzzle_geo

        self.muzzle_output_geo = None

        self.rig_module_root_path = "E:/Scripts/tpTools"

        # self.template_oral_geo = None
        # self.output_oral_geo = None
        # self.output_oral_geo_grp = None

        # self.vtx_cat = tpv.TpVertexCatalogue()
        # self.vtx_cat_dict = {}
        # self.vtx_cat_directory = "{}/tpRig/tpFaceRig/tpMouth/mouthData/".format(self.rig_module_root_path)
        # self.vtx_cat_file_name = 'tp_muzzleSurface_vtx_catalogue.json'
        # self.vtx_cat_file_path = '{}{}'.format(self.vtx_cat_directory, self.vtx_cat_file_name)

        self.joint_radius = 0.1

        # self.follicle_dict = {}
        # self.joint_dict = {}

        # self.muscle_list = [
        #     'levatorLabiiSuperiorisAN',
        #     'LevatorNasi',
        #     'levatorAnguliOris',
        #     'zygomaticusMinor',
        #     'depressorLabiiInferioris',
        #     'levatorLabiiSuperioris',
        #     'zygomaticusMajor',
        #     'risorius',
        #     'depressorAnguliOris',
        #     'buccinator',
        #     'mentalis']
        # self.muscle_point_dict = {}
        # self.muscle_object_dict = {}

        self.skull_vtx_cat = None
        self.skull_vtx_dict = {}

        self.jaw_vtx_cat = None
        self.jaw_vtx_dict = {}

        self.muzzle_vtx_cat = None
        self.master_vtx_dict = {}

        self.muscle_set_module_object_list = []

        self.module_build_list.extend([
            self._assign_catalogue_classes,
            self._assemble_skull_rooted_points,
            self._assemble_jaw_rooted_points,
            self._create_muscle_set_module_list,
            self._build_muscle_set_list,
            self._create_blendshape_node_from_submodules_to_output
        ])

    def add_base_geo(self, muzzle, skull, jaw):
        self.muzzle_base_geo = muzzle
        self.skull_base_geo = skull
        self.jaw_base_geo = jaw

    def _assign_catalogue_classes(self):
        """
        This method loads the catalogue data for each of the template geometries

        Current vertex catalogue data structure overview:
        - the saved .json files are Geometry centric, meaning that we have a
        file for each of the template geometries

        Each file has the following structure:
            - muscle name
                - muscle side
                    - 3d point list

        The fact that I have to explain it here means that this assembly should
        probably have it's own class. This could possibly be coming from a template class.

        Or each muscle should have it's own .json file containing:
            Muscle.json
                - Geometry
                    - Side
                        - 3d point list

        This would also require yet another redesign of the vertex catalogue

        :return:
        """

        # get skull vertex cat data
        skull_json_dir = '/tpRig/tpFaceRig/tpMouth/mouthData/tp_skull_vtx_catalogue.json'
        self.skull_vtx_cat = tpv.TpVertexCatalogue()
        self.skull_vtx_cat.import_json_from_dir(self.rig_module_root_path + skull_json_dir)
        self.skull_vtx_cat.set_geo(self.skull_base_geo)

        self.skull_vtx_dict = self.skull_vtx_cat.get_active_catalogue_dict_as_points()

        # get jaw vertex cat data
        jaw_json_dir = '/tpRig/tpFaceRig/tpMouth/mouthData/tp_jaw_vtx_catalogue.json'
        self.jaw_vtx_cat = tpv.TpVertexCatalogue()
        self.jaw_vtx_cat.import_json_from_dir(self.rig_module_root_path + jaw_json_dir)
        self.jaw_vtx_cat.set_geo(self.jaw_base_geo)

        self.jaw_vtx_dict = self.jaw_vtx_cat.get_active_catalogue_dict_as_points()

        # get surface vertex cat data
        muzzle_json_dir = '/tpRig/tpFaceRig/tpMouth/mouthData/tp_muzzle_vtx_catalogue.json'
        self.muzzle_vtx_cat = tpv.TpVertexCatalogue()
        self.muzzle_vtx_cat.import_json_from_dir(self.rig_module_root_path + muzzle_json_dir)
        self.muzzle_vtx_cat.set_geo(self.muzzle_base_geo)

        self.muzzle_vtx_dict = self.muzzle_vtx_cat.get_active_catalogue_dict_as_points()

    def _assemble_skull_rooted_points(self):
        """
        - All muscles have a start and end, a 'root'.
        - All muscles on the face are rooted on the bone, therefore each bone file has only muscle
        that are rooted on the bone.
        - Each template bone geo has a .json file, and the muzzle has a .json file.
        - All muscles ends on the muzzle, therefore the muzzle has them all.

        To assemble the points for a single muscle, we need to:
        - check the start point of the muscle on the bone file
        - check for the same muscle on the muzzle file and get the point
        - add them in this order to the main dictionary under the name of the muscle
        :return:
        """
        for muscle in self.skull_vtx_dict:
            side_dict = {}

            for side in self.skull_vtx_dict[muscle]:
                side_dict.update({side: self.skull_vtx_dict[muscle][side] + self.muzzle_vtx_dict[muscle][side]})

            self.master_vtx_dict.update({muscle: side_dict})

    def _assemble_jaw_rooted_points(self):
        for muscle in self.jaw_vtx_dict:
            side_dict = {}

            for side in self.jaw_vtx_dict[muscle]:
                side_dict.update({side: self.jaw_vtx_dict[muscle][side] + self.muzzle_vtx_dict[muscle][side]})

            self.master_vtx_dict.update({muscle: side_dict})

    def _assemble_exception_points(self):
        # no exceptions so far
        pass

    def _create_muscle_set_module_list(self):
        for muscle_name in self.master_vtx_dict:
            muscle_module_object = TpMuscleSet(name=muscle_name)
            self.muscle_set_module_object_list.append(muscle_module_object)  # list is pointless
            self.sub_module_list.append(muscle_module_object)  # change list to module_group_dict

            muscle_module_object.add_surface(self.muzzle_base_geo)

            for muscle_side in self.master_vtx_dict[muscle_name]:
                print('[Adding Muscles][{}][{}][{}]'.format(muscle_side,
                                                            muscle_name,
                                                            self.master_vtx_dict[muscle_name][muscle_side]))
                muscle_module_object.add_muscle(
                    point_list=self.master_vtx_dict[muscle_name][muscle_side],
                    side=muscle_side,
                    joint_amount=5,
                    limit_start=0.6,
                    limit_end=1)

    def _build_muscle_set_list(self):
        for muscle_set_module in self.muscle_set_module_object_list:
            print('[{}] Building...'.format(muscle_set_module.get_module_name()))
            muscle_set_module.build_module()
            # add top group to dict to be parented later
            self.module_group_dict['sub_module'].append(muscle_set_module.get_module_top_group())

    def _create_top_group_attributes(self):
        for muscle in self.muscle_set_module_object_list:
            mc.addAttr(self.module_control_node,
                       longName='{muscle_name}_pull'.format(muscle_name=muscle.get_module_name()),
                       keyable=True,
                       attributeType='double',
                       defaultValue=0,
                       minValue=0,
                       maxValue=1)

    def _create_blendshape_node_from_submodules_to_output(self):
        # get muscle set geometries
        muscle_set_submodele_geo_list = [sub_module.get_module_surface() for sub_module in self.sub_module_list]
        self.muzzle_output_geo = mc.duplicate(self.muzzle_base_geo, name=self.tp_name.build(name='muzzle_output',
                                                                                            node_type='geometry'))[0]
        self.module_group_dict['geometry'].append(self.muzzle_output_geo)
        mc.blendShape(muscle_set_submodele_geo_list, self.muzzle_output_geo)


class TpMuscleSet(mod.TpModule):

    def __init__(self, name=None, side=None):
        super(TpMuscleSet, self).__init__(name, side)
        """
        Responsible for creating a
        
        MODULE DEV
            - resolve attribute unique naming 
                - attribute has to be unique on the muscle level, or else it will conflict
                - possible solutions
                    - Attribute manager will append prefixes to the attribute when creating
            - what other attributes are necessary for this module?
            - add attribute method is being added to every class - not inherited
           
        action list
        
        :param name:
        :param side:
        """

        self.muscle_list = []
        self.base_surface = None
        self.module_surface = None

        self.module_build_list.extend([  # could be done with a super on the method
            self._duplicate_surface,
            self._build_muscle_list,
            # self._create_module_control_attributes,
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

        self.muscle_list.append(muscle_object)  # redundant
        self.sub_module_list.append(muscle_object)  # redundant - either one or the other

    # getters
    def get_module_surface(self):
        return self.module_surface

    # build methods
    def _duplicate_surface(self):
        self.module_surface = mc.duplicate(self.base_surface,
                                           name=self.tp_name.build(name=self.module_name,
                                                                   side=self.module_side,
                                                                   node_type='geometry'))[0]
        try:
            mc.parent(self.module_surface, world=True)
        except RuntimeError as err:
            print('[{}] Duplicate surface "{}", is already in world space. Proceeding...'.format(
                err, self.module_surface))
            # print('[Location] {}'.format(traceback.format_exc()))

        self.module_group_dict['rig_geometry'].append(self.module_surface)

    def _build_muscle_list(self):
        for muscle in self.muscle_list:
            muscle.build_module()
            self.module_group_dict['sub_module'].append(muscle.get_module_top_group())


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

    def get_control_attribute(self):
        return self.module_attribute_manager.get_attribute_object_list()[0]

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

        if len(self.point_list) > 4:
            # IF statement is necessary because after 5 points curve parameter > 1
            curve_shape = mc.listRelatives(self.curve, shapes=1)[0]
            curve_degree = mc.getAttr(curve_shape + ".degree")
            curve_spans = mc.getAttr(curve_shape + ".spans")

            # rebuild stage added to ensure the curve parameter is 0 to 1
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

        self.module_group_dict['curve'].append(self.curve)

    def _get_parameter_distribution(self):
        """
        Given the amount of desired segments on a curve, it will return
        a list of respective parameters
        """
        distribution = tpDist.Tp2dDistribute()
        distribution.set_amount(self.joint_amount)
        distribution.set_limit_start(self.limit_start)
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
        # self.module_attribute_manager.add_attribute_division('module_ctrl', 'CONTROLS')

        pull_attribute = self.module_attribute_manager.add_attribute(
            '_'.join([self.module_side, self.module_name, 'pull']),
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
        """
        Creates an IK Spline from first to last created joint chain
        """
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
