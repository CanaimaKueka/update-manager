# UpdateManager/Frontend/Gtk/ui.py
#  
#  Copyright (c) 2004-2009 Canonical
#                2004 Michiel Sikkes
#                2005 Martin Willemoes Hansen
#                2009 Stephan Peijnik
#  
#  Author: Michiel Sikkes <michiel@eyesopened.nl>
#          Michael Vogt <mvo@debian.org>
#          Martin Willemoes Hansen <mwh@sysrq.dk>
#          Stephan Peijnik <debian@sp.or.at>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#  USA.

""" Gtk UI frontend module """

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import gio
import pango

import logging
import os
import re
import sys
import time
import xml.sax.saxutils

import dbus
import dbus.service
import dbus.glib
import gobject
import glib
import gconf

from gettext import gettext as _

from UpdateManager import __version__ as um_version
from UpdateManager.Util.enum import Enum
from UpdateManager.Exceptions import ExitProgramException
from UpdateManager.Frontend.Gtk.GtkProgress import GtkCacheProgress
from UpdateManager.Frontend.Gtk.GtkProgress import GtkListProgress
from UpdateManager.Frontend.GtkCommon.SimpleGtkbuilderApp import SimpleGtkbuilderApp
from UpdateManager.Frontend.GtkCommon import get_ui_path
from UpdateManager.Frontend.Gtk.ChangelogViewer import ChangelogViewer
from UpdateManager.Frontend.Gtk.utils import init_proxy
from UpdateManager.DistSpecific.changelog import ChangelogHandler
from UpdateManager.Util.humanize import humanize_size

LOG = logging.getLogger("UpdateManager.Frontend.Gtk.ui")

LIST_COL = Enum("CONTENTS", "NAME", "PKG_INFO", "CATEGORY_ID")

class GtkDbusController(dbus.service.Object):
    """ Helper class to provide UpdateManagerIFace via dbus. """
    def __init__(self, parent, bus_name,
                 object_path = '/org/freedesktop/UpdateManagerObject'):
        dbus.service.Object.__init__(self, bus_name, object_path)
        self._parent = parent
        LOG.debug("GtkDbusController initialized.")

    @dbus.service.method('org.freedesktop.UpdateManagerIFace')
    def bringToFront(self):
        """ DBUS Service method for bringToFront """
        LOG.debug('bringToFront called via dbus.')
        self._parent.window_main.present()
        self._parent.window_main.set_urgency_hint(True)
        return True

