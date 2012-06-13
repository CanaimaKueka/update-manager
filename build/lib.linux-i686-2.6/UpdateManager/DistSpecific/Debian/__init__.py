# UpdateManager/DistSpecific/Debian/__init__.py
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

""" Debian-specific functionality. """

import logging

from UpdateManager.DistSpecific import DistBase, UPDATE_CATEGORY
from UpdateManager.DistSpecific.Debian.changelog import DebianChangelogFetcher

LOG = logging.getLogger('UpdateManager.Backend.Debian')

class DebianDist(DistBase):
    """ Implementation of distribution-specific functionality for
    Debian.
    """
    def __init__(self):
        DistBase.__init__(self, name="Debian GNU/Linux",
                          changelog_fetcher=DebianChangelogFetcher,
                          distupgrade_check=False)

    def get_update_category(self, pkg_info):
        """ Returns the update category for a given package """
        # We detect the update category using the
        # origin's label, archive name and whether its
        # trusted or not.
        label = pkg_info.get_candidate_origin_label()
        origin = pkg_info.get_candidate_origin_name()
        trusted = pkg_info.candidate_origin_is_trusted()

        # Untrusted updates are most likely unofficial ones, so
        # we only need to check whether the source is trusted first.
        if not trusted:
            return UPDATE_CATEGORY.THIRDPARTY

        if label == "Debian-Security" and origin == "Debian":
            return UPDATE_CATEGORY.SECURITY

        if label == "Backports.org archive" and \
           origin == "Backports.org archive":
            return UPDATE_CATEGORY.BACKPORT

        # TODO: how to best detect backports?

        elif label == "Debian" and origin == "Debian":
            return UPDATE_CATEGORY.DEFAULT

        # All other sources are third-party
        LOG.debug('Could not identify update: origin=%s,label=%s,trusted=%s',
                  origin, label, trusted)
        return UPDATE_CATEGORY.THIRDPARTY

    def get_bug_script_name(self):
        return "debian_reportbug.sh"
