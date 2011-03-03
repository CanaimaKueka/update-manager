# tests/_mock/Backend.py
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

from tests._mock import MockGenerator
from UpdateManager.Backend import BackendBase

class MockBackendGenerator(MockGenerator):
    def __init__(self, *init_args, **init_kwargs):
        MockGenerator.__init__(self, BackendBase, *init_args, **init_kwargs)
        self._requires_root = False
        self._is_locked = False

    def _override__init_backend(self, application):
        self._app = application

    def _override__requires_root(self):
        return self._requires_root

    def set_requires_root(self, value):
        self._requires_root = value

    def _override__is_locked(self):
        return self._is_locked

    def set_is_locked(self, value):
        self._is_locked = value
