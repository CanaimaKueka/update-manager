# UpdateManager/DistSpecific/Debian/changelog.py
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
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#  USA.

""" Debian-specific functionality. """

import logging

LOG = logging.getLogger('UpdateManager.DistSpecific.Canaima.changelog')

from UpdateManager.DistSpecific.changelog import HTTPChangelogFetcher

class CanaimaChangelogFetcher(HTTPChangelogFetcher):
    """ Canaima-specific ChangelogFetcher implementation. """
    def _get_changelog_url(self, pkg_info):
        """ Debian-specific changelog URL generation. """

        candidate_version = pkg_info.get_candidate_version()
        srcpkg_name = pkg_info.get_source_package_name()
        if ':' in candidate_version:
            candidate_version = candidate_version[
                candidate_version.find(':')+1:]
        url = "http://packages.debian.org/changelogs/pool/"
        candidate_uri = pkg_info.get_candidate_uri().split('/pool/', 1)[1]
        candidate_uri = candidate_uri[:candidate_uri.rfind('/')]
        url += '%s/%s_%s/changelog.txt' % (candidate_uri, srcpkg_name,
                                           candidate_version)
        LOG.debug("Downloading changelog for %s from %s.", srcpkg_name,
                  url)
        return url
