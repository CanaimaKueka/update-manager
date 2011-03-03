# tests/Util/lsb.py
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

from UpdateManager.Util import lsb

import subprocess

class LSBCase(unittest.TestCase):
    def test0_dist_name(self):
        out = subprocess.Popen(['lsb_release', '-si'],
                               stdout=subprocess.PIPE).communicate()[0]
        self.assertEqual(lsb.get_distribution_name(), out.strip())

    def test1_dist_release(self):
        out = subprocess.Popen(['lsb_release', '-sr'],
                               stdout=subprocess.PIPE).communicate()[0]
        self.assertEqual(lsb.get_distribution_release(), out.strip())

    def test2_dist_codename(self):
        out = subprocess.Popen(['lsb_release', '-sc'],
                               stdout=subprocess.PIPE).communicate()[0]
        self.assertEqual(lsb.get_distribution_codename(), out.strip())

    def test3_invalid_call(self):
        self.assertRaises(lsb.LSBError, lsb._invoke_lsb_release, '-Z')
                

LSBSuite = loader.loadTestsFromTestCase(LSBCase)
