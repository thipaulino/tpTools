from __future__ import division
import tpUtils as tpu
import maya.cmds as mc
import maya.OpenMaya as om
import maya.api.OpenMaya as om2
import maya.OpenMayaUI as OpenMayaUI
import json
import struct
import glob
import math
import os


# import tpUtils as tp
# reload(tp)
#
# loc = tp.RigTemplate()
# loc.export_template_data()
# loc.import_template_data()
# loc.rebuild_template_from_data(loc.environment_data)
#
# loc.set_loc_parent_sel_order()
# loc.load_sys()
# loc.sys_members()
# loc.update_template_data()
# loc.load_loc()
# loc.update_loc()
# loc.new_sys('head')
#
# neck_loc = ['d1', 'd2', 'd3', 'd4', 'd5', 'd6']
# for item in neck_loc:
#     loc.new_loc(item)
#
# loc.new_loc('t4')
#
# loc.rebuild_template()
# loc.parent_template()
# loc.rebuild_sys()
# loc.parent_sys()
# loc.rebuild_sys_from_data(loc.sys_data)
# loc.list_systems()
#
# loc.sys_members()
# loc.sys_members_data()
# loc.update_sys_data()
# loc.update_loc_data()
# loc.update_template_data()
# loc.loc_set_index(3)
# loc.template_members()
# loc.template_members_data()
#
# loc.set_root()
# loc.loc
# loc.loc_data
#
# loc.set_loc_sys()
# loc.list_sys_locs()
# loc.set_sys_parent()


