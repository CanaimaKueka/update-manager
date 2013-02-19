# tests/Util/enum.py
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

loader = unittest.TestLoader()

from UpdateManager.Util.enum import Enum, NegativeEnum

class EnumCase(unittest.TestCase):
    def test0_enum_nodoc(self):
        enum = Enum('TEST0', 'TEST1')
        self.assertEquals(enum.TEST0, 0)
        self.assertEquals(enum.TEST1, 1)

    def test1_enum_doc(self):
        enum = Enum(TEST0='Test0', TEST1 = 'Test1')
        self.assertTrue(enum.TEST0 >= 0)
        self.assertTrue(enum.TEST0 < 2)
        self.assertTrue(enum.TEST1 >= 0)
        self.assertTrue(enum.TEST1 < 2)

    def test2_z_in_name(self):
        try:
            enum = Enum('NAME_WITH_Z', ANOTHER_Z='Name with z')
        except TypeError, te:
            self.fail('Z not accepted in name')        

    def test3_9_in_name(self):
        try:
            enum = Enum('NAME_WITH_9', ANOTHER_9='Name with 9')
        except TypeError, te:
            self.fail('9 not accepted in name')

EnumSuite = loader.loadTestsFromTestCase(EnumCase)

class NegativeEnumCase(unittest.TestCase):
    def test0_enum_nodoc(self):
        enum = NegativeEnum('TEST0', 'TEST1')
        self.assertEquals(enum.TEST0, -1)
        self.assertEquals(enum.TEST1, -2)

    def test1_enum_doc(self):
        enum = NegativeEnum(TEST0 = 'Test0', TEST1 = 'Test1')

NegativeEnumSuite = loader.loadTestsFromTestCase(NegativeEnumCase)