class UpdateListControl(ChangelogHandler):
    """ Update ListView control/handler class. """
    
    def __init__(self, userinterface, treeview):
        """ Initializes the treeview """
        ChangelogHandler.__init__(self)
        self._treeview = treeview
        self._ui = userinterface
        self._current_pkg = None

        self._changelogs = {}
        self._store = gtk.ListStore(str, str, gobject.TYPE_PYOBJECT,
                                    gobject.TYPE_PYOBJECT)
        self._treeview.set_model(self._store)
        self._treeview.set_headers_clickable(True)

        trdr = gtk.CellRendererText()
        trdr.set_property("xpad", 6)
        trdr.set_property("ypad", 6)
        crdr = gtk.CellRendererToggle()
        crdr.set_property("activatable", True)
        crdr.set_property("xpad", 6)
        
        crdr.connect("toggled", self.row_toggled)

        column_inst = gtk.TreeViewColumn("Install", crdr)
        column_inst.set_cell_data_func(crdr, self.install_column_view_func)
        column_name = gtk.TreeViewColumn("Name", trdr,
                                         markup=LIST_COL.CONTENTS)
        column_name.set_cell_data_func(trdr, self.name_column_view_func)
        column_name.set_resizable(True)

        major, minor, patch = gtk.pygtk_version
        if (major >= 2) and (minor >= 5):
            column_inst.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column_inst.set_fixed_width(30)
            column_name.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column_name.set_fixed_width(100)
            self._treeview.set_fixed_height_mode(False)
            
        self._treeview.append_column(column_inst)
        column_inst.set_visible(True)
        self._treeview.append_column(column_name)
        self._treeview.set_search_column(LIST_COL.NAME)
        self._treeview.connect("button-press-event",
                                     self.show_context_menu)
        self._treeview.connect("cursor-changed", self.cursor_changed)
        self._treeview.connect("row-activated", self.row_activated)

    def get_store(self):
        """ Returns the store. """
        return self._store

    def set_sensitive(self, sensitive):
        """ Wrapper around the treeview's set_sensitive method.

        :param sensitive: Bool defining whether the widget should be sensitive
          or not.

        .. versionadded: 0.200.0~exp1
        """
        self._treeview.set_sensitive(sensitive)

    def show_context_menu(self, widget, event):
        """ Shows the context menu for treeview entries. """
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            selected_updates = 0
            update_count = 0
            for row in self._store:
                if row[LIST_COL.PKG_INFO]:
                    update_count += 1
                    if row[LIST_COL.PKG_INFO].active:
                        selected_updates += 1
            
            menu = gtk.Menu()
            item_deselect_all = gtk.MenuItem(_("_Uncheck All"))
            item_deselect_all.connect("activate", self.deselect_all_rows)
            menu.add(item_deselect_all)

            item_select_all = gtk.MenuItem(_("_Check all"))
            item_select_all.connect("activate", self.select_all_rows)
            menu.add(item_select_all)

            if update_count == 0:
                item_deselect_all.set_property("sensitive", False)
                item_select_all.set_property("sensitive", False)
            elif selected_updates == 0:
                item_deselect_all.set_property("sensitive", False)
                item_select_all.set_property("sensitive", True)
            elif selected_updates == update_count:
                item_deselect_all.set_property("sensitive", True)
                item_select_all.set_property("sensitive", False)
            else:
                item_deselect_all.set_property("sensitive", True)
                item_select_all.set_property("sensitive", True)

            menu.popup(None, None, None, 0, event.time)
            menu.show_all()
            return True

    def select_all_rows(self, widget):
        """ Handler for select all function. """
        self._ui.set_busy_status()
        for row in self._store:
            if row[LIST_COL.PKG_INFO] and not row[LIST_COL.PKG_INFO].active:
                row[LIST_COL.PKG_INFO].active = True
        self.update_download_size()
        self._treeview.queue_draw()
        self._ui.clear_busy_status()

    def deselect_all_rows(self, widget):
        """ Handler for deselect all function. """
        self._ui.set_busy_status()
        for row in self._store:
            if row[LIST_COL.PKG_INFO] and row[LIST_COL.PKG_INFO].active:
                row[LIST_COL.PKG_INFO].active = False
                
        self.update_download_size()
        self._treeview.queue_draw()
        self._ui.clear_busy_status()

    def clear_store(self):
        """ Empties the store """
        self._store.clear()
        LOG.debug('Update list store cleared.')

    def _store_append(self, description, pkg_name, pkg_info, origin_id):
        """ Appends an item to the store.

        :param description: Textual description, used in first column.
        :param pkg_name: Package name used in second column.
        :param pkg_info: :class:`UpdateManager.Backend.PackageInfoBase` object
        :param origin_id: The origin's ID.

        pkg_info and origin_id are mutually exclusive and are used to
        track which row corresponds to which origin or package.
        
        """
        assert(not (pkg_info and origin_id))
        def append_helper():
            self._store.append([description, pkg_name, pkg_info, origin_id])
        gobject.idle_add(append_helper)

    def store_get_update_count(self):
        """ Returns the number of updates available. """
        count = 0
        for row in self._store:
            if row[LIST_COL.PKG_INFO]:
                count += 1
        return count

    def store_is_empty(self):
        """ Returns whether the store is empty or not.

        .. versionadded: 0.200.0~exp1
        """
        return len(self._store) == 0
    
    def store_append_category(self, cat_name, cat_id):
        """ Appends a category description to the store.

        :param cat_name: The category's name.
        :param cat_id: The category's id.
        """
        descr = '<b><big>%s</big></b>' % (cat_name)
        self._store_append(descr, cat_name, None, cat_id)

    def store_append_pkg(self, pkg_info):
        """ Appends a package object to the store.

        :param pkg_info: :class:`UpdateManager.Backend.PackageInfoBase` object
        """
        name = xml.sax.saxutils.escape(pkg_info.get_package_name())
        summary = xml.sax.saxutils.escape(pkg_info.get_summary())
        size = _("(Size: %s)" % humanize_size(pkg_info.get_download_size()))
        
        old_version = pkg_info.get_installed_version()
        new_version = pkg_info.get_candidate_version()
        if old_version:
            version = _("From version %(old_version)s to %(new_version)s") \
                        % ({'old_version': old_version,
                            'new_version':new_version})
        else:
            version = _("Version: %s") % (new_version)

        text = "<b>%s</b>\n<small>%s</small>\n" % (name, summary)
        uninstalled_deps = pkg_info.get_uninstalled_dependencies()
        if uninstalled_deps:
            text+= "<small><b>%s</b>\n" \
                   % _("Requires installation of: ")
            for dep in uninstalled_deps:
                downsize_str = _("None")
                downsize = dep.get_download_size()
                if downsize:
                    downsize_str = humanize_size(downsize)
                text += "  %s (%s)\n" % (dep.get_package_name(), downsize_str)
            text += "</small>"

        deps = pkg_info.get_dependencies()
        
        if deps:
            text += "<small><b>%s</b>\n" \
                    % _("Depends on: ")
            for dep in deps:
                text += "  %s\n" % (dep.get_package_name())
            text += "</small>"

        sdeps = pkg_info.get_strict_dependencies()

        if sdeps:
            text += "<small><b>%s</b>\n" \
                    % _("Depends on (strict): ")
            for dep in sdeps:
                text += "  %s\n" % (dep.get_package_name())
            text += "</small>"
            
        rdeps = pkg_info.get_reverse_dependencies()
        
        if rdeps:
             text += "<small><b>%s</b>\n" \
                     % _("Is depended on by: ")
             for dep in rdeps:
                 text += "  %s\n" % (dep.get_package_name())

             text += "</small>"

        rsdeps = pkg_info.get_strict_reverse_dependencies()

        if rsdeps:
            text += "<small><b>%s</b>\n" \
                    % _("Is depended on by (strict): ")
            for dep in rsdeps:
                text += "  %s\n" % (dep.get_package_name())
            text += "</small>"

        conflicts = pkg_info.get_conflicts()
        if conflicts:
            text += "<small><b>%s</b>\n" \
                    % _("Conflicts with: ")
            for co in conflicts:
                text += "  %s (%s)\n" % (co.get_package_name(),
                                         co.get_candidate_version())
            text += "</small>"
            
        text += "<small>%s %s</small>" % (version, size)

        self._store_append(text, name, pkg_info, None)

    @classmethod
    def name_column_view_func(cls, cell_layout, renderer, model, iterator):
        """
        View handler function for the name column.
        """
        pkg = model.get_value(iterator, LIST_COL.PKG_INFO)

        if not pkg:
            renderer.set_property("sensitive", False)
        else:
            renderer.set_property("sensitive", True)

    @classmethod
    def install_column_view_func(cls, cell_layout, renderer, model, iterator):
        """
        View handler function for the install column.
        """
        pkg = model.get_value(iterator, LIST_COL.PKG_INFO)

        if not pkg:
            renderer.set_property("visible", False)
        else:
            renderer.set_property("visible", True)

            renderer.set_property("active", pkg.active)

            # TODO: handle packages which are being held back

    def set_package_selection(self, pkg_info, selected=True, handled=[]):
        pkg_info.active = selected

        # Check for circular dependency.
        # Not handling this case would lead to set_package_selection
        # being invoked in an endless loop, so this is really important.
        if pkg_info in handled:
            return

        # IMPORTANT: Get a *copy* of the handled parameter. Not doing this
        # would modify the contents of the default value of this keyword
        # argument!
        h = handled[:]
        h.append(pkg_info)
        if selected:
            # Package was selected. We now have to select all dependencies
            # and deselect all conflicting packages.    
            for dep in pkg_info.get_dependencies():
                self.set_package_selection(dep, selected=True, handled=h)
            for sdep in pkg_info.get_strict_dependencies():
                self.set_package_selection(sdep, selected=True, handled=h)
            for rsdep in pkg_info.get_strict_reverse_dependencies():
                self.set_package_selection(rsdep, selected=True, handled=h)
            for cpkg in pkg_info.get_conflicts():
                self.set_package_selection(cpkg, selected=False, handled=h)
        else:
            # The second possible case is that the package was deselected.
            # Basically this means that we have to deselect all reverse
            # dependencies.
            for rdep in pkg_info.get_reverse_dependencies():
                self.set_package_selection(rdep, selected=False, handled=h)
            for rsdep in pkg_info.get_strict_reverse_dependencies():
                self.set_package_selection(rsdep, selected=False, handled=h)
            for sdep in pkg_info.get_strict_dependencies():
                self.set_package_selection(sdep, selected=False, handled=h)
            
    def cursor_changed(self, treeview):
        """ Cursor change handler. """
        path, focuscol = self._treeview.get_cursor()
        iterator = self._store.get_iter(path)
        self._current_pkg = self._store.get_value(iterator, LIST_COL.PKG_INFO)
        
        if self._ui.expander_details.get_expanded():
            self.update_details()

    def row_activated(self, treeview, path, view_column):
        """ Double-click handler.

        .. note:: This handler expects row_toggled not to use the renderer
          parameter!
        """
        self.row_toggled(None, path)

    def row_toggled(self, renderer, path):
        """ Row toggle handler """
        iterator = self._store.get_iter(path)
        pkg = self._store.get_value(iterator, LIST_COL.PKG_INFO)

        if pkg is None:
            return False
        
        active_new = not pkg.active
        LOG.debug('Updated selection of %s (new: %s).', pkg, active_new)
        self.set_package_selection(pkg, active_new)

        self.update_download_size()
        self._ui.update_install_button()
        self._treeview.queue_draw()

    def update_download_size(self):
        """ Handler method that updates the download size label """
        downsize = 0
        for row in self._store:
            pkg_info = row[LIST_COL.PKG_INFO]
            if pkg_info and pkg_info.active:
                downsize += pkg_info.get_download_size()
                for udep in pkg_info.get_uninstalled_dependencies():
                    downsize += pkg_info.get_download_size()
            
        downsize_str = _("None")
        if downsize > 0:
            downsize_str = humanize_size(downsize)
                
        self._ui.label_downsize.set_text(_("Download size: %s") \
                                         % (downsize_str))
        
    def update_details(self):
        """ Details notebook updater """
        details_ctrl = self._ui.details_view
        pkg = self._current_pkg
            
        if pkg:
            details_ctrl.set_description_text(pkg.get_description())
            details_ctrl.set_sensitive(True)
            
            srcpkg = pkg.get_source_package_name()
            if srcpkg in self._changelogs.keys():
                LOG.debug("Using changelog present in cache (%s).", srcpkg)
                details_ctrl.set_changelog_text(self._changelogs[srcpkg])
            else:
                LOG.debug("Changelog not in cache, need to download (%s).",
                          srcpkg)
                details_ctrl.set_changelog_text(
                    _("Downloading list of changes..."))
                app = self._ui._application
                app.get_changelog(pkg, self)
        else:
            details_ctrl.set_description_text("")
            details_ctrl.set_changelog_text("")
            details_ctrl.set_sensitive(False)

    def _update_pkg_changelog(self, pkg_info, text):
        """ Helper function that updates the changelog text if
        the current package and the package passed to the method
        are the same.

        :param pkg_info: :class:`UpdateManager.Backend.PackageInfoBase` object
        :param text: Changelog text
        """
        if pkg_info == self._current_pkg:
            details_ctrl = self._ui.details_view
            details_ctrl.set_changelog_text(text)

    def changelog_finished(self, pkg_info, text):
        """ ChangelogHandler changelog_finished method """
        def update_func():
            self._changelogs[pkg_info.get_source_package_name()] = text
            self._update_pkg_changelog(pkg_info, text)
        gobject.idle_add(update_func)

    def changelog_failure(self, pkg_info, failure_message):
        """ ChangelogHandler changelog_failure method """
        def update_func():
            msg = _("Downloading list of changes failed.")
            self._changelogs[pkg_info.get_source_package_name()] = msg
            self._update_pkg_changelog(pkg_info, msg)
        gobject.idle_add(update_func)

