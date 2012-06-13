# UpdateManager/DistributionSpecific/Ubuntu/__init__.py
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

""" Ubuntu-specific functionality. """

from UpdateManager.DistSpecific import DistBase, UPDATE_CATEGORY
from UpdateManager.DistSpecific.Ubuntu.changelog import UbuntuChangelogFetcher

class UbuntuDist(DistBase):
    """
    Implementation of distribution-specific functionality for
    Ubuntu.
    """
    def __init__(self):
        DistBase.__init__(self, name="Ubuntu",
                          changelog_fetcher=UbuntuChangelogFetcher,
                          distupgrade_check=False)

    @classmethod
    def fetch_dist_info(cls):
        """ Doesn't do anything for now """
        # TODO: implement metarelease functionality
        return None

    def get_update_category(self, pkg_info):
        """ Returns the update category """
        # We detect the update category using the
        # origin's label, archive name and whether its
        # trusted or not.
        label = pkg_info.get_candidate_origin_label()
        archive = pkg_info.get_candidate_archive_name()
        origin = pkg_info.get_candidate_origin_name()
        trusted = pkg_info.candidate_origin_is_trusted()
        
        # Untrusted updates are most likely unofficial ones, so
        # we only need to check whether the source is trusted first.
        if not trusted or label != 'Ubuntu' or origin != 'Ubuntu':
            return UPDATE_CATEGORY.THIRDPARTY

        if archive.endswith('-security'):
            return UPDATE_CATEGORY.SECURITY
        elif archive.endswith('-updates'):
            return UPDATE_CATEGORY.RECOMMENDED
        elif archive.endswith('-proposed'):
            return UPDATE_CATEGORY.PROPOSED
        elif archive.endswith('-backports'):
            return UPDATE_CATEGORY.BACKPORT

        return UPDATE_CATEGORY.DEFAULT
