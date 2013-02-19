# tests/__init__.py
#
#  Copyright (c) 2009 Canonical
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

from _helpers import InterfaceValidatorSuite
from tests.Application import ApplicationSuite
from tests.Backend import BackendSuite
from tests.DistSpecific import DistSuite
from tests.Frontend import FrontendSuite
from tests.Util import UtilSuite

UpdateManagerSuite = unittest.TestSuite(
    [InterfaceValidatorSuite,
     ApplicationSuite,
     BackendSuite,
     DistSuite,
     FrontendSuite,
     UtilSuite])

def run_tests():
    try:
        import nose
        nose.run(suite=UpdateManagerSuite)
    except ImportError:
        unittest.TextTestRunner(verbosity=2).run(UpdateManagerSuite)
