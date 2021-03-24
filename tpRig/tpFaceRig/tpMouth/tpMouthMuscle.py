import tpRig.tpModule as mod
import tpRig.tpRigUtils as tpu
reload(tpu)
import tpRig.tpNameConvention as tpName
reload(tpName)
import tpVertexCatalogue.tpVertexCatalogue_logic as tpv
import tpRig.tp2dDistribute as tpDist
import maya.cmds as mc


class TpMouthMuscle(mod.TpModule):

    def __init__(self):
        super(TpMouthMuscle, self).__init__()

        self.module_name = 'mouth_muscle'

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

    def build(self):
        pass

    def build_module_surface(self):
        # enter loop by label
        #   copy surface from main for each muscle
        #   store data
        pass

    def assign_catalogue_classes(self):
        # get skull vertex cat data
        skull_json_dir = 'tpRig/tpFaceRig/tpMouth/mouthData/tp_skull_vtx_catalogue.json'
        self.skull_vtx_cat = tpv.TpVertexCatalogue()
        self.skull_vtx_cat.import_json_from_dir(skull_json_dir)

        # get jaw vertex cat data
        jaw_json_dir = 'tpRig/tpFaceRig/tpMouth/mouthData/tp_jaw_vtx_catalogue.json'
        self.jaw_vtx_cat = tpv.TpVertexCatalogue()
        self.jaw_vtx_cat.import_json_from_dir(jaw_json_dir)

        # get surface vertex cat data
        muzzle_json_dir = 'tpRig/tpFaceRig/tpMouth/mouthData/tp_muzzleSurface_vtx_catalogue.json'
        self.muzzle_vtx_cat = tpv.TpVertexCatalogue()
        self.muzzle_vtx_cat.import_json_from_dir(muzzle_json_dir)

    def assemble_master_catalogue(self):
        # get only not empty labels in all catalogues
        muzzle_cat = self.muzzle_vtx_cat.get_catalogue()
        for label in muzzle_cat:
            for side in muzzle_cat[label]:
                if side:
                    pass

    def build_muscle(self):
        for muscle_name in self.muscle_point_dict:
            for side in self.muscle_point_dict[muscle_name]:
                muscle_object = TpFaceMuscle(name=muscle_name, side=side)

                muscle_object.add_point_list(self.muscle_point_dict[muscle_name][side])
                muscle_object.set_joint_amount(5)
                muscle_object.set_limit_start(0.6)  # muscle length will be 0.4
                muscle_object.set_limit_end(1)

                muscle_object.build()
                self.muscle_object_dict.update({muscle_object.get_module_name(): muscle_object})

    def create_control_hub_node(self):  # consider using module top group
        """
        The control node holds the muscle_pull attribute, which will be used
        to dive the system
        """
        self.control_plug = mc.createNode('controller', name=self.tpName.build(name=self.name, side=self.side,
                                                                               node_type='controller'))
        self.control_plug_attribute = 'muscle_pull'
        mc.addAttr(self.control_plug, longName=self.control_plug_attribute, keyable=True,
                   attributeType='double', defaultValue=0, minValue=0, maxValue=1)
        mc.addAttr(self.control_plug, longName='metadata', dataType='string')

    def create_hub_attributes(self):
        for muscle in self.muscle_object_dict:
            mc.addAttr(self.module_control_node, longName=muscle, keyable=True,
                       attributeType='double', defaultValue=0, minValue=0, maxValue=1)

    def connect_muscles_to_control_hub(self):
        for muscle_obj in self.muscle_object_dict.values():
            name = muscle_obj.get_module_name()
            muscle_obj.muscle_control_attribute_connect_from('{}.{}'.format(self.module_control_node, name))

    def import_surface_skinning_data(self):  # will be added after built
        pass

    def assign_module_data(self):
        pass


class TpMuscleSet(mod.TpModule):

    def __init__(self, name, side):
        super(TpMuscleSet, self).__init__(name, side)
        self.muscle_list = []
        self.surface = None

    def build(self):
        pass

    def add_surface(self, surface):
        """or duplicate, or has to be provided already"""
        self.surface = surface

    def add_muscle(self, point_list, side, joint_amount, limit_start, limit_end):
        muscle_object = TpFaceMuscle(name=self.module_name, side=side)
        muscle_object.add_point_list(point_list)
        muscle_object.set_joint_amount(joint_amount)
        muscle_object.set_limit_start(limit_start)  # muscle length will be 0.4
        muscle_object.set_limit_end(limit_end)

        self.muscle_list.append(muscle_object)

    def build_muscle_list(self):
        for muscle in self.muscle_list:
            muscle.build()

    def create_control_node(self):
        pass

    def connect_controls(self):
        pass


