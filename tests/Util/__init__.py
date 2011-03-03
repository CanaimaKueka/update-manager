# tests/Util/__init__.py
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

from tests.Util.enum import EnumSuite, NegativeEnumSuite
from tests.Util.humanize import HumanizeSuite
from tests.Util.lsb import LSBSuite
from tests.Util.log import LogSuite

UtilSuite = unittest.TestSuite([EnumSuite, NegativeEnumSuite, LSBSuite, 
                                LogSuite, HumanizeSuite])
