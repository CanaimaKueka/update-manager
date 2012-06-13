# UpdateManager/Frontend/PythonApt.py
#
#  Copyright (c) 2009 Canonical
#                2009, 2010 Stephan Peijnik
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

""" python-apt backend """

import logging
import os
import urllib2
import weakref

from gettext import gettext as _

import apt
import apt.progress.base
import apt_pkg

from UpdateManager.Backend import PackageInfoBase, PackageInfoStoreBase
from UpdateManager.Backend import BackendBase, DEP_RELATION
from UpdateManager.Backend import PackageDependencyBase
from UpdateManager.BugHandler import Thread
from UpdateManager.Util.enum import Enum

LOG = logging.getLogger('UpdateManager.Backend.PythonApt')

def _translate_relation(rel_string):
    """ Helper function that translates a given relation string
    to a relation constant (:class:`UpdateManager.Backend.DEP_RELATION`).
    """
    rel = None
    if rel_string == '=':
        rel = DEP_RELATION.EQ
    elif rel_string == '<=':
        rel = DEP_RELATION.LTE
    elif rel_string == '>=':
        rel = DEP_RELATION.GTE
    elif rel_string == '<' or rel_string == '<<':
        rel = DEP_RELATION.LT
    elif rel_string == '>' or rel_string == '>>':
        rel = DEP_RELATION.GT
    return rel

class PackageInfoStore(PackageInfoStoreBase):
    """
    Implementation of :class:`UpdateManager.Backend.PackageInfoStoreBase`.
    """
    def __init__(self, cache, *args, **kwargs):
        PackageInfoStoreBase.__init__(self, *args, **kwargs)
        self._cache = cache

class PackageDependency(PackageDependencyBase):
    """
    Implementation of :class:`UpdateManager.Backend.PackageDependencyBase`.
    """
    def __init__(self, cache, *args, **kwargs):
        PackageDependencyBase.__init__(self, *args, **kwargs)

        if self._name in cache:
            pkg = cache[self._name]
            if pkg.is_installed:
                inst_version = pkg.installed.version
                if self._version is not None and self._relation is not None:
                    self._inst_version_matches = self._cmp_helper(inst_version)
                else:
                    self._inst_version_matches = True