class RigTemplate:

    """
    Class development:
        add template joint scale
        add vertex sets to store custom vertex data - DONE
        add edge sets to store custom edge data
        duplicate sys with different name
        add name construct method
            standard name construction across class
        add mirror name method
            if center keeps center
        add system parent to mirror sys
        create rigTemplate ui?
        switch names
            environment ?
            system - module
            locator - handle / unit / joint / proxy

        add cube shape to joint
        add annotation to modules
        add position by vertex average - sets
            switchable mesh name
            manual position override
        add set index by parent order
        add mirror selected joints
        add export single template module

        add nested systems (necessary?)
            neck sys would have: sterno++

        use connect wordMatrix to offsetParentMatrix
            instead of parent constraint

        reset index
            from parent data
            from selection order

        split class into
            handle
            module
            template

        fixes
            error when root not assigned
            set root happening on locator level
            error when no locator is not loaded - DONE
            connection lines double transforming - DONE

        add mirror system - DONE
            add system prefix - DONE
            check for center cases
        add root joint on environment - DONE
            check consequences to mirror
            always loads root sys and root loc/joint/unit on init - DONE
            handle root redundancy - stored data vs root on init - DONE
        export/import system data - DONE
        export/import template data - DONE
        parent systems - DONE
            add attribute to loc - DONE
            add attribute to sys - DONE
        rebuild template from data - DONE
        set module root - DONE
            update position on rebuild - DONE
        dev update_template_data - DONE
        create template group dict - DONE
        line between locators - DONE
        parent system - DONE
        rebuild system - DONE
    """

    def __init__(self):
        # loaded parts / entities
        self.tag_node = 'tp_rigSystems_rigTemplate'
        self.root_sys = 'root_sys_grp'
        self.environment_grp = ''
        self.sys = ''
        self.loc = ''

        # class parts data holders
        self.tag_data = {}
        self.environment_data = {}
        self.sys_data = {}
        self.loc_data = {}

        # cache data - temporary
        self.cache_template_data = {}
        self.cache_sys_data = {}
        self.cache_loc_data = {}

        # side standards
        self.prefix_standards = {
            'left': 'l',
            'right': 'r',
            'center': 'ct'}

        self.standards = {
            'prefix': '',
            'parts': {'handle': 'loc',
                      'module': 'sys',
                      'environment': 'template'}}

        self.data_templates = {
            'environment_data': {
                'name': '',
                'group': '',
                'systems': []},

            'sys_data': {
                'name': '',
                'group': '',
                'prefix': '',
                'position': {
                    't': [],
                    'r': [],
                    's': []},
                'locators': {},
                'root': '',
                'sys_parent': ''},

            'loc_data': {
                'parent': '',
                'prefix': '',
                'unique_name': '',
                'name': '',
                'index': '',
                'position': {
                    't': [],
                    'r': [],
                    's': []},
                'custom_sets': {
                    'vertex': {},
                    'edge': {},
                    'vertex_avg': []},
                'system_grp': '',
                'system_plug': '',  # Used to retrieve loc name
                'ref_vertex': [],
                'joint': '',
                'root': False},

            'tag_data': {
                'creation_date': '',
                'last_modified': '',
                'original_file': '',
                'class_version': '',
                'id': '',
                'credits': 'Create By Thiago Paulino'}}

        self.init_template_sys()

    # CREATE SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def init_template_sys(self):
        """
        Initializes system by searching for tag for tp_rigSystems_rigTemplate tag and getting environment
        if nonexistent, creates tag and environment
        """
        if not mc.objExists(self.tag_node):
            self.tag_node = mc.createNode('controller', name='tp_rigSystems_rigTemplate')
            mc.addAttr(self.tag_node, longName='metadata', dataType='string')
            mc.addAttr(self.tag_node, longName='environment_data', dataType='string', multi=True,
                       indexMatters=False)
            self.commit_data(self.tag_node, self.data_templates['tag_data'])
            self.new_environment()

        # load environment
        self.tag_data = eval(mc.getAttr('{}.metadata'.format(self.tag_node)))
        self.environment_grp = mc.listConnections('{}.environment_data'.format(self.tag_node), s=1, d=0)[0]
        self.environment_data = eval(mc.getAttr('{}.metadata'.format(self.environment_grp)))

        self.load_loc(self.sys_members(self.root_sys)[0])

    def new_environment(self, name=''):
        """
        Creates new group for all template systems with necessary attributes
        Connects to tag group for easy class access
        """
        self.environment_data = self.data_templates['environment_data']
        self.environment_data['group'] = mc.group(name='rig_template_grp', em=1)

        mc.addAttr(self.environment_data['group'], longName='metadata', dataType='string')
        mc.addAttr(self.environment_data['group'], longName='sys_data', dataType='string', multi=True,
                   indexMatters=False)
        mc.connectAttr('{}.metadata'.format(self.environment_data['group']),
                       '{}.environment_data'.format(self.tag_node),
                       nextAvailable=True)
        self.commit_data(self.environment_data['group'], self.environment_data)

        self.environment_data = eval(mc.getAttr('{}.metadata'.format(self.environment_data['group'])))

        self.new_sys('root')
        self.new_loc('root')

    def new_sys(self, name, prefix=''):
        """
        Creates new group for module/system with necessary data attributes and connections
        :param name:
        :param prefix:
        """

        prefix_edit = '{}_'.format(prefix) if prefix else ''
        self.sys_data = self.data_templates['sys_data']
        self.sys_data['prefix'] = prefix
        self.sys_data['name'] = name if name else 'tempName'
        self.sys_data['group'] = mc.group(name='{}{}_sys_grp'.format(prefix_edit, name), empty=True)
        mc.parent(self.sys_data['group'], self.environment_data['group'])
        mc.select(cl=True)

        mc.addAttr(self.sys_data['group'], longName='root', dataType='string')
        mc.addAttr(self.sys_data['group'], longName='parent', attributeType='message')
        mc.addAttr(self.sys_data['group'], longName='child', attributeType='message')
        mc.addAttr(self.sys_data['group'], longName='sys_parent', attributeType='message')
        mc.addAttr(self.sys_data['group'], longName='metadata', dataType='string')
        mc.addAttr(self.sys_data['group'], longName='loc_data', dataType='string',
                   multi=True, indexMatters=False)

        mc.connectAttr('{}.metadata'.format(self.sys_data['group']),
                       '{}.sys_data'.format(self.environment_data['group']),
                       nextAvailable=True)

        self.commit_data(self.sys_data['group'], self.sys_data)

    def new_loc(self, unique_name='', prefix='', loc_index='', system='', root=False):
        """
        Creates new template locator with metadata attribute
        :param prefix:
        :param unique_name:
        :param loc_index:
        :param system:
        :param root:
        """
        if system:
            self.load_sys(system)
        if not loc_index:
            loc_list = self.sys_members()  # place outside loc creation - encapsulate
            loc_index = 1 if not loc_list else tpu.get_next_index(loc_list)

        prefix = self.sys_data['prefix'] if self.sys_data['prefix'] else prefix
        prefix_edit = '{}_'.format(prefix) if prefix else ''
        loc_name = '{}_'.format(unique_name) if unique_name else ''
        name = '{}{}{}_{:02d}_loc'.format(prefix_edit, loc_name, self.sys_data['name'], loc_index)

        mc.select(cl=1)
        self.loc = mc.joint(name=name)
        mc.addAttr(self.loc, longName='metadata', dataType='string')
        mc.addAttr(self.loc, longName='parent', attributeType='message')
        mc.addAttr(self.loc, longName='child', attributeType='message')
        mc.addAttr(self.loc, longName='sys_child', attributeType='message')
        mc.connectAttr('{}.metadata'.format(self.loc), '{}.loc_data'.format(self.sys_data['group']),
                       nextAvailable=True)
        if root:
            self.set_root()  # re-evaluate

        self.loc_data = self.data_templates['loc_data']
        self.loc_data.update({
            'prefix': prefix,
            'unique_name': unique_name,
            'system_grp': self.sys_data['group'],
            'system_plug': mc.listConnections('{}.metadata'.format(self.loc), d=1, s=0, p=1)[0].split('.')[1],
            'name': self.loc,
            'root': True if root else False})
        self.commit_data(self.loc, self.loc_data)

        mc.parent(self.loc, self.sys_data['group'])

    def new_loc_array(self, name, amount):
        pass

    # REBUILD SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def rebuild_template_from_data(self, template_data):
        """
        rebuilds the whole tamplate based on provided data
        :param template_data:
        """
        # rebuild environment
        self.init_template_sys()
        # deletes existing root module
        mc.delete(self.root_sys)

        # rebuild all systems
        for sys in template_data['systems']:
            self.rebuild_sys_from_data(template_data['systems'][sys])

        # rebuild system parent connection
        # obs. has to be in template so that all systems are created prior to connect
        for sys in template_data['systems']:
            self.load_sys(sys)
            if template_data['systems'][sys]['sys_parent']:
                self.set_sys_parent(template_data['systems'][sys]['sys_parent'])

        self.update_template_data()

    def rebuild_template(self):
        """
        Queries template data, deletes template and rebuilds from data
        :return:
        """
        self.update_template_data()
        mc.delete(self.environment_data['group'])
        self.rebuild_template_from_data(self.environment_data)

    def rebuild_sys_from_data(self, sys_data):
        """
        Rebuilds single system based on data dictionary
        :param sys_data:
        :return:
        """
        self.new_sys(sys_data['name'], sys_data['prefix'])

        # set group position to match root joint
        # mc.xform(self.sys_data['group'],
        #          t=sys_data['locators'][sys_data['root']]['position']['t'],
        #          ro=sys_data['locators'][sys_data['root']]['position']['r'],
        #          ws=True)

        for loc in sys_data['locators']:
            # rebuild locator
            self.new_loc(sys_data['locators'][loc]['unique_name'], prefix=sys_data['locators'][loc]['prefix'],
                         loc_index=sys_data['locators'][loc]['index'])
            self.loc_data = sys_data['locators'][loc]
            self.commit_data(self.loc, self.loc_data)

        for loc in self.sys_members():
            # reposition locator based on commited data
            self.load_loc(loc)
            self.update_loc()

        if sys_data['root']:
            # reconnects root locator to system according to data
            self.set_root(sys_data['root'])

        self.update_sys_data()

    def rebuild_sys(self):
        """
        Queries system data, deletes single system and rebuilds from data
        :return:
        """
        self.update_sys_data()
        mc.delete(self.sys_data['group'])
        self.rebuild_sys_from_data(self.sys_data)

    def reposition_system(self):
        root = mc.listConnections('{}.root'.format(self.sys_data['group']), s=True, d=False)[0]
        pass

    def name_construct(self):
        """
        prefix _ id _ sys _ index _ type
        """
        pass

    # LOAD SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def load_sys(self, system=''):
        group = system if system else mc.ls(sl=1)[0]
        self.load_sys_data(group)

    def load_sys_data(self, system=''):
        self.sys_data = eval(mc.getAttr('{}.metadata'.format(system)))

    def load_loc(self, loc=''):
        self.loc = loc if loc else mc.ls(sl=1)[0]
        self.load_loc_data()
        self.load_sys(self.loc_sys())

    def load_loc_data(self, data=''):
        data = data if data else mc.getAttr('{}.metadata'.format(self.loc))
        self.loc_data = eval(data)

    def load_env_data(self):
        self.environment_data = eval(mc.getAttr('{}.metadata'.format(self.environment_data['group'])))

    def list_systems(self):
        data = mc.listConnections('{}.sys_list'.format(self.environment_data['group']))
        return data

    def list_sys_locs(self, system=''):
        sys = system if system else self.sys_data['group']
        data = mc.listConnections('{}.loc_data'.format(sys))
        return data

    # UPDATE DATA SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def update_loc_data(self):
        parent = mc.listConnections('{}.parent'.format(self.loc), s=1, d=0)
        child = mc.listConnections('{}.child'.format(self.loc), s=0, d=1)

        self.loc_data.update({
            'name': self.loc,
            'parent': '' if parent is None else str(parent[0]),
            'child': '' if child is None else str(child[0]),
            'system_grp': self.loc_sys(),
            'position': {'t': mc.xform(self.loc, q=1, t=1, ws=1),
                         'r': mc.xform(self.loc, q=1, ro=1, ws=1),
                         's': mc.xform(self.loc, q=1, s=1, ws=1)},
            'index': self.loc_index(),
        })

        self.commit_data(self.loc, self.loc_data)

    def update_sys_data(self):
        members_data = self.sys_members_data()
        root = self.sys_root()
        parent = self.sys_parent()

        self.sys_data.update({
            'locators': members_data,
            'root': root,
            'sys_parent': parent})

        self.commit_data(self.sys_data['group'], self.sys_data)

    def update_template_data(self):
        self.environment_data['systems'] = self.template_members_data()
        self.commit_data(self.environment_data['group'], self.environment_data)

    def update_sys_locs_data(self):
        locators = self.sys_members()

        for loc in locators:
            self.load_loc(loc)
            self.update_loc_data()

        self.sys_data['locators'] = locators
        self.commit_data(self.sys_data['group'], self.sys_data)

    def update_loc(self):
        mc.xform(self.loc,
                 t=self.loc_data['position']['t'],
                 ro=self.loc_data['position']['r'],
                 ws=True)

        if self.loc_data['parent']:
            self.set_loc_parent(self.loc_data['parent'])

    # SET SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def commit_data(self, group, data):
        mc.setAttr('{}.metadata'.format(group), data, type='string')

    def commit_loc_data(self):
        mc.setAttr('{}.metadata'.format(self.loc), self.loc_data, type='string')

    def set_root(self, loc_choice=''):
        """
        Connect and sets current loc/joint to root attribute
        """
        loc = loc_choice if loc_choice else self.loc
        mc.connectAttr('{}.metadata'.format(loc), '{}.root'.format(self.sys_data['group']))

    def set_loc_sys(self, system=''):
        """
        Changes loaded locator system
        :param system:
        """
        self.load_sys(self.loc_sys())
        mc.disconnectAttr('{}.system_grp'.format(self.loc), '{}.loc_list'.format(self.sys_data['group']),
                          nextAvailable=1)
        self.loc_data['system_grp'] = system if system else mc.ls(sl=1)[0]
        self.load_sys(self.loc_data['system_grp'])
        mc.connectAttr('{}.system_grp'.format(self.loc), '{}.loc_list'.format(self.sys_data['group']),
                       nextAvailable=True)

        loc_list = self.sys_members(self.loc_data['system_grp'])
        loc_index = tpu.get_next_index(loc_list)

        loc_name = '{}_'.format(self.loc_data['unique_name']) if self.loc_data['unique_name'] else ''
        name = '{}{}_{:02d}_loc'.format(loc_name, self.sys_data['name'], loc_index)
        self.loc = mc.rename(self.loc, name)
        mc.parent(self.loc, self.loc_data['system_grp'])

        self.update_loc_data()

    def set_loc_parent(self, parent=''):
        parent = parent if parent else mc.ls(sl=1)[0]
        mc.connectAttr('{}.child'.format(parent), '{}.parent'.format(self.loc))

    def set_loc_parent_sel_order(self, loc_list=''):
        sel = loc_list if loc_list else mc.ls(sl=1)
        loc_dict = {}
        for n, loc in enumerate(sel):
            if loc == sel[-1]:
                break
            else:
                loc_dict.update({loc: sel[n+1]})

        for loc in loc_dict:
            self.load_loc(loc)
            self.set_loc_parent(loc_dict[loc])

    def set_loc_parent_index_order(self):
        members = self.sys_members()
        order_dict = {}

        for member in members:
            self.load_loc(member)
            index = self.loc_index()
            order_dict.update({index: member})

        max_index = max(order_dict.keys()) + 1
        parent_list = [order_dict[n] for n in range(1, max_index)]

        self.set_loc_parent_sel_order(parent_list)

    def set_loc_index(self, index):
        new_name = self.loc.replace('{:02d}'.format(self.loc_index()), '{:02d}'.format(index))
        self.loc = mc.rename(self.loc, new_name)
        self.update_loc_data()

        return new_name

    def set_sys_parent(self, loc=''):
        parent_loc = loc if loc else mc.ls(sl=1)[0]
        mc.connectAttr('{}.sys_child'.format(parent_loc), '{}.sys_parent'.format(self.sys_data['group']))

        self.update_sys_data()

    # GET SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def template_members(self):
        members = mc.listConnections('{}.sys_data'.format(self.environment_data['group']))
        return '' if members is None else members

    def template_members_data(self):
        current_sys = self.sys_data['group']
        members = self.template_members()
        members_data = {}

        for member in members:
            self.load_sys(member)
            self.load_loc(self.sys_members()[0])
            self.update_sys_data()
            data = self.sys_data
            members_data.update({member: data})

        self.load_sys(current_sys)
        return members_data

    def sys_parent(self):
        parent = mc.listConnections('{}.sys_parent'.format(self.sys_data['group']), s=1, d=0)
        return '' if parent is None else parent[0]

    def sys_root(self):
        root = mc.listConnections('{}.root'.format(self.sys_data['group']), s=1, d=0)
        return '' if root is None else root[0]

    def sys_members_data(self):
        current_loc = self.loc
        members_data = {}

        for member in self.sys_members():
            self.load_loc(member)
            self.update_loc_data()
            members_data.update({member: self.loc_data})

        self.load_loc(current_loc)
        return members_data

    def sys_members(self, system=''):
        sys = system if system else self.sys_data['group']
        members = mc.listConnections('{}.loc_data'.format(sys))
        return '' if members is None else members

    def loc_sys(self):
        sys = mc.listConnections('{}.metadata'.format(self.loc), s=0, d=1)
        return '' if sys is None else sys[0]

    def loc_parent(self):
        parent_query = mc.listConnections('{}.parent'.format(self.loc), s=1, d=0)
        return '' if parent_query is None else parent_query[0]

    def loc_index(self):
        name_split = self.loc.split('_')
        index = ''

        for word in name_split:
            if word.isdigit():
                index = int(word)

        return index

    def list_all_loc(self):
        pass

    # ACTION SECTION ::::::::::::::::::::::::::::::::::::::::::::::::::::
    def snap_to_vtx_avg(self, vtx_input=''):
        """
        Snaps current locator to selected vertex list average position
        :param vtx_input:
        """
        vtx_list = vtx_input if vtx_input else mc.filterExpand(mc.ls(sl=1), sm=31)
        axis_x = axis_y = axis_z = 0

        for vtx in vtx_list:
            axis_x += mc.xform(vtx, q=1, t=1, ws=1)[0]
            axis_y += mc.xform(vtx, q=1, t=1, ws=1)[1]
            axis_z += mc.xform(vtx, q=1, t=1, ws=1)[2]

        x_avg = axis_x / len(vtx_list)
        y_avg = axis_y / len(vtx_list)
        z_avg = axis_z / len(vtx_list)

        mc.xform(self.loc, t=(x_avg, y_avg, z_avg), ws=1)

        self.loc_data['custom_sets']['vertex_avg'] = vtx_list
        self.commit_loc_data()
        self.update_template_data()

    def add_to_vtx_set(self, key=''):
        """
        Add selection to custom set - vertex
        """
        pass

    def sys_distribute_members(self):
        amount = len(self.sys_members())
        step = 100/(amount - 1)

        for n, member in enumerate(self.sys_members()):
            multiplier = n * step

    def members_in_index_order(self):
        pass

    def sys_distribute_loc_on_curve(self):
        pass

    def duplicate_system(self, name):
        pass

    def duplicate_loc(self, name):
        pass

    def mirror_system(self, axis=(1, 0, 0), new=True):
        side_relation = {'l': 'r',
                         'r': 'l'}
        t_axis_flip = [-1 if coord == 1 else 1 for coord in axis]  # (-1, 1, 1) for x
        r_axis_flip = [-1 if coord == 0 else 1 for coord in axis]  # (1, -1, -1) for x

        self.update_sys_data()
        sys_data = self.sys_data
        data = self.sys_members_data()

        flip_prefix = '' if not sys_data['prefix'] else side_relation[sys_data['prefix']]
        sys_data['prefix'] = flip_prefix

        for member in data:
            # rebuilding flip parent name
            parent = data[member]['parent']
            if parent:
                identity = sys_data['locators'][parent]['unique_name']
                index = sys_data['locators'][parent]['index']
                flip_parent = '{}_{}_{}_{:02d}_loc'.format(flip_prefix, identity, sys_data['name'], index)
                data[member]['parent'] = flip_parent

            # flipping coordinates
            t_coord = data[member]['position']['t']
            r_coord = data[member]['position']['r']
            flip_t = [flip * coord for flip, coord in zip(t_axis_flip, t_coord)]
            flip_r = [flip * coord for flip, coord in zip(r_axis_flip, r_coord)]
            data[member]['position']['t'] = flip_t
            data[member]['position']['r'] = flip_r

        # rebuilding flip root name
        root = sys_data['root']
        if root:
            identity = sys_data['locators'][root]['unique_name']
            index = sys_data['locators'][root]['index']
            flip_root = '{}_{}_{}_{:02d}_loc'.format(flip_prefix, identity, sys_data['name'], index)
            sys_data['root'] = flip_root

        # rebuild flip sys_parent
        # sys_parent = sys_data['sys_parent']
        # if sys_parent:
        #     self.load_loc(sys_parent)
        #     identity = sys_data['locators'][root]['unique_name']
        #     index = sys_data['locators'][root]['index']
        #     flip_root = '{}_{}_{}_{:02d}_loc'.format(flip_prefix, identity, sys_data['name'], index)
        #     sys_data['root'] = flip_root

        sys_data['locators'] = data
        self.rebuild_sys_from_data(sys_data)

    def mirror_loc(self, axis=(1, 0, 0)):
        """
        Duplicate data, mirrors coordinates, name, connections,
        and creates new locator on calculated position
        :param axis:
        :return:
        """
        side_relation = {'l': 'r',
                         'r': 'l'}
        axis_flip = [-1 * coord if coord == 1 else 1 for coord in axis]

        self.update_loc_data()
        side = self.loc_data['prefix']
        name = self.loc_data['unique_name']
        position = self.loc_data['position']['t']
        mirror = [flip * coord for flip, coord in zip(axis_flip, position)]

        self.new_loc(name, prefix=side_relation[side])
        self.loc_set_position(mirror)
        self.update_template_data()

    def loc_set_position(self, position):
        mc.xform(self.loc, t=position, ws=1)

    def parent_template(self):
        """
        Parent all systems in template, including systems themselves
        """
        for sys in self.template_members():
            self.load_sys(sys)
            self.parent_sys()

            if self.sys_parent():
                mc.parentConstraint(self.sys_parent(), self.sys_root(), mo=True)
            else:
                continue

    def parent_sys(self):
        """
        Parent locators in system based on connection data
        """
        locators = self.sys_members()
        prefix = '{}_'.format(self.sys_data['prefix']) if self.sys_data['prefix'] else ''
        curve_grp = mc.group(em=True, name='{}{}_crv_grp'.format(prefix, self.sys_data['name']))
        mc.parent(curve_grp, self.sys_data['group'])

        for loc in locators:
            self.load_loc(loc)
            parent = self.loc_parent()
            offset_grp = tpu.add_offset_grp(loc)
            mc.parent(offset_grp, self.loc_sys())

            if parent:
                mc.parentConstraint(parent, offset_grp, mo=True)
                mc.scaleConstraint(parent, offset_grp, mo=True)

                # Creating connection line
                parent_tr = mc.xform(parent, q=True, t=True, ws=True)
                self_tr = mc.xform(self.loc, q=True, t=True, ws=True)
                bridge_line = mc.curve(d=True, p=[self_tr, parent_tr], name='{}_crv'.format(self.loc))
                mc.parent(bridge_line, curve_grp)
                mc.setAttr("{}.overrideEnabled".format(bridge_line), 1)
                mc.setAttr("{}.overrideDisplayType".format(bridge_line), 1)
                mc.skinCluster(self.loc, parent, bridge_line, toSelectedBones=True, bindMethod=0,
                               skinMethod=0, normalizeWeights=1)
            else:
                continue

    # def bridge_curve(self):
    #     if self.loc_parent():
    #         parent_tr = mc.xform(self.loc_parent(), q=True, t=True, ws=True)
    #         self_tr = mc.xform(self.loc, q=True, t=True, ws=True)
    #
    #         bridge_line = mc.curve(d=True, p=[self_tr, parent_tr], name='{}_crv'.format(self.loc))
    #         mc.parent(bridge_line, curve_grp)
    #
    #         mc.setAttr("{}.overrideEnabled".format(bridge_line), 1)
    #         mc.setAttr("{}.overrideDisplayType".format(bridge_line), 1)
    #         mc.skinCluster(self.loc, parent, bridge_line,
    #                        toSelectedBones=True,
    #                        bindMethod=0,
    #                        skinMethod=0,
    #                        normalizeWeights=1)

    def export_template_data(self):
        """
        Export system data to json for future reconstruction
        """
        # update and stores template data
        self.update_template_data()
        data = self.environment_data

        # queries project data path
        project_path = mc.workspace(q=True, rootDirectory=True)
        data_path = '{}data/'.format(project_path)
        # queries jason files in path
        files_in_path = glob.glob('{}*.json'.format(data_path))

        # check versions and defines latest name
        next_index = tpu.get_next_index(files_in_path) if files_in_path else 1
        file_name = 'tp_rigSystems_rigTemplate_{:02d}_data.json'.format(next_index)
        file_path = '{}{}'.format(data_path, file_name)

        # exports json file
        with open(file_path, 'w') as file_for_write:
            json.dump(data, file_for_write, indent=4)

    def import_template_data(self):
        """
        Imports latest json file from project data folder
        :return environment data from file:
        """
        # queries project data path
        project_path = mc.workspace(q=True, rootDirectory=True)
        data_path = '{}data/'.format(project_path)

        # queries jason files in path
        files_in_path = glob.glob('{}*.json'.format(data_path))
        latest = max(files_in_path, key=os.path.getctime)

        with open(latest, 'r') as file_for_read:
            self.environment_data = json.load(file_for_read)

    def reorder_indexes(self):
        """
        Reorder system indexes in selection order
        """
        pass

    def clear_cache(self):
        self.cache_template_data = {}
        self.cache_sys_data = {}
        self.cache_loc_data = {}

    def sys_parent_hierarchy(self):

        pass
