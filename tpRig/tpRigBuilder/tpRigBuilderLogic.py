import tpRig.tpRigBuilder.modules.tpUtilities as tpProject
reload(tpProject)
import tpRig.tpRigBuilder.stacks.tpFaceRig as tpFace
reload(tpFace)
# import tpRig.tpRigBuilder.tpModule as tpModule
# import tpRig.tpRigManager_FaceB as tpRigManager
# reload(tpRigManager)

"""
Responsible for building the rig systems

- What is the relationship of the builder class with the rig and module classes?
    - Is it a parent class
    - Is it being called inside of the rig class
- Who is responsible for holding the Register method?
- What is the rig structure?
    - Rig
        - Bind Skeleton
        - Module?

"""


class TpRigBuilderLogic:

    def __init__(self):
        # self.rig_template_obj = tpRigManager.PostBuildUtils()
        self.module_object = tpFace.build_stack()

    def get_buildable_methods(self):
        # return self.rig_template_obj.get_registered_build_methods()
        return self.module_object.get_action_dict_list()