class PackageInfo(PackageInfoBase):
    """
    Implementation of :class:`UpdateManager.Backend.PackageInfoBase`.
    """
    def __init__(self, package_obj, app):
        PackageInfoBase.__init__(self)

        self._pyapt_package = package_obj
        self._app = app
        self._dependencies = []
        self._rdependencies = []
        self._sdependencies = []
        self._rsdependencies = []
        self._conflicts = []
        self._uninst_dependencies = []
        self._update_category = app.get_update_category(self)
        self._broken = False
        self._download_size = None

    def is_broken(self):
        """ Returns whether the package is broken or not """
        return self._broken

    def get_package_name(self):
        """ Returns the package name """
        return self._pyapt_package.name

    def get_installed_version(self):
        """ Returns the installed version """
        if self._pyapt_package.installed:
            return self._pyapt_package.installed.version
        return None

    def is_installed(self):
        """ Returns whether the package is installed or not """
        return not self._pyapt_package.installed is None

    def get_candidate_version(self):
        """ Returns the candidate version """
        if self._pyapt_package.candidate:
            return self._pyapt_package.candidate.version
        return None

    def get_download_size(self):
        """ Returns the download size in bytes """
        quoted_version = urllib2.quote(self._pyapt_package.candidate.version)
        filename = '%s_%s_%s.deb' \
                   % (self._pyapt_package.name,
                      quoted_version.lower(),
                      self._pyapt_package.candidate.architecture)

        archive_path = os.path.join('/var/cache/apt/archives/', filename)
        partial_path = os.path.join('/var/cache/apt/archives/partial/',
                                    filename)
        if os.path.exists(archive_path):
            # File has been fully fetched, return 0
            return 0
        elif os.path.exists(partial_path):
            # File has been partially fetched...
            try:
                stat_info = os.stat(partial_path)
                part_size = stat_info[os.path.stat.ST_SIZE]
                return self._pyapt_package.candidate.size - part_size
            except:
                pass
            
        return self._pyapt_package.candidate.size

    def get_update_category(self):
        """ Returns the update category """
        return self._update_category

    def get_summary(self):
        """ Returns the package summary (short description) """
        return self._pyapt_package.candidate.summary

    def _get_nonlocal_origin(self):
        """ Helper function that returns the first non-local origin """
        for origin in self._pyapt_package.candidate.origins:
            if origin.archive != 'now':
                return origin
        return None

    def get_candidate_archive_name(self):
        """ Returns the archive name """
        origin = self._get_nonlocal_origin()
        if not origin:
            return None
        return origin.archive

    def get_candidate_origin_label(self):
        """ Returns the origin label """
        origin = self._get_nonlocal_origin()
        if not origin:
            return None
        return origin.label

    def get_candidate_origin_name(self):
        """ Returns the origin name """
        origin = self._get_nonlocal_origin()
        if not origin:
            return None
        return origin.origin

    def get_candidate_component_name(self):
        """ Returns the component name """
        origin = self._get_nonlocal_origin()
        if not origin:
            return None
        return origin.component

    def candidate_origin_is_trusted(self):
        """ Returns true if the origin is trusted """
        origin = self._get_nonlocal_origin()
        if not origin:
            return False
        return origin.trusted

    def get_description(self):
        """ Returns the package description """
        return self._pyapt_package.candidate.description

    def get_source_package_name(self):
        """ Returns the source package name """
        return self._pyapt_package.candidate.source_name

    def get_candidate_uri(self):
        """ Returns the candidate uri """
        return self._pyapt_package.candidate.uri

    def get_dependencies(self):
        """ Returns the list of dependencies """
        return self._dependencies[:]

    def get_strict_dependencies(self):
        """ Returns the list of strict dependencies (packages with an exact
        version this candidate depends on).
        """
        return self._sdependencies[:]

    def get_uninstalled_dependencies(self):
        """ Returns a list of dependencies that are not installed. """
        return self._uninst_dependencies[:]

    def get_reverse_dependencies(self):
        """ Returns list of reverse dependencies (packages that depend on this
        package).
        """
        return self._rdependencies[:]

    def get_strict_reverse_dependencies(self):
        """ Returns list of strict reverse dependencies (packages that depend
        on the candidate version of this package).
        """
        return self._rsdependencies[:]

    def get_conflicts(self):
        """ Returns list of conflicting packages """
        return self._conflicts[:]

    def _resolve_dependencies(self, pkginfo_store):
        """ Resolves the package's dependencies """
        # Dependencies go first
        for dep_info in self._pyapt_package.candidate.dependencies:
            relations = []
            for dep in dep_info.or_dependencies:
                rel = _translate_relation(dep.relation)

                pkg_dep = PackageDependency(pkginfo_store._cache,
                                            dep.name, rel, dep.version)
                relations.append(pkg_dep)

            fulfilled_by_one = False
            # Multiple dependencies are handled as either-or ones, so
            # only one must be fulfilled.
            for pkg_dep in relations:
                # Check if the already installed version fulfills our
                # dependency
                if pkg_dep.fulfilled_by_installed_version():
                    fulfilled_by_one = True
                    # TODO: strict handling?
                    break
                
                # Check if there is a candidate for an upgrade
                # that fulfills our dependency
                elif pkg_dep.fulfilled_by_candidate_version(pkginfo_store):
                    candidate = pkginfo_store.get_package(pkg_dep._name)

                    if pkg_dep.is_strict():
                        self._sdependencies.append(candidate)
                        candidate._rsdependencies.append(weakref.proxy(self))
                    else:
                        self._dependencies.append(candidate)
                        candidate._rdependencies.append(weakref.proxy(self))
                    
                    fulfilled_by_one = True
                    break

            # As all dependencies (including uninstalled ones)
            # are in our store already any other case means the
            # package is broken.
            if not fulfilled_by_one:
                LOG.warning('%s is broken (%s unfulfilled)', self,
                            dep)
                self._broken = True

        # Next step: check conflicts
        # The method below is a workaround, accessing the record
        # directly, because python-apt does not include support for
        # accessing a package's conflicts record.
        pyapt_record = self._pyapt_package.candidate.record
        if 'Conflicts' in pyapt_record:
            conflicts = pyapt_record['Conflicts'].split(',')
            for co in conflicts:

                co = co.strip() # Remove leading & trailing whitespace
                
                # No version requirement
                if not '(' in co:
                    name = co
                    rel = None
                    version = None
                else:
                    beginpos = co.find('(') + 1
                    endpos = co.find(')')
                    name = co[:beginpos-1].strip()
                    info = co[beginpos:endpos].strip()
                    try:
                        rel_str, version = info.split(' ', 1)
                        rel = _translate_relation(rel_str)
                    except IndexError:
                        rel = None
                        version = info

                pkg_dep = PackageDependency(pkginfo_store._cache,
                                                name, rel, version)
                # Now we have our conflict in a PackageDependency object.
                # Reversing our dependency logic here should work just
                # fine.

                if name == self._pyapt_package.name:
                    LOG.debug('%s conflicts with itself (%s)',
                              name, pkg_dep)
                    continue
                
                if pkg_dep.fulfilled_by_candidate_version(pkginfo_store):
                    # Conflicts with a candidate
                    pkg_info = pkginfo_store.get_package(pkg_dep._name)
                    if not pkg_info in self._conflicts:
                        self._conflicts.append(pkg_info)
                else:
                    # Check if the package is installed at all.
                    if name in pkginfo_store._cache:
                        c_pkg = pkginfo_store._cache[name]

                        if c_pkg.is_installed:
                            inst_version = c_pkg.installed.version
                            if pkg_dep._cmp_helper(inst_version):
                                # The package is installed and matches
                                # the Conflict record: append to our
                                # conflicts list
                                pkg_info = PackageInfo(c_pkg, self._app)

                                # Check needed for multi-version conflicts
                                if not pkg_info in self._conflicts:
                                    self._conflicts.append(pkg_info)

