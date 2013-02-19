# tests/_mock/DistSpecific.py
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
from UpdateManager.DistSpecific import DistBase
from UpdateManager.DistSpecific.changelog import ChangelogFetcher

class MockChangelogFetcherGenerator(MockGenerator):
    def __init__(self, *init_args, **init_kwargs):
        MockGenerator.__init__(self, ChangelogFetcher, *init_args,
                               **init_kwargs)

    def _override__do_fetch(self):
        self._handler.changelog_failure(self._pkg_info, exc.message)

class MockDistGenerator(MockGenerator):
    def __init__(self, *init_args, **init_kwargs):
        if not "name" in init_kwargs.keys():
            init_kwargs["name"] = "MockDist"
        if not "changelog_fetcher" in init_kwargs.keys():
            mock_changelog_fetcher_gen = MockChangelogFetcherGenerator()
            init_kwargs["changelog_fetcher"] = mock_changelog_fetcher_gen.cls
        
        MockGenerator.__init__(self, DistBase, *init_args, **init_kwargs)
