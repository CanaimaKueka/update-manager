# UpdateManager/DistSpecific/__init__.py
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

from gettext import gettext as _

from UpdateManager.Util.enum import Enum

""" Distribution specific functionality """

UPDATE_CATEGORY = Enum('SECURITY',
                       'RECOMMENDED',
                       'DEFAULT',
                       'PROPOSED',
                       'BACKPORT',
                       'THIRDPARTY')

UPDATE_CATEGORY_MAP = {
    UPDATE_CATEGORY.SECURITY: _("Important security updates"),
    UPDATE_CATEGORY.RECOMMENDED: _("Recommended updates"),
    UPDATE_CATEGORY.DEFAULT: _("Distribution updates"),
    UPDATE_CATEGORY.PROPOSED: _("Proposed updates"),
    UPDATE_CATEGORY.BACKPORT: _("Backports"),
    UPDATE_CATEGORY.THIRDPARTY: _("Third-party updates"),
    }
"""
A mapping of update category identifiers to their (localized)
names. See UPDATE_CATEGORY for details.
"""

class DistBase(object):
    """
    Base class for distribution specific functionality.

    This class defines the API available to update-manager's core.
    
    Implementations *must* be subclasses of this base class.
    """
    def __init__(self, name=None, changelog_fetcher=None,
                 distupgrade_check=False):
        assert(name != None)
        assert(changelog_fetcher != None)
        self._name = name
        self._changelog_fetcher = changelog_fetcher
        self._distupgrade_check = distupgrade_check
        
    @classmethod
    def has_distupgrade_check(cls):
        """
        Define whether this implementation can check for distribution
        upgrades (MetaRelease functionality).
        """
        return self._distupgrade_check

    @classmethod
    def fetch_dist_info(cls):
        """
        Called only when hasDistUpgradeCheck returns True.

        This method should do the actual check (MetaRelease functionality).
        """
        pass

    def get_name(self):
        """
        Returns the distribution name.
        """
        return self._name

    def get_update_category(self, pkg_info):
        """
        Returns an update category ID for the package referred to by
        package_upd_info.

        :param pkg_info: :class:`UpdateManager.Backend.PackageInfoBase` object.
        :returns: Update category ID
        """
        raise NotImplementedError

    def get_update_category_name(self, update_category_id):
        """
        Returns an update category name for the update category id
        specified.

        :param update_category_id: Update category id
        """
        if not update_category_id in UPDATE_CATEGORY_MAP.keys():
            # This should never happen and if it happens this can be
            # classified as a bug.
            return "UNKNOWN"
        return UPDATE_CATEGORY_MAP[update_category_id]

    def get_changelog(self, pkg_info, changelog_handler):
        """
        Starts a changelog fetch thread and calls the given
        handler object accordingly.

        :param pkg_info: :class:`UpdateManager.Backend.PackageInfoBase`
          object
        :param changelog_handler:
          :class:`UpdateManager.DistSpecific.changelog.ChangelogHandler`
          object
        """
        self._changelog_fetcher(pkg_info, changelog_handler)

    def get_bug_script_name(self):
        """ Optionally returns the name of a bug script to use for bug
        reporting.
        """
        return None