class TpFaceMuscle(mod.TpModule):

    def __init__(self, name='tpMuscle', side='center'):
        super(TpFaceMuscle, self).__init__()
        """
        Creates a single muscle module
        :param name:
        :param side:
        """
        self.tpName = tpName.NameConvention()
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

        self.module_hub = None
        self.control_plug = None
        self.control_plug_attribute = None

        self.control_locator = None  # connected to pci_node, drives ik_handle

        self.module_build_list.extend([
            self.__build_curve,
            self.__get_parameter_distribution,
            self.__create_point_on_curve_info_node,
            self.__create_driver_locator,
            self.__create_set_range_node,
            self.create_control_plug_node,
            self.__make_control_node_connections,
            self.__build_fk_chain,
            self.__create_ik_spline,
            self.__create_bind_joint,
            self.__pack_and_ship,
        ])

    # control methods
    def muscle_control_attribute_connect_from(self, in_plug):
        mc.connectAttr(in_plug, '{node}.{attr}'.format(node=self.control_plug, attr=self.control_plug_attribute))

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

    # assemble methods
    def build(self):
        self.__build_curve()
        self.__get_parameter_distribution()
        self.__create_point_on_curve_info_node()
        self.__create_driver_locator()
        self.__create_set_range_node()
        self.create_control_plug_node()
        self.__make_control_node_connections()
        self.__build_fk_chain()
        self.__create_ik_spline()
        self.__create_bind_joint()
        self.__pack_and_ship()

    def create_top_group_node(self):
        self.top_group = mc.group(empty=True, name=self.tpName.build(name=self.module_name,
                                                                     side=self.module_side,
                                                                     group=True))

    def __build_curve(self):
        self.degree = 3 if len(self.point_list) >= 4 else 1
        self.curve = mc.curve(degree=self.degree,
                              p=self.point_list,
                              name=self.tpName.build(name=self.module_name + '_path',
                                                     side=self.module_side,
                                                     node_type='curve'))

    def __get_parameter_distribution(self):
        """
        Given the amount of desired segments on a curve, it will return
        a list of respective parameters
        """
        distribution = tpDist.Tp2dDistribute()
        distribution.set_amount(self.joint_amount)
        distribution.set_limit_start(self.limit_start)  # chain starts in the middle of the curve
        self.parameter_list = distribution.get_parameter_list()

    def __create_point_on_curve_info_node(self):
        self.pci_node = mc.createNode('pointOnCurveInfo',
                                      name=self.tpName.build(name=self.module_name,
                                                             side=self.module_side,
                                                             node_type='pointOnCurveInfo'))
        mc.connectAttr(self.curve + ".worldSpace", self.pci_node + ".inputCurve")

    def __create_driver_locator(self):
        """
        The locator will slide along the curve using the PCI node
        and pull the root CV on the IK splice curve
        """
        self.control_locator = mc.spaceLocator(name=self.tpName.build(name=self.module_name,
                                                                      side=self.module_side,
                                                                      node_type='locator'))[0]
        mc.setAttr(self.pci_node + ".parameter", self.parameter_list[0])
        mc.connectAttr(self.pci_node + ".position", self.control_locator + ".t")

        locator_group = mod.TpModuleGroup(name=self.module_name,
                                          component_type='locator')
        locator_group.add_item(self.control_locator)
        self.module_group_list.append(locator_group)

    def __create_set_range_node(self):
        """
        Remaps the input value from 0 to 1, to the parameter range on the curve
        to create muscle pull
        """
        self.pci_set_range = mc.createNode('setRange',
                                           name=self.tpName.build(name=self.module_name,
                                                                  side=self.module_side,
                                                                  node_type='setRange'))
        mc.setAttr(self.pci_set_range + '.oldMin.oldMinX', 0)
        mc.setAttr(self.pci_set_range + '.oldMax.oldMaxX', 1)
        mc.setAttr(self.pci_set_range + '.min.minX', self.limit_start)
        mc.setAttr(self.pci_set_range + '.max.maxX', 0)

    def create_control_plug_node(self):
        """
        The control node holds the muscle_pull attribute, which will be used
        to dive the system
        """
        self.control_plug = mc.createNode('controller',
                                          name=self.tpName.build(name=self.module_name,
                                                                 side=self.module_side,
                                                                 node_type='controller'))
        self.control_plug_attribute = 'muscle_pull'
        mc.addAttr(self.control_plug, longName=self.control_plug_attribute, keyable=True,
                   attributeType='double', defaultValue=0, minValue=0, maxValue=1)
        mc.addAttr(self.control_plug, longName='metadata', dataType='string')

    def __add_attribute_to_module_control(self):
        self.control_plug_attribute = 'muscle_pull'
        mc.addAttr(self.control_plug,
                   longName=self.control_plug_attribute,
                   keyable=True,
                   attributeType='double',
                   defaultValue=0,
                   minValue=0,
                   maxValue=1)
        mc.addAttr(self.control_plug, longName='metadata', dataType='string')

    def __make_control_node_connections(self):
        mc.connectAttr(self.control_plug + '.muscle_pull', self.pci_set_range + '.value.valueX')
        mc.connectAttr(self.pci_set_range + '.outValue.outValueX', self.pci_node + '.parameter')

    def __build_fk_chain(self):
        for n, parameter in enumerate(self.parameter_list):
            position = mc.pointOnCurve(self.curve, parameter=parameter)
            mc.select(clear=True)
            joint = mc.joint(radius=self.joint_radius, name=self.tpName.build(name=self.module_name,
                                                                              side=self.module_side,
                                                                              index=n+1,
                                                                              node_type='joint'))
            mc.xform(joint, translation=position, worldSpace=True)
            # joint = tpu.joint_on_curve_parameter(self.curve, parameter,)
            self.fk_joint_list.append(joint)

        tpu.parent_in_list_order(self.fk_joint_list)

        # orient joints
        for joint in self.fk_joint_list:
            mc.joint(joint, edit=True, orientJoint="xyz", secondaryAxisOrient="yup",
                     children=True, zeroScaleOrient=True)

    def __create_ik_spline(self):
        ik_handle_data = mc.ikHandle(startJoint=self.fk_joint_list[0],
                                     endEffector=self.fk_joint_list[-1],
                                     solver="ikSplineSolver",
                                     name=self.tpName.build(name=self.module_name,
                                                            side=self.module_side,
                                                            node_type='ikHandle'))
        self.ik_handle = ik_handle_data[0]
        self.ik_handle_effector = ik_handle_data[1]
        self.ik_handle_curve = mc.rename(ik_handle_data[2], self.tpName.build(name=self.module_name + '_ik',
                                                                              side=self.module_side,
                                                                              node_type='curve'))

        self.root_cluster = mc.cluster(self.ik_handle_curve + '.cv[0]',
                                       name=self.tpName.build(name=self.module_name,
                                                              side=self.module_side,
                                                              node_type='cluster'))[1]
        mc.parentConstraint(self.control_locator, self.root_cluster, maintainOffset=False)

    def __create_bind_joint(self):
        """
        Bind joint will be place and parented to the last joint on the Ik spline
        """
        mc.select(clear=True)
        self.bind_joint = mc.joint(radius=self.joint_radius, name=self.tpName.build(name=self.module_name,
                                                                                    side=self.module_side,
                                                                                    node_type='bind_joint'))
        self.bind_joint_group = mc.group(self.bind_joint, name=self.tpName.build(name=self.module_name,
                                                                                 side=self.module_side,
                                                                                 node_type='bind_joint',
                                                                                 group=True))
        mc.parentConstraint(self.fk_joint_list[-1], self.bind_joint_group, maintainOffset=False)

    def create_groups(self):
        for group in self.module_group_list:
            group.do_group()
            group.parent_under(self.top_group)

    def __pack_and_ship(self):
        pass


