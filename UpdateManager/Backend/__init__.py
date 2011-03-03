# UpdateManager/Backend/__init__.py
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

""" Base classes for backend implementations and helpers."""

import logging
from gettext import gettext as _
import os
import weakref

import apt
import apt_pkg

from UpdateManager.Util.enum import NegativeEnum, Enum

LOG = logging.getLogger('UpdateManager.Backend')

class PackageInfoStoreBase(object):
    """ PackageInfo Store

    Object to store :class:`PackageInfoBase` objects.
    """
    def __init__(self, *args, **kwargs):
        self._categories = {}
        self._packages = {}
        self._removals = []

    def add_package(self, pkg_info):
        """
        Adds a package to the store.

        :param pkg_info: :class:`PackageInfoBase` object
        """
        pkg_name = pkg_info.get_package_name()

        # We store weak references in _packages and hard references
        # in _categories.
        self._packages[pkg_name] = weakref.proxy(pkg_info)
        cat_id = pkg_info.get_update_category()
        if not self._categories.has_key(cat_id):
            self._categories[cat_id] = {pkg_name: pkg_info}
        else:
            self._categories[cat_id][pkg_name] = pkg_info

    def add_removal(self, pkg_info):
        """
        Adds a package removal to the store.

        :param pkg_info: :class:`PackageInfoBase` object

        .. versionadded:: 0.200.0~exp1
        """
        self._removals.append(pkg_info)

    def get_removals(self):
        """ Gets the packages marked for removal.

        :returns: list of :class:`PackageInfoBase` objects

        .. versionadded:: 0.200.0~exp1
        """
        return self._removals[:]

    def get_removal_count(self):
        """ Returns the number of packages marked for removal.

        :returns: list of :class:`PackageInfoBase` objects

        .. versionadded:: 0.200.0~exp1
        """
        return len(self._removals)

    def get_install_count(self):
        """ Returns the number of packages to be newly installed.

        :returns: list of :class:`PackageInfoBase` objects

        .. versionadded:: 0.200.0~exp1
        """
        count = 0
        for pkg in self._packages:
            pkg_info = self._packages[pkg]
            if not pkg_info.is_installed():
                count += 1
        return count
    
    def get_package(self, package_name):
        """ Gets a package from the internal dictionary.

        :returns: :class:`PackageInfoBase` object
        """
        if not self.has_package(package_name):
            return None
        return self._packages[package_name]

    def has_package(self, package_name):
        """ Checks if a given package exists in the store.

        :param package_name: The package's name.
        """
        return self._packages.has_key(package_name)

    def package_count(self):
        """ Gets number of packages in the store.

        :returns: Number of packages
        """
        return len(self._packages.keys())

    def get_packages(self):
        """ Gets a dict of packages.

        :returns: A dict with category IDs as keys, containing a dict
          with package names as keys and :class:`PackageInfoBase` objects
          as values.
        """
        return self._categories.copy()

    def get_package_list(self):
        """ Gets a list of packages.

        :returns: A list of :class:`PackageInfoBase` objects.
        """
        return self._packages.values()

    def resolve_dependencies(self):
        """ Resolves dependencies of all packages. """
        for pkg_info in self._packages.values():
            pkg_info._resolve_dependencies(self)

DEP_RELATION = Enum('EQ', 'LT', 'GT', 'GTE', 'LTE')

