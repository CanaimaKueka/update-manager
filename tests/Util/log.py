# tests/Util/log.py
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
import os
from UpdateManager.Util import log


class LogCase(unittest.TestCase):
    def test0_environ_set(self):
        os.environ['DEBUG_UPDATE_MANAGER'] = '1'
        log.init_logging()
        logger = logging.getLogger('UpdateManager')
        self.failUnless(logger.getEffectiveLevel() == logging.DEBUG)
        del os.environ['DEBUG_UPDATE_MANAGER']

    def test1_environ_unset(self):
        if 'DEBUG_UPDATE_MANAGER' in os.environ:
            del os.environ['DEBUG_UPDATE_MANAGER']
        log.init_logging()
        logger = logging.getLogger('UpdateManager')
        self.failUnless(logger.getEffectiveLevel() == log.DEFAULT_LOGLEVEL)

LogSuite = loader.loadTestsFromTestCase(LogCase)