class DetailsControl(object):
    """ Update details control/handler class """
    
    def __init__(self, userinterface, expander, gconfclient, nb_details,
                 tv_changes, tv_desc, vb_updates):
        """
        Constructor
        :param userinterface: GtkUI object
        :param expander: expander widget
        :param gconfclient: gconfclient object
        :param nb_details: details notebook widget
        :param tv_changes: changes textview widget
        :param tv_desc: description textview widget
        :param vb_updates: updates vbox
        """
        self._ui = userinterface
        self._expander = expander
        self._gconfclient = gconfclient
        self._nb_details = nb_details
        self._tv_changes = tv_changes
        self._tv_desc = tv_desc
        self._vb_updates = vb_updates

        # Create text view
        self._tv_changes.set_property("editable", False)
        self._tv_changes.set_cursor_visible(False)
        self._tv_changes.set_right_margin(4)
        self._tv_changes.set_left_margin(4)
        self._tv_changes.set_pixels_above_lines(4)
        self._tv_changes_buffer = self._tv_changes.get_buffer()
        self._tv_changes_buffer.create_tag("versiontag",
                                           weight=pango.WEIGHT_BOLD)
        self._tv_changes_buffer.set_text(_("Downloading list of changes..."))

        # Expander
        self._expander.connect("notify::expanded", self.expander_toggled)

    def expander_toggled(self, expander, data):
        """ Expander toggle handler """
        LOG.debug("Expander toggled.")
        expanded = self._expander.get_expanded()
        self._vb_updates.set_child_packing(self._expander, expanded, expanded,
                                           0, gtk.PACK_END)
        try:
            self._gconfclient.set_bool("/apps/update-manager/show_details",
                                       expanded)
        except (gconf.Error, glib.GError):
            pass

        if expanded:
            self._ui.update_list.update_details()

    def set_sensitive(self, state):
        """ Enables/disables control """
        self._nb_details.set_sensitive(state)

    def set_description_text(self, desc):
        """ Sets the description text. """
        # Regex magic
        
        # Add newline before each bullet
        re_compiled = re.compile(r'^(\s|\t)*(\*|0|-)', re.MULTILINE)
        desc = re_compiled.sub('\n*', desc)

        # replace all newlines by spaces
        re_compiled = re.compile(r'\n', re.MULTILINE)
        desc = re_compiled.sub(" ", desc)
        # replace all multiple spaces by newlines
        re_compiled = re.compile(r'\s\s+', re.MULTILINE)
        desc = re_compiled.sub("\n", desc)

        buf = self._tv_desc.get_buffer()
        buf.set_text(desc)

    def set_changelog_text(self, changelog):
        """ Sets the changelog text. """
        buf = self._tv_changes_buffer
        buf.set_text("")
        
        lines = changelog.split("\n")
        if len(lines) == 1:
            buf.set_text(changelog)
            return
        
        version_line = lines[0]
        version_info = version_line.split(' ')
        
        version_text = _("Version %s: ") % version_info[1][1:-1]
        version_text += "\n"
        
        end_iter = buf.get_end_iter()
        buf.insert_with_tags_by_name(end_iter, version_text,
                                     "versiontag")
        
        lines = lines[1:]
        for line in lines:
            if line.startswith(' -- '):
                continue
            
            end_iter = buf.get_end_iter()
            buf.insert(end_iter, line + "\n")
            