class PackageDependencyBase(object):
    """ Package dependency representation """
    def __init__(self, name, relation, version):
        self._name = name
        self._relation = relation
        self._version = version
        if not relation or not version:
            self._inst_version_matches = True
        else:
            self._inst_version_matches = False

    def is_strict(self):
        """ Returns whether the dependency is a strict one.

        Strict dependencies depend on exactly one version of another
        package.
        """
        return self._relation is DEP_RELATION.EQ

    def fulfilled_by_installed_version(self):
        """ Check if the currently installed version of the package
        fulfills the dependency.

        :returns: True if dependency is fulfilled, False otherwise
        """
        return self._inst_version_matches

    def fulfilled_by_candidate_version(self, pkg_info_store):
        """ Check if the candidate version of the package
        fulfills the dependency.

        :param pkg_info_store: :class:`PackageInfoStoreBase` object
        :returns: True if dependency is fulfilled, False otherwise
        """
        pkg = pkg_info_store.get_package(self._name)
        if not pkg:
            return False
        return self._cmp_helper(pkg.get_candidate_version())

    def _cmp_helper(self, other_version):
        """ Compare helper method.

        Compares a given package version string with the dependency.

        :param other_version: Version to compare, as a string.
        :returns: True if version matches, False otherwise
        """
        if not self._version:
            # No version information means we just depend on the package being
            # installed.
            return True
        cmp_res = apt_pkg.version_compare(other_version, self._version)

        if cmp_res == 0 and self._relation in [DEP_RELATION.EQ,
                                               DEP_RELATION.GTE,
                                               DEP_RELATION.LTE]:
            return True
        elif cmp_res < 0 and self._relation in [DEP_RELATION.LT,
                                                DEP_RELATION.LTE]:
            return True
        elif cmp_res > 0 and self._relation in [DEP_RELATION.GT,
                                                DEP_RELATION.GTE]:
            return True
        return False

    def __repr__(self):
        return '<PackageDependency: %s (%s %s)' % (self._name, self._relation,
                                                   self._version)
        
class PackageInfoBase(object):
    """
    Package info base class.

    All PackageInfo implementations *must* subclass this
    class and override *all* its methods.
    """
    def is_broken(self):
        """ Returns whether the package is broken or not """
        return self._broken
    
    def get_package_name(self):
        """ Return the package name as a string. """
        raise NotImplementedError

    def get_installed_version(self):
        """ The currently installed version as a string. """
        raise NotImplementedError

    def get_candidate_version(self):
        """ The candidate's version as a string. """
        raise NotImplementedError

    def get_update_category(self):
        """ The update's category as an integer. """
        raise NotImplementedError

    def get_download_size(self):
        """ The download size in bytes as an integer. """
        raise NotImplementedError

    def get_summary(self):
        """
        The package summary (aka. short description) as a string.
        """
        raise NotImplementedError

    def get_candidate_archive_name(self):
        """ The candidate's repository archive name. """
        raise NotImplementedError

    def get_candidate_origin_label(self):
        """ The candidate's repository origin label. """
        raise NotImplementedError

    def get_candidate_origin_name(self):
        """ The candidate's repository origin name. """
        raise NotImplementedError

    def get_candidate_component_name(self):
        """ The candidate's repository component name. """
        raise NotImplementedError

    def candidate_origin_is_trusted(self):
        """
        Return boolean indicating whether the repository we found the candidate
        in is trusted.
        """
        raise NotImplementedError

    def get_description(self):
        """
        Return the package description.
        """
        raise NotImplementedError

    def get_source_package_name(self):
        """
        Return the package's source package name.
        """
        raise NotImplementedError

    def get_candidate_uri(self):
        """
        Return the candidate uri.
        """
        raise NotImplementedError

    def _resolve_dependencies(self, pkginfo_store):
        """ Resolves the package's dependencies and adds all upgradable
        dependencies to the store.
        """
        raise NotImplementedError

    def is_installed(self):
        """ Returns whether the package is already installed or not. """
        raise NotImplementedError

    def get_dependencies(self):
        """ Returns the package's upgradable dependencies as
        a list of :class:`PackageInfoBase` objects.
        """
        raise NotImplementedError

    def get_strict_dependencies(self):
        """ Returns the package's upgradable strict dependencies as
        a list of :class:`PackageInfoBase` objects.
        """
        raise NotImplementedError

    def get_reverse_dependencies(self):
        """ Returns the packages that depend on this package as a list of
        :class:`PackageInfoBase` objects.
        """
        raise NotImplementedError

    def get_strict_reverse_dependencies(self):
        """ Returns the packages that depend strictly on this package
        as a list of :class:`PackageInfoBase` objects.
        """
        raise NotImplementedError

    def get_uninstalled_dependencies(self):
        """ Returns a list of dependencies that are not installed. """
        raise NotImplementedError

    def get_conflicts(self):
        """ Returns a list of conflicting packages. """
        raise NotImplementedError

    def __repr__(self):
        return '<PackageInfo: %s>' % self.get_package_name()

