# tests/Application.py
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

import unittest

loader = unittest.TestLoader()

import logging
import sys

MOCK_UID = 0

class MockGetuid(object):
    def __init__(self, uid):
        self._uid = uid
        sys.modules['os'].getuid = self
        sys.modules['os'].geteuid = self

    def __call__(self):
        return self._uid

    def set_uid(self, uid):
        self._uid = uid

REAL_GETUID = sys.modules['os'].getuid
MOCK_GETUID = MockGetuid(0)

from tests._mock.Frontend import MockFrontendGenerator
from tests._mock.Backend import MockBackendGenerator
from tests._mock.DistSpecific import MockDistGenerator

from UpdateManager.Application import Application, InvalidBaseClass
from UpdateManager.Application import ExitProgramException
from UpdateManager.Application import LoadingFailedException

from UpdateManager.Frontend import FrontendBase
from UpdateManager.Backend import BackendBase
from UpdateManager.DistSpecific import DistBase
from UpdateManager.Util.log import LOGLEVEL_NAME_MAP

### custom logging handler to suppress all log output
class DevNullLoggingHandler(logging.StreamHandler):
    def emit(self, record):
        pass

logger = logging.getLogger('UpdateManager')
for hdlr in logger.handlers:
    logger.removeHandler(hdlr)
logger.addHandler(DevNullLoggingHandler())

### Mock objects
FrontendGenerator = MockFrontendGenerator()
BackendGenerator = MockBackendGenerator()
DistGenerator = MockDistGenerator()
MockFrontend = FrontendGenerator.cls
MockBackend = BackendGenerator.cls
MockDist = DistGenerator.cls

### Application.Application test case
class ApplicationCase(unittest.TestCase):
    def test0_invalid_frontend_name(self):
        self.assertRaises(LoadingFailedException, Application,
                          "update-manager", "/usr/share/locale",
                          frontend="NONEXISTANT", app_args=[])
        
    def test1_invalid_backend_name(self):
        self.assertRaises(LoadingFailedException, Application,
                          "update-manager", "/usr/share/locale",
                          frontend="Gtk", backend="NONEXISTANT", app_args=[])
        
    def test2_invalid_dist_name(self):
        self.assertRaises(LoadingFailedException, Application,
                          "update-manager", "/usr/share/locale",
                          frontend="Gtk", dist_specific="NONEXISTANT",
                          app_args=[])

    def test3_invalid_frontend(self):
        self.assertRaises(AssertionError, Application, "update-manager",
                          "/usr/share/locale", frontend=object, app_args=[])
        self.assertRaises(AssertionError, Application, "update-manager",
                          "/usr/share/locale", frontend=object(), app_args=[])
        self.assertRaises(AssertionError, Application, "update-manager",
                          "/usr/share/locale", frontend=MockFrontend(),
                          app_args=[])

    def test4_invalid_backend(self):
        self.assertRaises(AssertionError, Application, "update-manager",
                          "/usr/share/locale", frontend=MockFrontend,
                          backend=object, app_args=[])
        self.assertRaises(AssertionError, Application, "update-manager",
                          "/usr/share/locale", frontend=MockFrontend,
                          backend=object(), app_args=[])
        self.assertRaises(AssertionError, Application, "update-manager",
                          "/usr/share/locale", frontend=MockFrontend,
                          backend=MockBackend(), app_args=[])

    def test5_invalid_dist(self):
        self.assertRaises(AssertionError, Application, "update-manager",
                          "/usr/share/locale", frontend=MockFrontend,
                          backend=MockBackend, dist_specific=object,
                          app_args=[])
        self.assertRaises(AssertionError, Application, "update-manager",
                          "/usr/share/locale", frontend=MockFrontend,
                          backend=MockBackend, dist_specific=object(),
                          app_args=[])
        self.assertRaises(AssertionError, Application, "update-manager",
                          "/usr/share/locale", frontend=MockFrontend,
                          backend=MockBackend, dist_specific=MockDist(),
                          app_args=[])

    def test6_init_loglevel_setting(self):
        logger = logging.getLogger('UpdateManager')
        for level_name in LOGLEVEL_NAME_MAP:
            level = LOGLEVEL_NAME_MAP[level_name]

            app = Application("update-manager", "/usr/share/locale",
                              frontend=MockFrontend,
                              backend=MockBackend,
                              app_args=["-l", level_name])
            self.failUnless(logger.getEffectiveLevel() == level)
            del app
            
        # Next test: invalid loglevel name
        self.assertRaises(ExitProgramException, Application, "update-manager",
                          "/usr/share/locale", frontend=MockFrontend,
                          backend=MockBackend,
                          app_args=["-l", "INVALID_LEVEL"])

    def test7_init_debugoption(self):
        logger = logging.getLogger('UpdateManager')
        app = Application("update-manager", "/usr/share/locale",
                          frontend=MockFrontend, backend=MockBackend,
                          app_args=["-d",])
        self.failUnless(logger.getEffectiveLevel() == logging.DEBUG)

    def test8_main(self):
        app = Application("update-manager", "/usr/share/locale",
                          frontend=MockFrontend, backend=MockBackend,
                          app_args=[])
        self.assertRaises(ExitProgramException, app.main)
        # TODO: should we test for the correct invocation path here?

    def test9_init_nonroot_privileged(self):
        MOCK_GETUID.set_uid(1001)
        BackendGenerator.set_requires_root(True)
        FrontendGenerator.set_uses_privileged_funcs(True)
        self.assertRaises(ExitProgramException, Application,
                          "update-manager", "/usr/share/locale",
                          frontend=MockFrontend,
                          backend=MockBackend,
                          app_args=[])
        
    def test10_init_root_privileged(self):
        MOCK_GETUID.set_uid(0)
        BackendGenerator.set_requires_root(True)
        FrontendGenerator.set_uses_privileged_funcs(True)
        try:
            app = Application("update-manager", "/usr/share/locale",
                              frontend=MockFrontend,
                              backend=MockBackend,
                              app_args=[])
        except ExitProgramException:
            self.fail('ExitProgramException raised.')

    def test11_init_nonroot_unprivileged(self):
        MOCK_GETUID.set_uid(1000)
        BackendGenerator.set_requires_root(True)
        FrontendGenerator.set_uses_privileged_funcs(False)
        try:
            app = Application("update-manager", "/usr/share/locale",
                              frontend=MockFrontend,
                              backend=MockBackend,
                              app_args=['-d'])
        except ExitProgramException:
            self.fail('ExitProgramException raised.')
        
ApplicationSuite = loader.loadTestsFromTestCase(ApplicationCase)
