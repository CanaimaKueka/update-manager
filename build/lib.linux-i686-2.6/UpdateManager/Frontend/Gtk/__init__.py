# UpdateManager/Frontend/Gtk/__init__.py
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

""" Gtk frontend module """

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import logging
import os.path
import subprocess

from gettext import gettext as _

from UpdateManager.BugHandler import BugHandler
from UpdateManager.Frontend import FrontendBase
from UpdateManager.Frontend.Gtk.GtkProgress import GtkCacheProgress
from UpdateManager.Frontend.Gtk.ui import GtkUI
from UpdateManager.Frontend.GtkCommon import get_desktop_path
from UpdateManager.Frontend.GtkCommon.GtkExceptionHandler import \
     GtkExceptionHandler

LOG = logging.getLogger("UpdateManager.Frontend.Gtk")

class GtkFrontend(FrontendBase):
    """
    Gtk frontend implementation.
    """

    def __init__(self):
        self._ui = None
        gobject.threads_init()
        gtk.init_check()
        FrontendBase.__init__(self, uses_privileged_funcs=True)

    def init_gettext(self, app_name, locale_dir):
        """ Gtk/Glade gettext initialization """
        # Initializing glade gettext isn't needed for GtkBuilder anymore
        pass

    def init_frontend(self):
        """ Gtk/Glade frontend initialization """
        BugHandler.install_handler(GtkExceptionHandler)
        self._ui = GtkUI(self)
        GtkExceptionHandler.gtk_setup(self._ui)
        self._ui.show_window()
        self._ui.window_main.set_sensitive(True)

    def main(self, application):
        """ Gtk/Glade main loop invocation. """
        self._ui._application = application
        self._ui.run()
        return 0

    def handle_unprivileged_invocation(self, app_args):
        """ Gtk/Glade unprivileged user handler. """
        cmd = ' '.join(app_args)
        LOG.debug('Spawning new update-manager process via gksu.')
        return subprocess.call(['/usr/bin/gksu', '-k', '-D',
                                get_desktop_path('update-manager.desktop'),
                                                 '--', cmd])

    def get_cache_handler(self):
        """
        Returns a CacheProgressHandler implementation instance.
        """
        return self._ui.cache_progress

    def get_list_handler(self):
        """
        Returns a ListProgressHandler implementation instance.
        """
        return self._ui.list_progress

    def get_commit_handler(self):
        """
        Returns a CommitProgressHandler implementation instance.
        """
        return self._ui.list_progress

    def handle_exception(self, exception):
        """
        Handles an uncaught exception.

        :param exception: Exception instance

        .. versionadded: 0.200.1
        """
        error_dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                                         buttons=gtk.BUTTONS_OK)
        error_dialog.set_markup('<b>%s</b>' \
                                % _('A fatal error has been detected'))
        error_dialog.format_secondary_markup(_('Exception:\n %s') %\
                                             (str(exception)))
        res = error_dialog.run()
        self._ui.set_exit()