class CacheProgressHandler(object):
    """ Cache (re-)opening progress handler """
    def cache_begin(self):
        """ Begin notification """
        raise NotImplementedError
    
    def cache_update(self, progress):
        """ Handle a progress update

        :param progress: Either one of :data:`CACHE_PROGRESS` (negative)
          or a percentage.
        """
        raise NotImplementedError

    def cache_operation(self, operation):
        """ Handle an operation update (current operation changed)

        :param operation: Current operation
        """
        raise NotImplementedError

    def cache_finished(self):
        """ Finished notification """
        raise NotImplementedError


    def cache_failed(self, failure_message):
        """ Failure notification

        :param failure_message: Failure message
        """
        raise NotImplementedError

class ListProgressHandler(object):
    """ Package list downloading handler """
    def list_item_begin(self, uri, item_size, downloaded_size):
        """ Item download has started

        :param uri: Item uri
        :param item_size: Item size in bytes
        :param downloaded_size: Number of bytes already downloaded
        """
        raise NotImplementedError

    def list_item_finished(self, item_uri):
        """ Item download has finished

        :param item_uri: Item uri
        """
        raise NotImplementedError

    def list_item_update(self, item_uri, file_size, downloaded_size):
        """ Item download progress update

        :param item_uri: Item uri
        :param file_size: File size in bytes
        :param downloaded_size: Number of bytes already downloaded
        """
        raise NotImplementedError

    def list_begin(self):
        """ List download operation has started """
        raise NotImplementedError

    def list_finished(self):
        """ List download operation has finished """
        raise NotImplementedError

    def list_update(self, download_speed, eta_seconds, percent_done):
        """ List download operation progress update

        :param download_speed: Current download speed in bytes per second
        :param eta_seconds: ETA for all operations to finish in seconds
        :param percent_done: Percentage done
        """
        raise NotImplementedError

    def list_aborted(self):
        """ List download operation was aborted """
        raise NotImplementedError

    def list_failed(self, failure_message):
        """ List download operation has failed

        :param failure_message: Failure message
        """
        raise NotImplementedError

class CommitProgressHandler(object):
    """ Commit progress handler """
    def preparation_begin(self):
        """ Commit preparation begins
        
        .. versionadded:: 0.200.0~exp1
        """
        raise NotImplementedError

    def requires_removal_or_installation(self, removals, installs):
        """ Commit operation requires removal or installation of packages.

        :param removals: list of :class:`PackageInfoBase` objects marked for
          removal
        :param installs: list of :class:`PackageInfoBase` objects marked for
          installation
        :returns: True if the operation should continue or False to abort.

        .. versionadded:: 0.200.0~exp1
        """
        raise NotImplementedError
    
    def download_item_begin(self, uri, item_size, downloaded_size):
        """ Item download has started

        :param uri: Item uri
        :param item_size: Item size
        :param downloaded_size: Number of bytes already downloaded
        """
        raise NotImplementedError

    def download_item_finished(self, uri):
        """ Item download has finished

        :param uri: Item uri
        """
        raise NotImplementedError

    def download_item_update(self, uri, item_size, downloaded_size):
        """ Item download update notification

        :param uri: Item uri
        :param item_size: File size in bytes
        :param downloaded_size: Number of bytes already downloaded.
        """
        raise NotImplementedError
    
    def download_begin(self, download_size, package_count, download_count):
        """ Download operation has started

        :param download_size: Overall number of bytes to be downloaded
        :param package_count: Number of packages to be upgraded
        :param download_count: Number of packages to be downloaded
        """
        raise NotImplementedError

    def download_update(self, download_speed, eta_seconds, percent):
        """ Download operation update

        :param download_speed: Current download speed in bytes per second
        :param eta_seconds: ETA for all operations to finish in seconds
        :param percent_done: Percentage done
        """
        raise NotImplementedError

    def download_finished(self):
        """ Download operation has finished """
        raise NotImplementedError

    def download_aborted(self):
        """ Download operation was aborted """
        raise NotImplementedError

    def download_failed(self, failure_message):
        """ Download operation has failed

        :param failure_message: Failure message
        """
        raise NotImplementedError

    def install_begin(self):
        """ Install operation has started """
        
        raise NotImplementedError

    def install_update(self, package, percent, status_message):
        """ Install operation update

        :param package: Package that is currently being processed
        :param percent: Overall percentage done
        :param status_message: Current status message
        """
        raise NotImplementedError

    def install_finished(self):
        """ Install operation has finished """
        raise NotImplementedError

    def install_failed(self, error_message):
        """ Install operation has failed

        :param error_message: Error message
        """
        raise NotImplementedError