# Cache progress helper class
class CacheProgressHelper(apt.progress.base.OpProgress):
    """ Cache open progress helper. """

    STEPS = 5
    
    def __init__(self, handler):
        self._handler = handler
        self._percent_done = 0
        self._steps_done = 0
        self._percent_last = 0
        self._last_op = None

        apt.progress.base.OpProgress.__init__(self)
        
    def update(self, percent=None):
        """ Handles an update of the cache opening progress.

        :param percent: Percentage done
        """
        if percent is None:
            percent = self.percent 
        if self.op != self._last_op:
            self._handler.cache_operation(self.op)
            self._last_op = self.op
            
        if self.major_change:
            self._steps_done += 1
            
        if percent != 0:
            percent_done = (float(self._steps_done)/self.STEPS)*100
            percent_done += int(float(percent)/self.STEPS)
            if percent_done < self._percent_last:
                percent_done = self._percent_last
            self._handler.cache_update(percent_done)
            self._percent_last = percent_done

FETCH_STATUS = Enum("DONE", "QUEUED", "FAILED", "HIT", "IGNORED")

class ListProgressHelper(apt.progress.base.AcquireProgress):
    def __init__(self, handler):
        self._handler = handler
        self._abort = False
        self._percent = 0
        self.eta = 0
        self._done_count = 0
        self._fail_count = 0

    def abort(self):
        """ Handles an abort notification from the UI """
        self._abort = True

    def pulse(self, owner):
        """ Handles a pulse from python-apt

        :param items: Current items
        """
        apt.progress.base.AcquireProgress.pulse(self, owner)

        self.percent = (((self.current_bytes + self.current_items) * 100.0) /
                        float(self.total_bytes + self.total_items))
        if self.current_cps > 0:
            self.eta = ((self.total_bytes - self.current_bytes) /
                        float(self.current_cps))
        
        if self.percent > self._percent:
            self._percent = self.percent

        if not self._abort:
            for worker in owner.workers:
                if not worker.current_item:
                    continue
                self._handler.list_item_update(worker.current_item.uri,
                                               worker.total_size,
                                               worker.current_size)
                self._handler.list_update(self.current_cps, self.eta,
                                          self._percent)
        else:
            self._handler.list_aborted()
        return not self._abort

    def fail(self, item):
        """Handle a failed item.

        :param item: An :class:`apt_pkg.AcquireItemDesc` object describing the
                     item.
        """
        self._fail_count += 1

    def ims_hit(self, item):
        """Handle an already up-to-data item.

        :param item: An :class:`apt_pkg.AcquireItemDesc` object describing the
                     item.
        """
        self._handler.list_item_finished(item.uri)
        self._done_count += 1


    def done(self, item):
        """Handle a completed item.

        :param item: An :class:`apt_pkg.AcquireItemDesc` object describing the
                     item.
        """
        self._handler.list_item_finished(item.uri)
        self._done_count += 1

    def fetch(self, item):
        """Handle the start of fetching an item.

        :param item: An :class:`apt_pkg.AcquireItemDesc` object describing the
                     item.
        """
        try:
            # Partial size requires python-apt (>= 0.7.93.4)
            self._handler.list_item_begin(item.uri, item.owner.filesize,
                                          item.owner.partialsize)
        except AttributeError:
            self._handler.list_item_begin(item.uri, item.owner.filesize, 0)



