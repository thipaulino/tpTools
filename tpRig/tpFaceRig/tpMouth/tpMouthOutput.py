import tpRig.tpModule as mod
import tpRig.tpRigUtils as tpu
import tpRig.tpNameConvention as tpName
import tpVertexCatalogue.tpVertexCatalogue_logic as tpv
import maya.cmds as mc

"""
Module Development - Mouth Output

- Add left and right to vertex label data - DONE
    # Else, how to aquire data?
    # Issue - without l_ r_ dict will conflict
        - Add layers inside label - keep left, righ, center, inside
        - possible to add more data if necessary this way
"""


class TpMouthOutput(mod.TpModule):

    def __init__(self):
        super(TpMouthOutput, self).__init__()

        self.module_name = 'mouth_output'

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

    def build(self):
        self.setup_oral_geo()
        self.import_vertx_catalog_data()

        self.create_follicles()
        self.group_follicles()

        self.create_joints()
        self.group_joints()

        self.assign_module_data()

    def set_oral_geo(self, geo):
        self.template_oral_geo = geo

    def set_joint_radius(self, joint_radius):
        self.joint_radius = joint_radius

    def setup_oral_geo(self):
        self.output_oral_geo = mc.duplicate(self.template_oral_geo,
                                            name=self.tpName.build('output', 'center', 'geometry'))[0]
        mc.parent(self.output_oral_geo, world=True)
        mc.delete(self.output_oral_geo, constructionHistory=True)

    def import_vertx_catalog_data(self):
        self.vtx_cat.import_json_from_dir(self.vtx_cat_file_path)

    def create_follicles(self):
        """
        Creates surface follicles based on json catalogue data
        :return:
        """
        self.vtx_cat.set_geo(self.output_oral_geo)
        labels = self.vtx_cat.list_labels()

        for label in labels:
            self.vtx_cat.set_label(label)
            label_items = self.vtx_cat.list_label_active_items()
            item_temp_dict = {}

            for item in label_items:
                self.vtx_cat.set_label_item(item)
                item_vtx_list = self.vtx_cat.get_item_data_as_fullpath()
                follicle_temp_list = []

                for n, vertex in enumerate(item_vtx_list):
                    follicle = tpu.follicle_on_vertex(vertex, self.tpName.build(name=label, side=item,
                                                                                node_type='follicle', index=n))
                    follicle_temp_list.append(follicle)

                item_temp_dict.update({item: follicle_temp_list})

            self.follicle_dict.update({label: item_temp_dict})

    def create_joints(self):
        """
        Create joints and parent constrain them to created follicles
        :return:
        """
        for label in self.follicle_dict:
            item_temp_dict = {}

            for item in self.follicle_dict[label]:
                joint_temp_list = []

                for n, follicle in enumerate(self.follicle_dict[label][item]):
                    mc.select(clear=True)
                    joint = mc.joint(radius=self.joint_radius,
                                     name=self.tpName.build(name=label, side=item, node_type='joint', index=n))
                    mc.parentConstraint(follicle, joint, maintainOffset=False)
                    joint_temp_list.append(joint)

                item_temp_dict.update({item: joint_temp_list})

            self.joint_dict.update({label: item_temp_dict})

    def group_follicles(self):
        """
        Group created follicles into sub-groups based on labels and items
        :return:
        """
        label_group_list = []

        for label in self.follicle_dict:
            item_group_list = []

            for item in self.follicle_dict[label]:
                item_group = mc.group(self.follicle_dict[label][item],
                                      name=self.tpName.build(name=label, side=item, node_type='follicle', group=True))
                item_group_list.append(item_group)

            label_group = mc.group(item_group_list,
                                   name=self.tpName.build(name=label, node_type='follicle', group=True))
            label_group_list.append(label_group)

        self.follicle_group = mc.group(label_group_list,
                                       name=self.tpName.build(name='follicle', node_type='follicle', group=True))

    def group_joints(self):
        """
        Group created joints into sub-groups based on labels and items
        :return:
        """
        label_group_list = []

        for label in self.joint_dict:
            item_group_list = []

            for item in self.joint_dict[label]:
                item_group = mc.group(self.joint_dict[label][item],
                                      name=self.tpName.build(name=label, side=item, node_type='joint', group=True))
                item_group_list.append(item_group)

            label_group = mc.group(item_group_list,
                                   name=self.tpName.build(name=label, node_type='joint', group=True))
            label_group_list.append(label_group)

        self.joint_group = mc.group(label_group_list,
                                    name=self.tpName.build(name='joint', node_type='joint', group=True))

    def assign_module_data(self):
        """
        Assign groups, nodes and data to proper slots in class
        :return:
        """
        self.geometry_list = [self.output_oral_geo]
        self.follicle_list = [follicle for label in self.follicle_dict for follicle in self.follicle_dict[label]]
        self.joint_list = [joint for label in self.joint_dict for joint in self.joint_dict[label]]
        self.joint_bind_list = [joint for label in self.joint_dict for joint in self.joint_dict[label]]

        self.module_group_list = [self.follicle_group, self.joint_group]