"""
Getting started 20.01.2021

surface = given

muscles
    risorius,
    buccinator,
    deprAnguli,
    zygMajor,
    zygoMinor,
    levatorAnguli,
    levatorLabiiSup,
    levatorLabiiSAN,
    depressorLabii,
    levatorNasi,
    sup_lip_roll,
    mentalis,
    pucker

- get skull geo and check
- catalogue point on muzzle_geo and skull_geo for each muscle
- repurpose flexiLoft tool for rig application
- build muscle chains based on vertex reference

- duplicate muzzle_geo for the number of muscles
- bind chain to its surface
- import weights

create surface follicles
create follicle joints

return all created nodes

Action List
    combine skull geo - PASS
    make uvs for skull/jaw - DONE
    export skull_geo for module use 
    export muzzle_geo for module use 

    catalogue points for each muscle on skull/muzzle - DONE
    export JSON for module use - DONE

    double check all points for intended use
        remove points that needs to be averaged
        leave only points that defines the curve

    create muscle control hub node
    create curve - DONE
        create function to create curve from 2 or more input positions

    ## ik spline based muscle approach - DONE
        create function to distribute joint along curve based on UV - DONE
        create joints on parameters
        orient joints 
        parent joint on fk order
        turn fk chain into ik spline
        create locator at end joint position/parameter (muscle bone insertion)
        parent IK handle to locator
        create and connect point on curve info (PCI) info node
        plug in locator to node
        set parameter to the same as last joint in chain
        connect PCI node parameter to range retarget (setRange) node
        connect range retarget to muscle hub
        create bind joint on same location as first joint in chain
        top group it


    ## single joint on rails approach
        create point on curve info node(PCI) 
        connect PCI to curve
        create locator
        plug locator to PCI
        create joint
        top group joint
        constraint joint group to locator


    # consider template stage to adjust positions manually    

    add skull geo to python module folder
    add muzzle geo to python module folder

    create locator from point average
    build curve from two or more points

    flexiloft - repurpose for muscle build
        build fk chain
        create ik spline

    skinCluster import/export - repurpose

    setup new clean project 
        reposition Joaquins head geo to real world metrics
        same for skull geometry 
        same for body geometry




"""
