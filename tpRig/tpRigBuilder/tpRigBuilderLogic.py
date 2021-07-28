import tpRig.tpRigManager as tpRigManager
reload(tpRigManager)

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
        self.rig_template_obj = tpRigManager.tpRig()

    def get_buildable_methods(self):
        return self.rig_template_obj.get_registered_build_methods()