class GtkUI(SimpleGtkbuilderApp):
    """ Gtk/Glade userinterface class. """
    def __init__(self, frontend):
        self._frontend = frontend
        self._application = None
        self._dist_upgrade = None
        self._package_list_update = False
        self.dbus_controller = None
        self.setup_dbus()
        
        gtk.window_set_default_icon_name("update-manager")


        SimpleGtkbuilderApp.__init__(self, get_ui_path('UpdateManager.ui'))

        self.update_list = UpdateListControl(self, self.treeview_update)

        self.image_logo.set_from_icon_name("update-manager",
                                           gtk.ICON_SIZE_DIALOG)
        self.window_main.set_sensitive(False)
        self.window_main.grab_focus()
        self.button_close.grab_focus()

        self.window_main.connect("delete_event", self.close)
        self.button_close.connect("clicked", lambda w: self.exit())
        self.button_about.connect("clicked", self.on_button_about_clicked)

        # Disable the settings button if software-properties-gtk is not
        # installed.
        if not os.path.exists("/usr/bin/software-properties-gtk"):
            self.button_settings.set_sensitive(False)
        else:
            self.button_settings.connect("clicked",
                                         self.on_button_settings_clicked)
            self.button_settings.set_sensitive(True)

        # Initialize gconf connection.
        self._gconfclient = gconf.client_get_default()
        init_proxy(self._gconfclient)

        self.gconf_store_launch_time()

        self.textview_changes = ChangelogViewer()
        self.textview_changes.show()
        self.scrolledwindow_changes.add(self.textview_changes)

        # The details view has to be initialized *after* gconf!
        self.details_view = DetailsControl(self, self.expander_details,
                                           self._gconfclient,
                                           self.notebook_details,
                                           self.textview_changes,
                                           self.textview_descr,
                                           self.vbox_updates)

        self.cache_progress = GtkCacheProgress(self.dialog_cacheprogress,
                                               self.progressbar_cache,
                                               self.label_cache,
                                               self.window_main, self)
        self.list_progress = GtkListProgress(self.dialog_check,
                                             self.progressbar_check,
                                             self.label_check_summary,
                                             self.label_check_status,
                                             self.expander_check,
                                             self.button_check_cancel,
                                             self.treeview_check,
                                             self.vbox_checkdetails,
                                             self.scrolled_check,
                                             self)

        self.window_main.connect('focus-in-event', self.on_get_focus)
        self.restore_state()

    def on_get_focus(self, widget, data):
        """ On focus handler """
        if self.window_main.get_urgency_hint():
            self.window_main.set_urgency_hint(False)

    def gconf_store_launch_time(self):
        """ Saves the launch time via gconf, for use by update-notifier. """
        try:
            self._gconfclient.set_int("/apps/update-manager/launch_time",
                                      int(time.time()))
            LOG.debug("Stored launch time via gconf.")
        except gobject.GError, err:
            LOG.error("Could not set launch_time via gconf: %s", err)

    def setup_dbus(self):
        """ Sets up a DBUS listener if none is installed yet. """
        try:
            bus = dbus.SessionBus()
        except dbus.DBusException, db_exc:
            LOG.warning("DBUS initialization failed: %s", db_exc)
            return

        try:
            proxy_obj = bus.get_object('org.freedesktop.UpdateManager',
                                       '/org/freedesktop/UpdateManagerObject')
            iface = dbus.Interface(proxy_obj,
                                   'org.freedesktop.UpdateManagerIFace')
            LOG.info('Bringing running interface to front.')
            iface.bringToFront()
            sys.exit(0)
        except dbus.DBusException, err:
            LOG.debug('No listening object (%s)', err)
            bus_name = dbus.service.BusName('org.freedesktop.UpdateManager',
                                            bus)
            self.dbus_controller = GtkDbusController(self, bus_name)

    def close(self, widget, data=None):
        """ Close callback. """
        LOG.debug("Gtk close event.")
        if not self.window_main.get_property("sensitive"):
            return True
        else:
            self.exit()

    def exit(self):
        """ Saves the state and exits the application. """
        self.save_state()
        LOG.debug("Exiting.")
        self.set_exit()

    def save_state(self):
        """ Saves the state.

        Currently only the window-size is stored.
        """
        (pos_x, pos_y) = self.window_main.get_size()

        try:
            self._gconfclient.set_pair("/apps/update-manager/window_size",
                                       gconf.VALUE_INT, gconf.VALUE_INT,
                                       pos_x, pos_y)
            LOG.debug("State saved.")
        except gobject.GError, err:
            LOG.fatal("Could not save the configuration to gconf: %s", err)

    def restore_state(self):
        """ Restores the state from gconf. """
        pos_x = 0
        pos_y = 0
        try:
            (pos_x, pos_y) = self._gconfclient.get_pair(
                "/apps/update-manager/window_size", gconf.VALUE_INT,
                gconf.VALUE_INT)
        except (gconf.Error, glib.GError):
            pass
        if pos_x > 0 and pos_y > 0:
            self.window_main.resize(pos_x, pos_y)

        expanded = False
        try:
            expanded = self._gconfclient.get_bool(
                "/apps/update-manager/show_details")
        except (gconf.Error, glib.GError):
            pass
        self.expander_details.set_expanded(expanded)
        self.vbox_updates.set_child_packing(self.expander_details,
                                            expanded, True, 0, True)
        
        LOG.debug("State restored.")

    def show_window(self):
        """ Displays the main window. """
        self.window_main.show()
        LOG.debug("Main window made visible.")

    def on_button_reload_clicked(self, widget):
        """ Reload button click handler. """
        LOG.debug("Reload button clicked.")
        self._application.reload_package_list()

    def update_package_list(self):
        """ Package list updater. """
        if self._package_list_update:
            LOG.debug('Update already running...')
            return
        else:
            self._package_list_update = True
            
        self.button_install.set_sensitive(False)
        LOG.debug("Updating treeview.")
        self.label_header.set_markup(
            '<big><b>%s</b></big>'
            % _('Gathering information about updates...'))
        self.label_main_details.set_markup('')
        self.update_list.clear_store()
        self.update_list.set_sensitive(False)

        # Make sure all gtk events have been processed and the store is
        # actually empty before moving on...
        while not self.update_list.store_is_empty():
            if gtk.events_pending():
                gtk.main_iteration(block=False)
            else:
                time.sleep(0.2)

        self.set_busy_status()
        want_dist_upgrade = self._dist_upgrade
        if want_dist_upgrade is None:
            want_dist_upgrade = True

        pkg_info_store = self._application.get_available_updates(
            want_dist_upgrade)
        if pkg_info_store == None:
            LOG.error("pkg_info_store is None, has an error occured?")
            return
        
        if (pkg_info_store.get_removal_count() > 0 or \
               pkg_info_store.get_install_count() > 0) \
               and self._dist_upgrade is None:
            dialog = gtk.MessageDialog(parent=self.window_main,
                                       flags=gtk.DIALOG_MODAL,
                                       type=gtk.MESSAGE_QUESTION,
                                       buttons=gtk.BUTTONS_YES_NO)
            dialog.set_markup('<b>%s</b>' % (
                _("Upgrading may require removal or installation of new packages.")))
            dialog.format_secondary_text('%s' % (
                _("Do you want to perform a safe-upgrade, which does not remove packages or install new ones?")))

            dialog.show_all()
            res = dialog.run()
            
            dialog.hide_all()
            del dialog
            
            if res == gtk.RESPONSE_YES:
                self._dist_upgrade = False
                # The UI really needs to be updated here, so let's wait for
                # gtk.
                while gtk.events_pending():
                    gtk.main_iteration(block=False)
                pkg_info_store = self._application.get_available_updates(
                    self._dist_upgrade)
            else:
                self._dist_upgrade = True

        pkg_tree = pkg_info_store.get_packages()
        categories = {}
        text_label_main = ""
        found_update = False
        
        for cat_id in pkg_tree.keys():
            cat_name = self._application.get_update_category_name(cat_id)
            self.update_list.store_append_category(cat_name, cat_id)
            
            pkgs = pkg_tree[cat_id]
            
            for pkg_info in map(pkgs.get, sorted(pkgs.keys())):
                if getattr(pkg_info, 'active', None) is None:
                    selected = False
                    if pkg_info.is_installed():
                        selected = True
                    self.update_list.set_package_selection(pkg_info,
                                                           selected)
                self.update_list.store_append_pkg(pkg_info)
                found_update = True

        # Update the main window
        text_header = ""
        text_downsize = ""
        if not found_update:
            text_header = "<big><b>%s</b></big>" \
                          % _("Your system is up-to-date")

            # Disable everything that is unused when there are no updates
            # available.
            self.notebook_details.set_sensitive(False)
            self.treeview_update.set_sensitive(False)
            self.label_downsize.set_text("")
            self.textview_changes.get_buffer().set_text("")
            self.textview_descr.get_buffer().set_text("")
            
            self.button_close.grab_default()
            self.update_list.set_sensitive(False)
        else:
            # Updates available
            firstrun = False
            try:
                firstrun = self._gconfclient.get_bool(
                    "/apps/update-manager/first_run")
            except (gconf.Error, glib.GError):
                pass

            if firstrun:
                dist_name = self._application.get_dist_name()
                text_header = "<big><b>%s</b></big>" \
                              % (_("Welcome to %s!") % (dist_name))
                text_label_main = _("These software updates have been issued since %s was released.") % (dist_name)

                try:
                    self._gconfclient.set_bool(
                        "/apps/update-manager/first_run", False)
                except (gconf.Error, glib.GError):
                    pass
            else:
                text_header = "<big><b>%s</b></big>" \
                              % _("Software updates are available for this computer.")
                
            text_label_main += ' ' + _("If you don't want to install them now, choose \"Update Manager\" from the Administration menu later.")
            
            self.notebook_details.set_sensitive(True)
            self.treeview_update.set_sensitive(True)
            self.update_list.set_sensitive(True)
            self.button_install.grab_default()
            gobject.idle_add(self.update_list.update_download_size)

        # Update the labels and disable busy status.
        self.label_header.set_markup(text_header)
        self.label_main_details.set_text(text_label_main)
        gobject.idle_add(self.update_install_button)
        self._package_list_update = False
        gobject.idle_add(self.clear_busy_status)

    def on_button_about_clicked(self, source):
        """ Callback method for about button that shows the about dialog.

        :param source: Source of event, unused.
        """
        ad = gtk.AboutDialog()
        ad.set_title(_("About Update Manager"))
        ad.set_logo_icon_name("update-manager")
        ad.set_name(_("Update Manager"))
        ad.set_version(um_version)
        ad.set_authors(["Martin Wilemoes Hansen",
                        "Sebastian Heinlein",
                        "Michiel Sikkes",
                        "Stephan Peijnik",
                        "Michael Vogt"])
        ad.set_copyright("Copyright (C) 2004 - 2009 Canonical, and Others")
        ad.run()
        ad.hide()
        return False

    def update_install_button(self):
        """ Helper method that sets the install button to sensitive or not
        depending on whether at least one package is selected for upgrading
        """
        # The install button must only be sensitive if there is at least one
        # package is selected.
        sensitive = False
        for row in self.update_list._store:
            pkg = row[LIST_COL.PKG_INFO]
            if pkg and pkg.active:
                sensitive = True
                break

        self.button_install.set_sensitive(sensitive)
        return False

    def set_busy_status(self, state=True):
        """ Shows a watch cursor if the application is busy for more than 0.3
        seconds.
        Additionally implements a loop to handle user interface events
        meanwhile.
        """
        if self.window_main.window is None:
            return

        if state:
            LOG.debug("Busy status set.")
            self.window_main.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        else:
            LOG.debug("Busy status cleared.")
            self.window_main.window.set_cursor(None)

    def clear_busy_status(self):
        """ Wrapper around set_busy_status(False). This is purely cosmetic
        and should improve readability of code.
        """
        return self.set_busy_status(False)

    def on_keyboard_interrupt(self):
        """ Control+C handler """
        raise ExitProgramException(255, "Control+C invoked")

    def on_button_settings_clicked(self, widget):
        """ Settings button click handler.

        :param widget: Source of event
        """
        if os.getuid() != 0 and os.geteuid() != 0:
            LOG.debug("Starting software-properties-gtk with gksu.")
            desktop = "/usr/share/applications/software-properties.desktop"
            gobject.spawn_async(["/usr/bin/gksu", "--desktop",
                                 desktop])
        else:
            LOG.debug("Starting software-properties-gtk with gio.")
            ctx = gio.AppLaunchContext()
            app_info = gio.AppInfo("/usr/bin/software-properties-gtk",
                                   "/usr/bin/software-properties-gtk")
            try:
                app_info.launch(None, ctx)
            except gobject.GError, g_err:
                LOG.fatal("Could not execute software-properties-gtk: %s",
                          g_err)
            
    def on_button_install_clicked(self, widget):
        """ Install button click handler.

        :param widget: Source of event
        """
        selected_updates = []
        os.environ['DEBIAN_FRONTEND'] = "gnome"
        
        # Do we really want to use the none frontend here?
        os.environ['APT_LISTCHANGES_FRONTEND'] = "none"
        for row in self.update_list.get_store():
            pkg_info = row[LIST_COL.PKG_INFO]
            if pkg_info and pkg_info.active:
                selected_updates.append(pkg_info)
        fork_func = self.list_progress.get_terminal_fork_func()
        self._application.commit(selected_updates, fork_func)
