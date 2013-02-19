# tests/_mock/Frontend.py
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
#from tests._mock.Backend import MockCacheHandler, MockListHandler
#from tests._mock.Backend import MockCommitHandler

from UpdateManager.Frontend import FrontendBase

class MockFrontendGenerator(MockGenerator):
    def __init__(self, *init_args, **init_kwargs):
        self._return_value = 0
        self._cache_hdlr = None
        self._uses_privileged_funcs = False
        self._list_hdlr = None
        self._commit_hdlr = None
        MockGenerator.__init__(self, FrontendBase, *init_args, **init_kwargs)

    def set_return_value(self, value):
        self._return_value = value

    def _override__get_cache_handler(self):
        return self._cache_hdlr

    def set_cache_hdlr(self, cache_hdlr):
        self._cache_hdlr = cache_hdlr

    def _override__get_list_handler(self):
        return self._list_hdlr

    def set_list_hdlr(self, list_hdlr):
        self._list_hdlr = list_hdlr

    def _override__get_commit_handler(self):
        return self._commit_hdlr

    def set_commit_hdlr(self, commit_hdlr):
        self._commit_hdlr = commit_hdlr
        
    def _override__main(self, app):
        return self._return_value
        
    def _override__uses_privileged_functions(self):
        return self._uses_privileged_funcs

    def set_uses_privileged_funcs(self, priv_funcs):
        self._uses_privileged_funcs = priv_funcs
