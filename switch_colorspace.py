import maya.cmds as cmds


class UI():
    """
    Builds a UI to manage switching of colorspaces on file nodes
    """

    def __init__(self):
        """
        Constructor
        """
        self.win_name = 'switch_color_win'
        self.missing_rbs = []

        self.delete_win()
        self.create_win()
        self.populate_colorspaces()

        cmds.showWindow(self.win)
        cmds.window(self.win, e=1, w=250)

    def delete_win(self):
        """
        Deletes the window if it exists
        """
        if cmds.window(self.win_name, ex=1):
            cmds.deleteUI(self.win_name)

    def create_win(self):
        """
        Builds the window
        """
        border_space = 10
        line_space = border_space / 2
        section_space = 15
        field_height = 25

        self.win = cmds.window(self.win_name, title='Switch Colorspace')
        main_form = cmds.formLayout(nd=100)

        self.from_txt = cmds.text(l='From Colorspace:', fn='boldLabelFont')

        # create a column to house the missing radio buttons
        self.from_column = cmds.columnLayout(adj=1)
        self.from_coll = cmds.radioCollection()
        self.create_missing_rbs()

        # keep the avail and custom button outside of the column
        # so it's always on the bottom
        cmds.setParent(main_form)
        self.from_avail_rb = cmds.radioButton(
            l='Available:',
            onc=lambda x: cmds.optionMenu(self.avail_om, e=1, en=1),
            ofc=lambda x: cmds.optionMenu(self.avail_om, e=1, en=0))
        self.avail_om = cmds.optionMenu(en=0, h=field_height)
        self.from_cust_rb = cmds.radioButton(
            l='Custom:',
            onc=lambda x: cmds.textField(self.from_field, e=1, en=1),
            ofc=lambda x: cmds.textField(self.from_field, e=1, en=0))
        self.from_field = cmds.textField(en=0, h=field_height)

        self.to_txt = cmds.text(l='To Colorspace:', fn='boldLabelFont')
        self.to_om = cmds.optionMenu(h=field_height)

        self.apply_txt = cmds.text(l='Apply to:', fn='boldLabelFont')
        self.apply_coll = cmds.radioCollection()
        self.sel_rb = cmds.radioButton(l='selection', sl=1)
        self.scene_rb = cmds.radioButton(l='scene')

        self.apply_btn = cmds.button(l='Apply', c=self.apply, h=40)

        cmds.formLayout(
            main_form,
            e=True,
            attachForm=(
                (self.from_txt, 'top', border_space),
                (self.from_txt, 'left', border_space),
                (self.from_column, 'left', border_space),
                (self.from_column, 'right', border_space),
                (self.from_avail_rb, 'left', border_space + 1),
                (self.avail_om, 'left', border_space),
                (self.avail_om, 'right', border_space),
                (self.from_cust_rb, 'left', border_space + 1),
                (self.from_field, 'left', border_space),
                (self.from_field, 'right', border_space),
                (self.to_txt, 'left', border_space),
                (self.to_om, 'left', border_space),
                (self.to_om, 'right', border_space),
                (self.apply_txt, 'left', border_space),
                (self.sel_rb, 'left', border_space),
                (self.apply_btn, 'left', border_space),
                (self.apply_btn, 'right', border_space),
                (self.apply_btn, 'bottom', border_space),
            ),
            attachControl=(
                (self.from_column, 'top', line_space, self.from_txt),
                (self.from_avail_rb, 'top', 1, self.from_column),
                (self.avail_om, 'top', line_space, self.from_avail_rb),
                (self.from_cust_rb, 'top', 1, self.avail_om),
                (self.from_field, 'top', line_space, self.from_cust_rb),
                (self.to_txt, 'top', section_space, self.from_field),
                (self.to_om, 'top', line_space, self.to_txt),
                (self.apply_txt, 'top', section_space, self.to_om),
                (self.sel_rb, 'top', line_space, self.apply_txt),
                (self.scene_rb, 'top', line_space, self.apply_txt),
                (self.apply_btn, 'top', section_space, self.scene_rb),
            ),
            attachPosition=((self.scene_rb, 'left', line_space, 50), ))

    def populate_colorspaces(self):
        """
        Populates the option menus with all of the available colorspaces
        """
        colorspaces = cmds.colorManagementPrefs(q=1, iss=1)
        option_menus = [self.to_om, self.avail_om]

        for colorspace in colorspaces:
            for option_menu in option_menus:
                cmds.menuItem(l=colorspace, p=option_menu)

    def create_missing_rbs(self):
        """
        Creates radio buttons for all missing colorspaces in the scene
        """
        # remove missing rbs first
        for rb in self.missing_rbs:
            cmds.deleteUI(rb)
        self.missing_rbs = []

        missing_cs = get_missing_colorspaces()
        if missing_cs:
            for cs in missing_cs:
                self.missing_rbs.append(
                    cmds.radioButton(l=cs,
                                     collection=self.from_coll,
                                     p=self.from_column))

    def apply(self, *args):
        """
        Switches the colorspace based on values from the UI
        """
        # make sure we have a valid from colorspace
        from_cs = ''
        sel_rb = cmds.radioCollection(self.from_coll, q=1, sl=1)
        if sel_rb != 'NONE':
            from_cs = cmds.radioButton(sel_rb, q=1, l=1)
            if 'Custom' in from_cs:
                from_cs = cmds.textField(self.from_field, q=1, text=1)

        if not from_cs:
            raise ValueError('From colorspace is not defined!')

        # make sure we have files to operate on
        files = []
        if cmds.radioButton(self.sel_rb, q=1, sl=1):
            files = cmds.ls(sl=1, type='file')
        else:
            files = cmds.ls(type='file')
        if not files:
            raise ValueError('No file nodes specified!')

        # get the to colorspace and set it
        to_cs = cmds.optionMenu(self.to_om, q=1, v=1)
        for file in files:
            if cmds.getAttr(file + '.colorSpace') == from_cs:
                try:
                    switch_colorspace(file, to_cs)
                    print 'Changed colorspace from {from_cs} to {to_cs} on {file}'.format(
                        from_cs=from_cs, to_cs=to_cs, file=file)
                except:
                    print 'Could not change colorspace from {from_cs} to {to_cs} on {file}'.format(
                        from_cs=from_cs, to_cs=to_cs, file=file)

        # refresh!
        self.create_missing_rbs()
        cmds.window(self.win, e=1, h=1)


def get_missing_colorspaces():
    """
    Returns a list of all missing colorspaces
    """
    missing_cs_nodes = cmds.colorManagementPrefs(q=1, missingColorSpaceNodes=1)
    missing_cs = set()
    for node in missing_cs_nodes:
        missing_cs.add(cmds.getAttr(node + '.colorSpace'))

    return list(missing_cs)


def switch_colorspace(file, colorspace):
    """
    Changes the colorspace on a given file node
    """
    cmds.setAttr(file + '.colorSpace', colorspace, type='string')