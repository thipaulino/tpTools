import tpRig.tpTemplate as tpTemplate


class TpFaceTemplate(tpTemplate.TpTemplate):

    def __init__(self):
        super(TpFaceTemplate, self).__init__()
        """
        Class dedicated to managing the template geo and data.
        
        The class should be able to 
            - import the template
            - export modified template 
            - provide positioning data when requested.
        
        """

    def build_template(self):
        pass

    def import_template_geo(self):
        pass

    def export_template_geo(self):
        """
        Exports modified template geo.
        Stores it in project file and version control.
        :return:
        """

    def build_skull_warp_setup(self):
        pass

    def get_mouth_muscle_position_data(self):
        pass


class TpTemplateItem:

    def __init__(self):
        pass