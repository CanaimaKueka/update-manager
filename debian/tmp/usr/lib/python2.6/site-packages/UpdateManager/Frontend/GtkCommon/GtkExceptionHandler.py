# UpdateManager/Frontend/GtkCommon/GtkExceptionHandler.py
#  
#  Copyright (c) 2009 Stephan Peijnik
#  
#  Author: Stephan Peijnik <debian@sp.or.at>
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

""" Gtk Exception Handler module """

import gtk
import os
import time
import sys
import subprocess
import traceback

import logging

from gettext import gettext as _

if __name__ == '__main__':
    pass
else:
    from UpdateManager.BugHandler import ExceptionHandlerBase
    LOG = logging.getLogger(
        "UpdateManager.Frontend.GtkCommon.GtkExceptionHandler")

    class GtkExceptionHandler(ExceptionHandlerBase):
        """ Gtk implementation of
        :class:`UpdateManager.BugHandler.ExceptionHandlerBase`
        """
        @classmethod
        def gtk_setup(cls, gtk_builder_app):
            cls.gtk_is_running = gtk_builder_app.is_running
            cls.gtk_is_exit_pending = gtk_builder_app.is_exit_pending
            cls.gtk_set_exit = gtk_builder_app.set_exit
            cls.pre_handle_exception = cls._pre_handle_exception
            
        @classmethod
        def _pre_handle_exception(cls):
            if cls.gtk_is_running() and False:
                if not cls.gtk_is_exit_pending():
                    cls.gtk_set_exit()
                LOG.debug("Waiting for GTK main loop to exit...")
                while cls.gtk_is_running():
                    time.sleep(0.5)
                LOG.debug("GTK main loop exited.")
            
        @classmethod
        def handle_exception(cls, ex_type, ex_value, ex_tb, ex_origin,
                             with_script):
            """ Exception handler """
            LOG.debug("Exception detected: type=%s,value=%s,tb=%s,origin=%s",
                      ex_type, ex_value, ex_tb, ex_origin)
            LOG.debug("Backtrace:")
            exception_lines = traceback.format_exception(ex_type, ex_value,
                                                         ex_tb)
            for line in exception_lines:
                LOG.debug(" %s", line.strip('\n'))
            LOG.debug("Starting subprocess...")
            res = subprocess.call(['python', __file__,
                                   "%s" % (with_script)])
            LOG.debug("Subprocess returned: %s", res)
            return res == 0

if __name__ == '__main__':
    dialog = None
    gtk.init_check()
    if sys.argv[1] == "True":
        dialog = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_YES_NO)
        dialog.set_markup(_("A fatal error has been detected in update-manager."))
        dialog.format_secondary_markup("%s\n\n%s" % (
            _("Do you want to submit a bug report?"),
            _("Selecting No will close the application.")))
    else:
        dialog = gtk.MessageDialog(parent=None, type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_CLOSE)
        dialog.set_markup(_("A fatal error has been detected in update-manager."))
        dialog.format_secondary_markup(_("The program will now exit."))

    res = dialog.run()
    if res == gtk.RESPONSE_YES:
        sys.exit(0)
    else:
        sys.exit(1)
