# UpdateManager/DistSpecific/Auto/__init__.py
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

""" Automatic distribution selection module """

from UpdateManager.DistSpecific import DistBase
from UpdateManager.DistSpecific.loader import DistLoader
from UpdateManager.Util.lsb import get_distribution_name

class AutoDist(DistBase):
    """ Automatic distribution selection """
    def __init__(self, *args, **kwargs):
        dist_name = get_distribution_name()
        from UpdateManager.Application import Application
        self._dist = Application._load_meta(DistLoader, dist_name,
                                            "dist_specific", DistBase)

    def has_distupgrade_check(self):
        """ Wrapper around detected distribution's method """
        return self._dist.has_distupgrade_check()

    def fetch_dist_info(self):
        """ Wrapper around detected distribution's method """
        return self._dist.fetch_dist_info()

    def get_name(self):
        """ Wrapper around detected distribution's method """
        return self._dist.get_name()

    def get_update_category(self, package_upd_info):
        """ Wrapper around detected distribution's method """
        return self._dist.get_update_category(package_upd_info)

    def get_update_category_name(self, update_category_id):
        """ Wrapper around detected distribution's method """
        return self._dist.get_update_category_name(update_category_id)

    def get_changelog(self, pkg_info, changelog_handler):
        """ Wrapper around detected distribution's method """
        return self._dist.get_changelog(pkg_info, changelog_handler)

    def get_bug_script_name(self):
        """ Wrapper around detected distribution's method """
        return self._dist.get_bug_script_name()
