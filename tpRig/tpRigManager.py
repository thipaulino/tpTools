"""
Module Description

the class will be the parent of all other classes, such as the modules

Ideally, instead of copying attributes from module to module until it surfaces on the rig top group,
by inheriting this class, we should be able to add the necessary attributes directly to the rig
top group, and avoid creating loops or complex solutions to attribute creation.

"""


class tpRig:
    def __init__(self):
        pass

    def build_rig(self):
        pass

    def _setup_modules(self):
        pass

    def _setup_rig_groups(self):
        pass

    def _import_skin_clusters(self):
        pass
