# tests/Frontend/Gtk/GtkProgress.py
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
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import unittest

loader = unittest.TestLoader()

from tests._helpers import InterfaceValidator, ValidationFailed

from UpdateManager.Frontend.Gtk.GtkProgress import BackendProgressHandlerObject
from UpdateManager.Backend import CommitProgressHandler, ListProgressHandler

class CommitProgressHandlerCase(unittest.TestCase):
    def test0_implements_interface(self):
        try:
            InterfaceValidator(CommitProgressHandler, 
                               BackendProgressHandlerObject).validate()
        except ValidationFailed, v_failed:
            self.fail(v_failed.message)

CommitProgressHandlerSuite = loader.loadTestsFromTestCase(
    CommitProgressHandlerCase)

class ListProgressHandlerCase(unittest.TestCase):
    def test0_implements_interface(self):
        try:
            InterfaceValidator(ListProgressHandler,
                               BackendProgressHandlerObject).validate()
        except ValidationFailed, v_failed:
            self.fail(v_failed.message)


ListProgressHandlerSuite = loader.loadTestsFromTestCase(
    ListProgressHandlerCase)

GtkProgressSuite = unittest.TestSuite([CommitProgressHandlerSuite,
                                      ListProgressHandlerSuite])