class BackendProgressHandler(CacheProgressHandler, ListProgressHandler,
                             CommitProgressHandler):
    """ Combination of :class:`CacheProgressHandler`,
    :class:`ListProgressHandler` and :class:`CommitProgressHandler` for
    frontends implementing all of these in a single class.
    """
    pass

class BackendBase(object):
    """
    Base class for update-manager backends.

    This class forms the public interface to Update Manager backends.
    All Backend implementations *must* subclass this class and implement
    *all* of its methods.

    .. note:: The backend itself must ensure that two mutually exclusive
      operations are not happening at the same time.
    """
    def __init__(self, requires_root=True):
        self._requires_root = requires_root
    
    def init_backend(self, application):
        """
        Early initialization code. This method must not be overridden, unless
        some early backend initialization has to be done.

        :param application: :class:`UpdateManager.Application.Application`
          object.
        """
        self._app = application
    
    def get_available_updates(self, dist_upgrade=False):
        """
        Gets available updates (synchronous).

        :param dist_upgrade: Defines whether to do a dist upgrade or not.

        :returns: :class:`PackageInfoStoreBase` object

        .. versionchanged:: 0.200.0~exp1
          Added `dist_upgrade` parameter.
        """
        raise NotImplementedError

    def reload_cache(self, cache_progress_handler):
        """
        Reloads the package cache (asynchronous).

        :param cache_progress_handler: :class:`CacheProgressHandler`
          implementation
        """
        raise NotImplementedError

    def download_package_lists(self, list_progress_handler):
        """
        Downloads the package lists (asynchronous).

        :param download_progress_handler: :class:`ListProgressHandler`
          implementation
        """
        raise NotImplementedError

    def commit(self, selected_updates, commit_progress_handler,
               fork_func=os.fork):
        """
        Downloads and installs the packages specified in selcted_updates
        (asynchronous).

        :param selected_updates: List of :class:`UpdateManager.Backend.PackageInfoBase` objects
        :param commit_progress_handler: :class:`CommitProgressHandler`
          implementation
        :param fork_func: Function used for forking. Defaults to os.fork.
        """
        raise NotImplementedError

    def abort_operation(self):
        """ Aborts the current fetch operation. """
        raise NotImplementedError
        
    def acquire_lock(self):
        """ Acquire the package manager lock. """
        raise NotImplementedError

    def release_lock(self):
        """ Release the package manager lock. """
        raise NotImplementedError

    def is_locked(self, by_us=False):
        """
        Indicates whether the package manager lock has been acquired.

        :param by_us: Defines whether to check if we hold the lock ourselves
                      or for checking whether the lock is held by another
                      process.
        
        """
        raise NotImplementedError

    def requires_root(self):
        """ Specifies whether the backend requires root privileges to
        operate or not.

        :returns: True if root privileges are required, False otherwise.
        """
        return self._requires_root
