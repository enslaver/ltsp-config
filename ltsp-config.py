#!/usr/bin/env python
#
# LTSP-Config UI
# Copyright (C) Joshua Trimm <enslaver@enslaver.com>
#
# Allows administrators to configure the ltsp server using a GUI interface,
# which is basically a front end to edit the lts.conf and configure a few other
# options.
#
# TODO:
# Make buttons work
# Assign tooltip to each column based on lts.conf.options
# Load all default options in combobox so user can scroll through each
# Detect if value = true/false and replace with on/off type widget
# Auto detect location of lts.conf
#
#
#Based on configparserui
#Copyright (C) Alex Goretoy <alex@goretoy.com>
#This program is free software: you can redistribute it and/or modify it
#under the terms of the GNU General Public License version 3, as published
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranties of
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along
#with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE


import os, sys
import getopt
import threading

try:
    import pygtk
    pygtk.require("2.0")
    import gtk, gobject
    gobject.threads_init()
    gtk.gdk.threads_init()
except:
    print >> sys.stderr, ("Error: Cant connect to widget, check to be sure "
                          "you have pygtk installed and your DISPLAY variable "
                          "set")
    sys.exit(1)

import configuration
import data_validation


VARS_CONFIG_FILE = "lts_vars.conf"
LTSVARS_CONFIG = configuration.LTSVarsConfig(VARS_CONFIG_FILE)

widget_list = {
    "main_window": ["option_combobox", 'add_option_button',
                    'remove_option_button', 'option_name_entry',
                    'option_value_entry', 'config_hbox',
                    'expand_button', 'collapse_button', 'status1_label',
                    ],
    'warning_dialog': ["warning_dialog_title_label",
                       'warning_dialog_message_label',
                       'warning_dialog_cancel_button',
                       'warning_dialog_ok_button',
                       ],
    'save_dialog': ['save_dialog_cancel_button', "save_dialog_ok_button",
                    ],
    'open_dialog': ['open_dialog_cancel_button', 'open_dialog_cancel_button',
                    ],
    }


class uiListView(gtk.List):
    def __init__(self, liststore=None):
        if liststore:
            self.liststore = liststore
        else:
            self.liststore = gtk.ListStore(str)

        super(uiListView, self).__init__()

