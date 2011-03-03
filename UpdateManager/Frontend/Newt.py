# UpdateManager/Frontend/Newt.py
#
#  Copyright (c) 2009 Canonical
#                2009 Stephan Peijnik
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

""" Newt/snack text interface """

import logging
import subprocess
import os
import sys
import time

LOG = logging.getLogger('UpdateManager.Frontend.Newt')

from gettext import gettext as _
from snack import SnackScreen, ButtonBar, Textbox, CheckboxTree, GridForm
from snack import snackArgs

from UpdateManager.Backend import CacheProgressHandler
from UpdateManager.Frontend import FrontendBase

class NewtCacheProgressHandler(CacheProgressHandler):
    def __init__(self, ui):
        CacheProgressHandler.__init__(self)
        self._ui = ui
        self._op = ''
        
    def cache_begin(self):
        sys.stdout.write(_('Loading package cache.') + '\n')
        sys.stdout.flush()

    def cache_finished(self):
        sys.stdout.write(_('Finished loading package cache.') + '\n')
        sys.stdout.flush()
        self._ui.get_updates()
                                        
    def cache_update(self, progress):
        sys.stdout.write('[%2d] %s\r' % (progress, self._op))
        sys.stdout.flush()

    def cache_operation(self, operation):
        if self._op:
            sys.stdout.write('DONE: %s\n' % (self._op))
            sys.stdout.flush()
        self._op = operation
        
class NewtUI(object):
    """ Newt UI implementation """
    def __init__(self, frontend):
        self._frontend = frontend
        self.screen = SnackScreen()
        self.textview_changes = None
        self.button_bar = None
        self.checkbox_tree_updates = None
        self.layout = None
        self._app = None
        self._updates_received = False

    def create_ui(self):
        """ Creates/Draws the UI """
        self.button_bar = ButtonBar(self.screen,
                                    ( (_("Cancel"), "cancel"),
                                      (_("Install"), "ok")),
                                    compact = True)
        self.textview_changes = Textbox(72, 8, "Changelog", True, True)
        self.checkbox_tree_updates = CheckboxTree(height=8, width=72, scroll=1)
        self.checkbox_tree_updates.setCallback(self.checkbox_changed)
        self.layout = GridForm(self.screen, "Updates", 1, 5)
        self.layout.add(self.checkbox_tree_updates, 0, 0)
        # empty line to make it look less crowded
        self.layout.add(Textbox(60, 1, " ", False, False), 0, 1)
        self.layout.add(self.textview_changes, 0, 2)
        # empty line to make it look less crowded
        self.layout.add(Textbox(60, 1, " ", False, False), 0, 3)
        self.layout.add(self.button_bar, 0, 4)
        # FIXME: better progress than the current suspend/resume screen thing
        self.screen.suspend()

    def cache_reload_callback(self, percent, operation):
        """ Cache reloading callback

        :param percent: Percentage done
        :param operation: Current operation
        """
        if percent == RELOAD_CACHE_STATUS.DONE:
            sys.stdout.write(_('Finished loading package cache.') + '\n')
        elif percent == RELOAD_CACHE_STATUS.BEGIN:
            sys.stdout.write(_('Loading package cache.') + '\n')
        else:
            sys.stdout.write('[%2d] %s\r' % (percent, operation))

    def main(self, application):
        """ UI main loop

        :param application: class:`UpdateManager.Application.Application`
          object
        """
        self._app = application

        while not self._updates_received:
            time.sleep(0.3)

        self.screen.resume()
        res = self.layout.runOnce()
        self.screen.finish()
        button = self.button_bar.buttonPressed(res)
        if button == "ok":
            self.screen.suspend()
                                        

    def get_updates(self):
        sys.stdout.write(_("Building Updates List") + "\n")
        sys.stdout.flush()

        packages = self._app.get_available_updates()
        # download_size = 0
        categories = {}

        for pkg in packages:
            catid = pkg.get_update_category()
            if not catid in categories.keys():
                categories[catid] = [pkg, ]
            else:
                categories[catid].append(pkg)

        for (i, cat_id) in enumerate(categories.keys()):
            cat_name = self._app.get_update_category_name(cat_id)
            self.checkbox_tree_updates.append(cat_name, selected=True)
            for pkg in categories[cat_id]:
                self.checkbox_tree_updates.addItem(pkg.get_package_name(),
                                                   (i, snackArgs['append']),
                                                   pkg,
                                                   selected=True)
        self._updates_received = True

    def update_ui(self):
        """ Redraws the UI """
        self.layout.draw()
        self.screen.refresh()

    def checkbox_changed(self):
        """ Handler for checkbox state-changes """
        pkg = self.checkbox_tree_updates.getCurrent()
        descr = ""

        if hasattr(pkg, "get_description"):
            descr = pkg.get_description()
        # TODO: changelog handling/selection of changelog instead of
        # description

        self.textview_changes.setText(descr)
        self.update_ui()

class NewtFrontend(FrontendBase):
    """ Newt/Snack text frontend """
    def __init__(self, *args, **kwargs):
        FrontendBase.__init__(self, *args, **kwargs)
        self._ui = None
        
    def init_frontend(self):
        """ Early frontend initialization
        """
        self._ui = NewtUI(self)
        self._ui.create_ui()
        self.cache_reload_callback = self._ui.cache_reload_callback

    def main(self, application):
        """ Main loop

        :param application: :class:`UpdateManager.Application.Application`
          object
        """
        return self._ui.main(application)

    def handle_unprivileged_invocation(self, app_args):
        """ Newt unprivileged user handler. """
        cmd = ' '.join(app_args)
        if os.path.exists('/usr/bin/sudo'):
            LOG.debug('Spwaning new update-manager process via sudo.')
            return subprocess.call(['/usr/bin/sudo', cmd])

        # Fall back to su
        LOG.debug('Spawning new update-manager process via su.')
        return subprocess.call(['/bin/su', '-c', cmd])
                                   

    def get_cache_handler(self):
        return NewtCacheProgressHandler(self._ui)
