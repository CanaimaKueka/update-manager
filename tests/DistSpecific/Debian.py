# tests/DistSpecific/Debian.py
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

from tests._helpers import InterfaceValidator, ValidationFailed

from UpdateManager.DistSpecific.Debian import DebianDist
from UpdateManager.DistSpecific import DistBase

class DebianCase(unittest.TestCase):
    def test0_implements_distbase(self):
        try:
            InterfaceValidator(DistBase, DebianDist).validate()
        except ValidationFailed, v_failed:
            self.fail(v_failed.message)

DebianSuite = loader.loadTestsFromTestCase(DebianCase)