class uiTreeView(gtk.TreeView):
    columns = []
    rows = {}
    def __init__(self, treestore = None):
        if treestore:
            self.treestore = treestore
        else:
            self.treestore = gtk.TreeStore(str)

        super(uiTreeView, self).__init__(self.treestore)
        #self.set_has_tooltip(True)
        self.set_tooltip_column(0)
        self.connect("query-tooltip", self.tooltip_query)
        self.last_tooltip = ''  # register changes to the tooltip text

    def add_columns(self,columns=[], expander_index = -1, edited_callback = None):
        if columns and isinstance(columns, list):
            self.cells = {}
            for i in range(len(columns)):
                def col0_edited_cb( cell, path, new_text, model, callback ):
                    callback(cell, path, new_text, model )
                    #if model[path][2] is not new_text:
                    #    print "Change '%s' to '%s'" % (model[path][2], new_text)
                    #    model[path][2] = new_text
                    #return

                self.cells[ columns[i] ] = gtk.CellRendererText()

                if i == 0:
                    self.cells[ columns[i] ].set_property('cell-background', 'black')
                    self.cells[ columns[i] ].set_property('foreground', 'white')
                else:
                    self.cells[ columns[i] ].set_property( 'editable', True )
                    if i == 1:
                        self.cells[ columns[i] ].set_property( 'editable', False )
                    if edited_callback:
                        self.cells[ columns[i] ].connect( 'edited', col0_edited_cb, self.treestore, edited_callback )
                setattr(self, 'tvcolumn' + str(i), getattr(gtk, 'TreeViewColumn')(columns[i], self.cells[ columns[i] ]))
                curr_column = getattr(self, 'tvcolumn' + str(i) )
                #curr_column.pack_start(self.cell, True)
                curr_column.set_attributes(self.cells[ columns[i] ], text=i, cell_background_set=3)
                self.append_column(curr_column)
                if expander_index >= 0 and i == expander_index:
                    self.set_expander_column(curr_column)

    def add_row(self,fields = [], index = None):
        return self.append_row(fields, index)

    def add_rows(self, rows = []):
        return self.append_rows(rows)

    def append_row(self, fields = [], index = None):
        return self.treestore.append(index, fields)

    def append_rows(self, rows = []):
        iters = []
        for row in range(len(rows)):
            index, fields = rows[row]
            iters.append(self.append_row(fields, index))

        return iters

    def other(self):
        # add data
        iter = self.treestore.append(None, ['123', 'Widget'])
        self.treestore.append(iter, ['123-1', 'Widget Frammer'])
        self.treestore.append(iter, ['123-2', 'Widget Whatsit'])
        self.treestore.append(iter, ['123-3', 'Widget Thingy'])
        iter = self.treestore.append(None, ['456', 'Thingamabob'])
        self.treestore.append(iter, ['456-1', 'Thingamabob Frammer'])
        iter1 = self.treestore.append(iter, ['456-2', 'Thingamabob Bunger'])
        self.treestore.append(iter, ['456-2-1', 'Thingamabob Bunger Spring'])




        self.b0.connect_object('clicked', gtk.TreeView.expand_all,
                               self.treeview)
        self.b1.connect_object('clicked', gtk.TreeView.collapse_all,
                              self.treeview)
        # make treeview searchable
        self.treeview.set_search_column(0)

        # Allow sorting on the column
        self.tvcolumn.set_sort_column_id(0)

        # Allow drag and drop reordering of rows
        self.treeview.set_reorderable(True)

        self.treeview.enable_model_drag_source(0, [("STRING", 0, 0),
                                                   ('text/plain', 0, 0)
                                                   ],
                                               gtk.gdk.ACTION_DEFAULT)
        self.treeview.enable_model_drag_dest([("STRING", 0, 0),
                                              ('text/plain', 0, 0),
                                              ('text/uri-list', 0, 0)
                                              ],
                                             gtk.gdk.ACTION_DEFAULT)

        self.treeview.connect("drag_data_get", self.drag_data_get_data)
        self.treeview.connect("drag_data_received",
                              self.drag_data_received_data)

    def _set_tooltip(self, treepath, tooltip):
        model = self.get_model()
        iter = model.get_iter(treepath)
        text = self.treestore.get_value(iter, 1)
        try:
            text = LTSVARS_CONFIG[text].description
        except:
            text = ''
        if not text:
            return False
        if self.last_tooltip and self.last_tooltip != text:
            self.last_tooltip = ''
            return False
        self.last_tooltip = text
        tooltip.set_text(text)
        return True

    def tooltip_query(self, treeview, x, y, mode, tooltip):
        """Horrible, bloody, and ugly.
        ..but in all fairness, it's not my fault."""
        # Treepath is off by one for some reason.  ..in a bad way.
        # ..so, we work around it.
        model = self.get_model()
        path = self.get_path_at_pos(x, y)
        if not path:
            # every part of our TreeView is tooltippable.  However, GTK thinks
            # the last item is a blank space.  ..so, we correct that.
            treepath = [0]  # root items
            try:
                # get last root item..
                while model.get_iter(tuple(treepath)):
                    treepath[0] += 1
            except ValueError:
                treepath[0] -= 1
                if treepath[0] < 0:
                    print "Bad treepath."
                    return False
            try:
                # get the last item in this root item
                treepath.append(0)
                while model.get_iter(tuple(treepath)):
                    treepath[1] += 1
            except ValueError:
                treepath[1] -= 1
                treepath = tuple(treepath)
                if treepath[1] < 0:
                    print "Bad treepath.."
                    return False
            return self._set_tooltip(treepath, tooltip)
        else:
            treepath = path[0]
            if len(treepath) == 1:
                # We are at the last item in a primary category, but gtk
                # thinks we're in the first item of the next category.  E.g.,
                # for a category with 13 entries, we're *actually* on
                # (0, 12) but gtk thinks we're on (1,).  So, we work around it.
                treepath = [treepath[0] - 1, 0]
                if treepath[0] < 0:
                    return False
                try:
                    # get the *actual* last number..
                    while model.get_iter(tuple(treepath)):
                        treepath[1] += 1
                except ValueError:
                    # back up to the last item that didn't cause an error.
                    treepath[1] -= 1
                    if treepath[1] < 0:
                        return False
                    treepath = tuple(treepath)
                iter = model.get_iter(tuple(treepath))
            else:
                # the normal use case -- still off by one, but much easier to
                # handle..
                treepath = (treepath[0], treepath[1] - 1)
                if treepath[1] < 0:
                    return False
            return self._set_tooltip(treepath, tooltip)
        return False

class uiBuilder(gtk.Builder):
    def __init__(self, *args, **kwargs):
        super(uiBuilder, self).__init__()

    def add_file(self, fname):
        self.add_from_file(sys.path[0] + os.path.sep + fname)
