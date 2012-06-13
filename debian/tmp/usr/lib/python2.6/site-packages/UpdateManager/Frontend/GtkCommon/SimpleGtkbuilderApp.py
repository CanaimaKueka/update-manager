"""
 SimpleGladeApp.py
 Module that provides an object oriented abstraction to pygtk and libglade.
 Copyright (C) 2004 Sandino Flores Moreno
 Copyright (C) 2009 Stephan Peijnik
"""

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import os
import sys
import re
import threading
import logging

import gtk
import gobject

LOG = logging.getLogger('UpdateManager.Frontend.GtkCommon.SimpleGtkbuilderApp')

# based on SimpleGladeApp
class SimpleGtkbuilderApp(object):

    def __init__(self, path):
        self.builder = gtk.Builder()
        self.builder.add_from_file(path)
        self.builder.connect_signals(self)
        self._exit_event = threading.Event()
        self._running_event = threading.Event()
        for o in self.builder.get_objects():
            if isinstance(o, gtk.Buildable):
                setattr(self, gtk.Buildable.get_name(o), o)
            else:
                setattr(self, o.get_name(), o)

    def set_exit(self):
        self._exit_event.set()

    def is_exit_pending(self):
        return self._exit_event.isSet() and self._running_event.isSet()

    def is_running(self):
        return self._running_event.isSet()

    def run(self):
        """
        Starts the main loop of processing events checking for Control-C.

        The default implementation checks wheter a Control-C is pressed,
        then calls on_keyboard_interrupt().

        Use this method for starting programs.
        """
        try:
            self._running_event.set()
            while not self._exit_event.isSet():
                while gtk.events_pending():
                    gtk.main_iteration()

                # Intelligent waiting:
                # We put this thread to sleep if there are no gtk events
                # pending.
                # 
                # gtk.main_iteration() will now block until the timeout
                # is detected.
                if not gtk.events_pending():
                    def timeout_func():
                        pass
                    gobject.timeout_add(200, timeout_func)
                    gtk.main_iteration()
                    
            LOG.debug("Exit event received.")
            self._exit_event.clear()
            self._running_event.clear()
        except KeyboardInterrupt:
            LOG.debug("KeyboardInterrupt received.")
            self._exit_event.clear()
            self._running_event.clear()
            self.on_keyboard_interrupt()
        except:
            # We need to mark the main loop as exited first and then raise
            # the exception again.
            LOG.debug("Exception inside main loop.")
            self._exit_event.clear()
            self._running_event.clear()
            raise

    def on_keyboard_interrupt(self):
        """
        This method is called by the default implementation of run()
        after a program is finished by pressing Control-C.
        """
        pass

