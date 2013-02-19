#!/usr/bin/env python
# run_tests.py
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

import os

SCRIPT_ABSPATH=os.path.abspath(__file__)
DIR_ABSPATH=os.path.abspath(os.path.dirname(SCRIPT_ABSPATH))

import sys

sys.path.insert(0, DIR_ABSPATH)

from tests import run_tests

if __name__ == '__main__':
    run_tests()