class DownloadProgressHelper(apt.progress.base.AcquireProgress):
    """ Download progress helper """
    def __init__(self, handler):
        self._handler = handler
        self._abort = False
        self.eta = 0
        self.currentCPS = 0
        self._percent = 0
        self.percent = 0.0
        self.eta = 0.0

    def abort(self):
        """ Handles an abort notification from the UI """
        self._abort = True

    def pulse(self, owner):
        """ Handles a pulse from python-apt

        :param items: Current items
        """
        apt.progress.base.AcquireProgress.pulse(self, owner)

        self.percent = (((self.current_bytes + self.current_items) * 100.0) /
                        float(self.total_bytes + self.total_items))
        if self.current_cps > 0:
            self.eta = ((self.total_bytes - self.current_bytes) /
                        float(self.current_cps))
        
        if self.percent > self._percent:
            self._percent = self.percent

        if not self._abort:
            for worker in owner.workers:
                if not worker.current_item:
                    continue
                self._handler.download_item_update(worker.current_item.uri,
                                                   worker.total_size,
                                                   worker.current_size)
                self._handler.download_update(self.current_cps, self.eta,
                                              self._percent)
        return not self._abort

    def fail(self, item):
        """Handle a failed item.

        :param item: An :class:`apt_pkg.AcquireItemDesc` object describing the
                     item.
        """
        self._handler.download_item_finished(item.uri)

    def done(self, item):
        """Handle a completed item.

        :param item: An :class:`apt_pkg.AcquireItemDesc` object describing the
                     item.
        """
        self._handler.download_item_finished(item.uri)
        

    def fetch(self, item):
        """Handle a completed item.

        :param item: An :class:`apt_pkg.AcquireItemDesc` object describing the
                     item.
        """
        self._handler.download_item_begin(item.uri, item.owner.filesize, 0)

    def stop(self):
        """
        Stop handler. Sends out notifications when downloading has stopped
        (but was not aborted).
        """
        if not self._abort:
            self._handler.download_finished()
            self._handler.install_begin()

class InstallProgressHelper(apt.progress.base.InstallProgress):
    """ Install progress helper """
    def __init__(self, commit_handler, fork_func):
        apt.progress.base.InstallProgress.__init__(self)
        self._fork_func = fork_func
        self._handler = commit_handler

    def error(self, pkg, errormsg):
        """ Error handling

        :param pkg: Package name
        :param errormsg: Error message
        """
        self._handler.install_failed(errormsg)

    def conffile(self, current, new):
        """ Config file question handling

        :param current: Current config file name
        :param new: New config file name
        """
        # TODO: conffile handling
        pass

    def status_change(self, pkg, percent, status):
        """ Status change handling

        :param pkg: Package name
        :param percent: Overall percentage done
        :param status: Status string
        """
        self._handler.install_update(pkg, int(percent), status)

    def fork(self):
        """ Fork handling.

        This method uses the internal _fork_func variable to fork.
        """
        return self._fork_func()