#        try:
#            if os.environ["OS"].startswith("Windows"):
#                self.add_from_file(sys.path[0] + '\\' + file ) #+ "\\builder.ui")
#        except KeyError, e:
#            self.add_from_file(sys.path[0] + '/' + file ) #+ "/builder.ui")

    def get_widget(self, name = None):
        if name:
            #is name string
            if isinstance(name, basestring):
                setattr(self, name, self.get_object( name ))

    def get_widgets(self, name = None):
        if name:
            #is name dict
            if isinstance(name, dict):
                names = []
                for i in name.keys():
                    if i:
                        names.append(i)
                for i in name.values():
                    if i:
                        if isinstance(i, list):
                            for j in range(len(i)):
                                names.append(i[j])
                        elif isinstance(i, dict):
                            pass
                        else:
                            #else name is a string
                            names.append(i)
                # Get objects (widgets) from the Builder
                for i in range(len(names)):
                    setattr(self, names[i], self.get_object(names[i]))

    def connect_widgets(self, parent):
        self.connect_signals(self)

class uiLogic(uiBuilder):
    def __init__(self,*args, **kwargs):
        super(uiLogic, self).__init__(*args, **kwargs)
        builder_file = kwargs.get('builder_file', 'ltsp-config.ui')
        self.add_file(builder_file)
        self.get_widgets(widget_list)

        # Combobox to add an option
        cell = gtk.CellRendererText()
        self.option_combobox.set_model(gtk.ListStore(str))
        self.option_combobox.set_entry_text_column(0)
        self.option_combobox.pack_start(cell, True)

        self.config_treeview = uiTreeView( gtk.TreeStore(str, str, str, 'gboolean' ) )
        self.config_treeview.connect('button-press-event', self.on_treeview_button_press_event )
        self.config_treeview.add_columns( ['Sections', 'Options','Values'], 0, self.on_column_edited )
        #self.config_treeview.set_default_sort_func( sort_func = None )
        #self.config_treeview.set_property('fixed-height-mode', True)
        self.config_treeview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        self.expand_button.connect_object('clicked', gtk.TreeView.expand_all,
                               self.config_treeview)
        self.collapse_button.connect_object('clicked', gtk.TreeView.collapse_all,
                              self.config_treeview)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scrolled_window.add_with_viewport(self.config_treeview)

        self.config_hbox.pack_start(scrolled_window)

        self.config_treeview.get_selection().connect('changed',
                                                     self.set_selected_section)
        self.config_treeview.connect('cursor-changed',
                                     self.set_selected_section)

        self.connect_widgets(self)
        self.main_window.show_all()


class functions(object):
    pass


class DataKeyTypeError(TypeError):
    pass


class uiData(dict):
    def __setitem__(self, key, value):
        if not isinstance(key, basestring):
            self[key] = value
        else:
            raise DataKeyTypeError('key must be of type string')

    def __getitem__(self, key):
        return self[key]


class uiHelpers(object):
    def _init(self):
        self.vars_meta = LTSVARS_CONFIG
        self.validator = data_validation.LTSPValidator(self.vars_meta)
        self.config = configuration.Raw()
        self.config.optionxform = str
        self.config_filename = sys.path[0] + '/' + 'lts.conf'
        self.selected_section = (None, None)
        self.config_treeview.get_model().clear()
        self.status1_label.set_text('')
        self.warning_dialog_message_label.set_text('')
        self.option_combobox.child.set_text('')
        #self.option_name_entry.set_text('')
        #self.option_value_entry.set_text('')
        self.main_window.set_title('LTSP Configuration')
        self.status1_label.set_text('Editing Config')
        self._toggle_option_buttons()
        self.update_option_combobox()
        try:
            self.config.read([self.config_filename])
        except configuration.ConfigParser.MissingSectionHeaderError:
            self.config_filename = None
            self.status1_label.set_text('Error: File Missing Section Header')
        self.update_config_treeview()

    def _toggle_option_buttons(self):
        if self.config.sections() and self.selected_section[0]:
            self.remove_option_button.set_sensitive(True)
        else:
            self.add_option_button.set_sensitive(False)
            self.remove_option_button.set_sensitive(False)

    def set_selected_section(self, widget, data = None):
        treeselection = self.config_treeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_SINGLE)
        ( tree_model, tree_iter ) = treeselection.get_selected()
        try:
            self.selected_section= ( tree_model.get_value(tree_iter, 0), tree_iter)
        except TypeError, e:
            #catch TypeError after removing row
            self.selected_section = (None, None)
        finally:
            self._toggle_option_buttons()

    def update_option_combobox(self):
        """Update the option combobox with all available variables/options,
        including both 'unofficial' ones that are a part of the user's config,
        and 'official' ones that are a part of the vars_conf metadata."""
        model = self.option_combobox.get_model()
        model.clear()
        vars = set(self.vars_meta.vars)
        for section in self.config.sections():
            vars.update(self.config.items(section))
        vars = list(vars)
        for var in sorted(vars):
            model.append([var])

    def update_config_treeview(self):
        self.config_treeview.get_model().clear()

        if self.config_filename:
            self.main_window.set_title('LTSP Configuration')

        for section in self.config.sections():
            row = [section, None, None, True]
            section_iter = self.config_treeview.add_row(row, None)
            for option, value in self.config.items(section):
                error = self.validator.check_data(option, value)
                if error:
                    print "Warning for %s: %s" % (option, error)
                try:
                    tooltip = self.vars_meta[option].description
                except:
                    tooltip = ''
                self.config_treeview.add_row([ None, option, value, False ], section_iter)
        self.config_treeview.expand_all()
        #for section in self.secopt.keys():
        #    section_iter = self.config_treeview.add_row([section, None, None, False], None)
        #    for n in range(len(self.secopt[ section ]['options'])):
        #        self.config_treeview.add_row([section, self.secopt[ section ]['options'][n], self.secopt[ section ]['values'][n], False ], section_iter)


