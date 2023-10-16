import tpRig.tpRigBuilder.modules.tpUtilities as tpUtilities
import tpRig.tpRigBuilder.modules.tpProject as tpProject
import tpRig.tpRigBuilder.tpModule as tpModule
reload(tpUtilities)
reload(tpProject)
reload(tpModule)


def build_stack():
    stack_module_obj = tpModule.Module(module_name='main_stack', module_has_top_item=False)

    utils_module_obj = tpUtilities.build_module_object(background_color='dark_green')
    project_module_obj = tpProject.build_module_object(background_color='dark_cyan')

    stack_module_obj.add_module(utils_module_obj)
    stack_module_obj.add_module(project_module_obj)

    return stack_module_obj




