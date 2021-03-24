
class NameConvention:

    def __init__(self):

        self.joint = 'jnt'
        self.group = 'grp'
        self.curve = 'crv'
        self.surface = 'srf'
        self.geometry = 'geo'
        self.locator = 'loc'
        self.cluster = 'cls'
        self.clusterHandle = 'clsHdl'
        self.handle = 'hdl'
        self.follicle = 'flc'
        self.left = 'l'
        self.right = 'r'
        self.center = 'ct'

        self.name_dict = {
            'type': {
                'joint': 'jnt',
                'bind_joint': 'bind_jnt',
                'group': 'grp',
                'curve': 'crv',
                'geometry': 'geo',
                'follicle': 'flc',
                'pointOnCurveInfo': 'pci',
                'setRange': 'setRange',
                'controller': 'controller',
                'ikHandle': 'ikHdl',
                'locator': 'loc',
                'cluster': 'cls'
            },
            'side': {
                'left': 'l',
                'left_superior': 'l_sup',
                'left_inferior': 'l_inf',
                'right': 'r',
                'right_superior': 'r_sup',
                'right_inferior': 'r_inf',
                'center': 'ct',
                'center_superior': 'ct_sup',
                'center_inferior': 'ct_inf',
                'superior': 'sup',
                'inferior': 'inf'
            }
        }

    def build(self, name='tpNode', side=None, node_type=None, index=None, group=False):
        name_list = []

        if side is not None:
            name_list.append(self.name_dict['side'][side])

        name_list.append(name)

        if index is not None:
            name_list.append('{:02d}'.format(index))

        if node_type is not None:
            name_list.append(self.name_dict['type'][node_type])

        if group:
            name_list.append(self.name_dict['type']['group'])

        return '_'.join(name_list)

    def joint(self):
        return self.joint

    def group(self):
        return self.group

    def curve(self):
        return self.curve

    def surface(self):
        return self.surface

    def geometry(self):
        return self.geometry

    def locator(self):
        return self.locator

    def cluster(self):
        return self.cluster

    def cluster_handle(self):
        return self.clusterHandle