class NotAnIter(TypeError):
    '''raised when iter goes stale after remove
    '''
    pass


class uiSignals(uiHelpers):
    def __init__(self, *args, **kwargs):
        super(uiSignals, self).__init__(*args, **kwargs)
        self._init()

    def on_column_edited(self, cell, path, new_text, model ):
        var = model[path][1]
        if var in self.vars_meta:
            var_data = self.vars_meta[var]
            error = self.validator.check_data(var, new_text)
            if error:
                error = error.split(':', 2)[2]
                self.status1_label.set_text(error)
                return
            status = 'Verified value and changed %s to %s'
        else:
            status = 'Changed unknown variable %s to %s'
        #if model[path][1] != new_text:
        #    self.status1_label.set_text('Changed %s to %s' % (model[path][1], new_text))

        if model[path][2] != new_text:
            self.status1_label.set_text(status % (model[path][1], new_text))
            model[path][2] = new_text
	    self.config.set( model[path][0], model[path][1], model[path][2] )
        return

    def gtk_widget_hide(self, w, e):
        w.hide()
        return

    def on_menu_new_item_activate(self, w = None, e = None):
        if self.config.sections():
            self.warning_dialog_message_label.set_text('You have some unsaved work.\nAre you sure you want to create a new config file?')
            if self.warning_dialog.run():
                self._init()

    def on_menu_open_item_activate(self, w = None, e = None):
        def run():
            if self.open_dialog.run():
                self._init()
                self.status1_label.set_text('Go!')
                self.config_filename = self.open_dialog.get_filename()
                try:
                    self.config.read([self.config_filename])
                except configuration.ConfigParser.MissingSectionHeaderError:
                    self.config_filename = None
                    status = 'Error: File Missing Section Header'
                    self.status1_label.set_text(status)
                self.update_config_treeview()

        if self.config.sections():
            warning = ('You have some unsaved work.\n'
                       'Are you sure you want to open another config file?')
            self.warning_dialog_message_label.set_text(warning)
            if self.warning_dialog.run():
                run()
        else:
            run()

    def _save_menu_helper(self):
        if self.config_filename:
            with open(self.config_filename, 'wb') as c:
                self.config.write(c)
            self.status1_label.set_text('Saved %s' %
                                        (self.config_filename.split('/')[-1]))
            return False
        return True

    def on_menu_save_item_activate(self, w = None, e = None):
        #if self.config.sections():
            if(self._save_menu_helper()):
                self.on_menu_save_as_item_activate()

    def on_menu_save_as_item_activate(self, w = None, e = None):
        #if self.config.sections():
            if self.save_dialog.run():
                self.config_filename = self.save_dialog.get_filename()
                self._save_menu_helper()

    def on_remove_secopt_button_cb(self, w, e = None):
        print dir(self.config_treeview.get_selection()), self.config_treeview.get_selection()
        treeselection = self.config_treeview.get_selection()
        (tree_model, tree_iter) = treeselection.get_selected()
        try:
            section = tree_model.get_value(tree_iter, 0)
            option = tree_model.get_value(tree_iter, 1)
            value = tree_model.get_value(tree_iter, 2)
        except TypeError, e:
            return

        tree_model.remove(tree_iter)

        if not option:
            self.status1_label.set_text('Removed %s' % (section))
            self.config.remove_section( section )
        else:
            self.status1_label.set_text('Removed %s from %s' % (option, section))
            self.config.remove_option(section, option)

        self.selected_section = (None, None)
        self.update_config_treeview()

    def on_option_name_entry_changed(self, w=None, e=None):
        self._toggle_option_buttons()

    def on_add_option_button_cb(self, w, e = None):
        section = self.selected_section[0]
        if section is None:
            msg = "Can't add option: Select a section first"
            self.status1_label.set_text(msg)
            return
        var = self.option_combobox.get_active_text().strip()
        if not var:
            return
        if var in self.vars_meta:
            var_data = self.vars_meta[var]
            value = var_data.default
            status = "Added option %s to %s and set to default value   "
        else:
            value = ''
            status = "Added unknown option %s to %s   "

        if var and section:
            if var in dict(self.config.items(section)):
                self.status1_label.set_text("Option %s already present." % var)
                return
            self.config.set(section, var, value )

        self.status1_label.set_text(status % (var, section))
        self.update_config_treeview()
        self.update_option_combobox()

    def on_treeview_button_press_event(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor( path, col, 0)

                popupMenu = gtk.Menu()
                menuPopup1 = gtk.ImageMenuItem (gtk.STOCK_OPEN)
                popupMenu.add(menuPopup1)
                menuPopup2 = gtk.ImageMenuItem (gtk.STOCK_OK)
                popupMenu.add(menuPopup2)
                popupMenu.show_all()
                popupMenu.popup( None, None, None, event.button, time)
            return True

    # close the window and quit
    def delete_event(self, widget, event=None, data=None):
        gtk.main_quit()
        return False

    def on_warning_dialog_cancel_button_clicked(self,w=None,e=None):
        self.warning_dialog.hide()

    def on_warning_dialog_ok_button_clicked(self, w=None, e=None):
        self.warning_dialog.hide()

    def on_option_combobox_popup(self, w=None, e=None):
        self.update_option_combobox()

    def make_pb(self, tvcolumn, cell, model, iter):
        stock = model.get_value(iter, 1)
        pb = self.treeview.render_icon(stock, gtk.ICON_SIZE_MENU, None)
        cell.set_property('pixbuf', pb)
        return

    def str_obj(self, tvcolumn, cell, model, iter):
        obj = model.get_value(iter, 0)
        cell.set_property('text', str(obj))
        return

    def toggled(self, cell, path):
        iter = self.treestore.get_iter(path)
        value = not self.treestore.get_value(iter, 1)
        self.treestore.set_value(iter, 1, value)
        return

    def drag_data_get_data(self, treeview, context, selection, target, etime):
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        data = model.get_value(iter, 1)
        print data
        selection.set('text/plain', 8, data)

    def drag_data_received_data(self, treeview, context, x, y, selection,
                                info, etime):
        print selection.target, selection.type,
        print selection.format, selection.data
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            model = treeview.get_model()
            path, position = drop_info
            data = selection.data
            print path, data, model.get_value(model.get_iter(path), 1)
        return


class pyGTKConfigParser(uiSignals, uiLogic):
    def __init__(self, *args, **kwargs):
        super(pyGTKConfigParser, self).__init__(*args, **kwargs)


class options(dict):
    pass

#don't worry about passing options to pygtk-parser, it wont really do anything with them atm
##TODO: handle options
def parse_args(args):
    """ Parse args given to program. Change appropriate variables.
    """

    try:
        opts = getopt.getopt(args, "lf:ll:v:h", ['log_filename=', 'log_level=',
                                                 'verbose', 'help'])[0]
    except getopt.GetoptError, e:
        raise ArgError, str(e)

    return_args = {
        'interval': 0,
        'user': None,
        'password': None
    }

    for opt, val in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit(1)
        elif opt in ("-lf", "--log_filename"):
            return_args['log_filename'] = val
        elif opt in ("-ll", "--log_level"):
            return_args['log_level'] = get_log_level(val)
        elif opt in ("-v", "--verbose"):
            return_args['verbose'] = True
        else:
            raise ArgError, "Don't know how to handle argument %s" % opt

    return return_args


class ArgError(Exception):
    """ Invalid command line argument exception """
    pass


def main(*args, **kwargs):
    gobject.threads_init()
    pyGTKConfigParser(*args, **kwargs)

    #initialize threading system, must be before gtk.main
    gtk.gdk.threads_init()

    #run main gtk
    gtk.main()
    return

if __name__ == "__main__":
    try:
        args = parse_args(sys.argv[1:])
    except ArgError, e:
        print "Argument Error: %s!" % e
        print
#nonexistent        print_help()
        sys.exit(1)

    main(args)
