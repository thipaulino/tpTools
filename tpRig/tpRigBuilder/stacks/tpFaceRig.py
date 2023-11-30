import tpRig.tpRigBuilder.modules.tpUtilities as tpUtilities
import tpRig.tpRigBuilder.modules.tpProject as tpProject
import tpRig.tpRigBuilder.tpModule as tpModule
import tpRig.tpRigBuilder.modules.tpPostBuildUtils as tpPostBuildUtils
reload(tpUtilities)
reload(tpProject)
reload(tpModule)
reload(tpPostBuildUtils)

"""
Consider the possibility of having the scripts in the individual character project,
so that if there is something customized on the script
that can be retrieved later on.
"""


def build_stack():
    stack_module_obj = tpModule.Module(module_name='main_stack', module_has_top_item=False)

    utils_module_obj = tpUtilities.build_module_object(background_color='dark_green')
    project_module_obj = tpProject.build_module_object(background_color='dark_cyan')
    post_utils_mod_obj = tpPostBuildUtils.build_module_object(background_color='dark_magenta')

    stack_module_obj.add_module(utils_module_obj)
    stack_module_obj.add_module(project_module_obj)
    stack_module_obj.add_module(post_utils_mod_obj)

    return stack_module_obj