class PythonAptBackend(BackendBase):
    """ python-apt backend implementation. """
    
    def __init__(self, application):
        BackendBase.__init__(self, requires_root=True)
        self._cache = None
        self._available_updates = None
        self._fetch_operation = None
        self._operation_in_progress = False
        self._application = application
        path = os.environ["PATH"]
        parts = path.split(":")
        if not "/sbin" in parts:
            path += ":/sbin"
            LOG.debug("Added /sbin to PATH.")
        if not "/usr/sbin" in parts:
            path += ":/usr/sbin"
            LOG.debug("Added /sbin to PATH.")
        os.environ["PATH"] = path

    def acquire_lock(self):
        """ Tries to acquire package manager lock.

        :returns: True of lock has been acquired, False otherwise.
        
        """
        if not self._application.uses_privileged_functions():
            return True
        
        # No need to try locking, we already hold the lock.
        try:
            apt_pkg.pkgsystem_lock()
            LOG.debug('Package system lock acquired.')
            return True
        except SystemError, e:
            LOG.debug('Package system lock not acquired: %s', e)

        return False

    def release_lock(self):
        """
        Releases package manager lock.

        :returns: True if lock has been released, False otherwise.
        """
        if not self._application.uses_privileged_functions():
            return True
        try:
            apt_pkg.pkgsystem_unlock()
            LOG.debug('Package system lock released.')
            return True
        except SystemError, e:
            LOG.debug('Package system lock not released: %s', e)
        
        return False

    def is_locked(self, by_us=False):
        """
        Checks if the package manager lock is held.

        :param by_us: Defines whether to check if anyone holds the lock
          or if we hold the lock ourselves (default: False).
        :returns: Boolean indicating whether the lock is being held.
        """
        if by_us:
            if self.release_lock():
                self.acquire_lock()
                return True
            return False
        else:
            if self.acquire_lock():
                self.release_lock()
                return True
            return False

    def reload_cache(self, cache_progress_handler):
        """
        Reloads the package cache.
        """
        if self._operation_in_progress:
            return False
        
        self._operation_in_progress = True
        progress_helper = CacheProgressHelper(cache_progress_handler)

        def thread_helper():
            if not self.is_locked(by_us=True):
                self.acquire_lock()

            self._available_updates = None
            cache_progress_handler.cache_begin()
            if not self._cache:
                # Cache has not been opened before. 
                self._cache = apt.Cache(progress_helper)
            else:
                # Reloading the cache.
                self._cache.open(progress_helper)

            self._operation_in_progress = False
            cache_progress_handler.cache_finished()
                
        Thread(target = thread_helper, name = "PythonAptCache").start()
        return True

    def download_package_lists(self, list_progress_handler):
        """
        Reloads the package list(s).
        """
        if self._operation_in_progress:
            return False
        
        progress_helper = ListProgressHelper(list_progress_handler)
        self._operation_in_progress = True
        self._fetch_operation = progress_helper

        def thread_helper():
            if self.is_locked(by_us=True):
                self.release_lock()
                
            list_progress_handler.list_begin()
            try:
                self._cache.update(progress_helper)
                self.acquire_lock()
                LOG.debug('Fail count: %d, done count: %d',
                          progress_helper._fail_count,
                          progress_helper._done_count)
                if progress_helper._done_count > 0 \
                       or progress_helper._fail_count == 0:
                    list_progress_handler.list_finished()
                else:
                    list_progress_handler.list_failed(
                        _("Could not download packages information."))
            except apt.cache.LockFailedException, lock_err:
                list_progress_handler.list_failed(
                    "Locking failed: %s" % str(lock_err))
            except apt.cache.FetchFailedException, fetch_err:
                list_progress_handler.list_failed(
                    "Fetch failed: %s" % str(fetch_err))
            except apt.cache.FetchCancelledException:
                pass
            except SystemError, sys_err:
                LOG.error("System error: %s", sys_err)

            self._operation_in_progress = False
            self._fetch_operation = None
            
        Thread(target = thread_helper, name = "PythonAptList").start()
        return True

    def get_available_updates(self, dist_upgrade=True):
        """
        Returns a list containing
        :class:`UpdateManager.Backend.PackageInfoBase` objects of available
        updates.
        
        :param dist_upgrade: Defines whether to do a dist upgrade or not.

        .. versionchanged: 0.200.0~exp1
          Added the `dist_upgrade` parameter.
        """
        if self._operation_in_progress:
            return PackageInfoStore(self._cache)
        elif not self._cache:
            return PackageInfoStore(self._cache)

        # We need to reset the cache first.
        self._cache.clear()
        self._available_updates = PackageInfoStore(self._cache)
        self._cache.upgrade(dist_upgrade=dist_upgrade)
        for pkg in self._cache.get_changes():
            if pkg.marked_upgrade or pkg.marked_install or pkg.marked_downgrade:
                pkg_info = PackageInfo(pkg, self._app)
                self._available_updates.add_package(pkg_info)
            elif pkg.marked_delete:
                pkg_info = PackageInfo(pkg, self._app)
                self._available_updates.add_removal(pkg_info)
            elif pkg.marked_reinstall:
                LOG.debug('Package %s marked as "reinstall": TODO', pkg)
            
        self._available_updates.resolve_dependencies()
        if not self.is_locked():
            self.acquire_lock()
            
        return self._available_updates

    def abort_operation(self):
        """ Aborts a fetch operation. """
        if self._fetch_operation:
            self._fetch_operation.abort()
            return True
        return False

    def commit(self, selected_updates, commit_progress_handler,
               fork_func=os.fork):
        """ Downloads and installs the updates selected.

        :param selected_updates: List of :class:`PackageInfo` objects
        :param commit_progress_handler:
          :class:`UpdateManager.Backend.CommitHandlerBase` object
        :param fork_func: Function used for forking. Defaults to os.fork.
        """
        if self._operation_in_progress:
            return False
        self._operation_in_progress = True

        def thread_helper():
            commit_progress_handler.preparation_begin()
            # The actiongroup should speed up the operations below...
            ag = apt_pkg.ActionGroup(self._cache._depcache)
            
            for pkg_info in self._available_updates.get_package_list():
                found = False
                
                for spkg in selected_updates:
                    if spkg.get_package_name() == pkg_info.get_package_name():
                        found = True
                        break

                if not found and not pkg_info._pyapt_package.marked_keep:
                    pkg_info._pyapt_package.mark_keep()
                else:
                    pkg_info._pyapt_package.mark_install(auto_fix=False,
                                                        auto_inst=False)
            ag.release()
            del ag

            if self._cache._depcache.broken_count > 0:
                # This should never happen, but we still handle it.
                # If there are broken packages the operations below will
                # not finish successfully.
                LOG.fatal('BrokenCount > 0 (%d)!',
                              self._cache._depcache.broken_count)
                LOG.debug('Trying to fix broken upgrades...')
                changes_old = self._cache.get_changes()
                try:
                    self._cache._depcache.fix_broken()
                    if self._cache._depcache.broken_count > 0:
                        LOG.debug('Packages still broken after fix attempt.')
                        self._operation_in_progress = False
                        return
                    changes_new = self._cache.get_changes()
                    new_packages = []
                    for new_pkg in changes_new:
                        if not new_pkg in changes_old:
                            pkg_info = PackageInfo(new_pkg, self._application)
                            LOG.debug('New change on %s.', pkg_info)
                            new_packages.append(pkg_info)
                except SystemError, s_err:
                    # TODO: Should we really call download_failed here?
                    commit_progress_handler.download_failed(s_err.message)
                    self._operation_in_progress = False
                    return

            size = 0
            download_count = 0
            selected_count = 0
            removals = []
            installs = []
            for pkg in self._cache.get_changes():
                if pkg.marked_install or pkg.marked_upgrade:
                    selected_count += 1
                    pkg_info = PackageInfo(pkg, self._application)
                    pkg_size = pkg_info.get_download_size()
                    if pkg_size > 0:
                        size += pkg_size
                        download_count += 1

                    if not pkg.is_installed:
                        installs.append(PackageInfo(pkg, self._application))
                if pkg.marked_delete:
                    removals.append(PackageInfo(pkg, self._application))

            if len(removals) or len(installs):
                res = commit_progress_handler.requires_removal_or_installation(
                    removals, installs)
                if type(res) != bool:
                    LOG.debug('requires_removal_or_installation did not '+\
                              ' return bool value (%s)!', res)
                    commit_progress_handler.download_failed(
                        _("Internal error: the commit progress handler did not handle requires_removal_or_installation correctly."))
                    self._operation_in_progress = False
                    return
                elif res is False:
                    commit_progress_handler.download_aborted()
                    self._operation_in_progress = False
                    return
            
            commit_progress_handler.download_begin(size, selected_count,
                                                   download_count)
            
            download_helper = DownloadProgressHelper(commit_progress_handler)
            self._fetch_operation = download_helper
            install_helper = InstallProgressHelper(commit_progress_handler,
                                                   fork_func)
            if self.is_locked(by_us=True):
                self.release_lock()
            try:
                self._cache.commit(fetch_progress=download_helper,
                                   install_progress=install_helper)
            except apt.cache.FetchCancelledException:
                pass
            except apt.cache.FetchFailedException, ex:
                commit_progress_handler.download_failed(ex.message)
            except SystemError, ex:
                commit_progress_handler.download_failed(ex.message)
                
            self.acquire_lock()
            if not download_helper._abort:
                commit_progress_handler.install_finished()
            else:
                commit_progress_handler.download_aborted()
            self._fetch_operation = None
            self._operation_in_progress = False

        Thread(target = thread_helper, name = "PythonAptCommit").start()
        return True
        
