# UpdateManager/DistSpecific/changelog.py
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

""" Changelog fetcher functionality """

import logging
import urllib2

from threading import Thread

from UpdateManager.Util.enum import Enum

LOG = logging.getLogger('UpdateManager.DistSpecific.changelog')

CHANGELOG_FETCH_STATUS = Enum(
    FAILED = "Fetching failed",
    DONE = "Fetching finished")
""" Changelog fetcher status """

class ChangelogFetcherException(Exception):
    """ Changelog fetcher exception """
    pass

class ChangelogHandler(object):
    """ Changelog result handler """
    def changelog_finished(self, pkg_info, raw_changelog):
        """ Changelog fetching finished notification

        :param pkg_info: :class:`UpdateManager.Backend.PackageInfoBase` object
        :param raw_changelog: The last changelog entry as a string
        """
        raise NotImplementedError

    def changelog_failure(self, pkg_info, error_message):
        """ Changelog fetching failure notification

        :param pkg_info: :class:`UpdateManager.Backend.PackageInfoBase` object
        :param error_message: Error message
        """
        raise NotImplementedError

class ChangelogFetcher(object):
    """ Changelog Fetcher base class.

    This class must be subclassed by all ChangelogFetcher implementations.
    """
    def __init__(self, pkg_info, changelog_handler):
        self._pkg_info = pkg_info
        self._handler = changelog_handler

        LOG.debug("Fetching changelog entry for %s.",
                  pkg_info.get_package_name())
        name = "changelogfetcher-%s" % (pkg_info.get_package_name())
        Thread(target = self._do_fetch, name = name).start()

    def _do_fetch(self):
        """ The actual worker method.

        This method must be overridden.
        """
        raise NotImplementedError
    
class HTTPChangelogFetcher(ChangelogFetcher):
    """ Simple HTTP Changelog Fetcher """

    def _do_fetch(self):
        """ HTTP worker implementation """
        LOG.debug("Getting changelog URL for package %r", self._pkg_info)
        url = self._get_changelog_url(self._pkg_info)
        found_double_dash = False
        try:
            LOG.debug("Fetching %s...", url)
            connection = urllib2.urlopen(url)
            text = ""
            
            while not found_double_dash:
                line = connection.readline()
                if line.startswith(' -- '):
                    LOG.debug("Found double-dash sequence, closing stream.")
                    found_double_dash = True
                text += line
                
            connection.close()
            
            self._handler.changelog_finished(self._pkg_info, text)
        except urllib2.URLError, exc:
            LOG.error('Fetching the changelog entry via HTTP failed: %s',
                      exc)
            self._handler.changelog_failure(self._pkg_info, exc.message)

    def _get_changelog_url(self, pkg_info):
        """ Gets the (distribution-specific) changelog URL.

        :param pkg_info: :class:`UpdateManager.Backend.PackageInfoBase`
          object.

        This method must be overridden.
        """
        raise NotImplementedError
