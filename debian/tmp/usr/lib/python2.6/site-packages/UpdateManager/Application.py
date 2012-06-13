# UpdateManager/Application.py
#
#  Copyright (c) 2004-2009 Canonical
#                2004 Michiel Sikkes
#                2005 Martin Willemoes Hansen
#                2009 Stephan Peijnik
#
#  Author: Michiel Sikkes <michiel@eyesopened.nl>
#          Michael Vogt <mvo@debian.org>
#          Martin Willemoes Hansen <mwh@sysrq.dk>
#          Stephan Peijnik <debian@sp.or.at>          
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

""" Application class and helpers """

import gettext
import logging
import os
import sys

_ = gettext.gettext

from UpdateManager.Util.log import init_logging, LOGLEVEL_NAME_MAP

# Logging must be initialized as early as possible.
init_logging()


from UpdateManager import __version__
from UpdateManager.Backend import BackendBase
from UpdateManager.Backend.PythonApt import PythonAptBackend
from UpdateManager.Backend.loader import BackendLoader
from UpdateManager.BugHandler import BugHandler
from UpdateManager.Config import UpdateManagerConfig
from UpdateManager.Exceptions import ExitProgramException
from UpdateManager.Exceptions import LoadingFailedException
from UpdateManager.Exceptions import InvalidBaseClass
from UpdateManager.Frontend import FrontendBase
from UpdateManager.Frontend.loader import FrontendLoader
from UpdateManager.DistSpecific import DistBase
from UpdateManager.DistSpecific.loader import DistLoader
from UpdateManager.DistSpecific.Auto import AutoDist
from UpdateManager.Util.loader import LoaderException
from UpdateManager.Util.loader import InvalidImplementationName
from UpdateManager.Util.opts import OptParser, make_option

LOG = logging.getLogger('UpdateManager.Application')

DEFAULT_BACKEND = 'PythonApt'
""" Default backend module name """

DEFAULT_DIST_SPECIFIC = 'Auto'
""" Default distribution specific module name """

class Application(object):
    """
    update-manager application.
    """
    
    def __init__(self, app_name, locale_dir, frontend,
                 backend=DEFAULT_BACKEND, dist_specific=DEFAULT_DIST_SPECIFIC,
                 app_args=sys.argv[1:]):
        """
        Initializes update-manager.
        
        :param app_name: Application name (for gettext) as str.
        :param locale_dir: locale directory (for gettext) as str.
        :param frontend: Frontend implementation name
        :param backend: Backend implementation name
        :param dist_specific: DistSpecific implementation name
        :param app_args: Application arguments (defaults to sys.argv[1:]).

        :raises: :exc:`ExitProgramException` if the program should exit
          with a given status code.
        :raises: :exc:`InvalidBaseClass` if an invalid base class was
          passed to the constructor.
        """
        assert(app_name is not None)
        assert(locale_dir is not None)
        assert(frontend is not None)
        assert(backend is not None)
        assert(dist_specific is not None)
        assert(type(frontend) is str or \
               (callable(frontend) and type(frontend) is type and \
                issubclass(frontend, FrontendBase)))
        assert(type(backend) is str or \
               (callable(backend) and type(backend) is type and \
                issubclass(backend, BackendBase)))
        assert(type(dist_specific) is str or \
               (callable(dist_specific) and type(dist_specific) is type \
                and issubclass(dist_specific, DistBase)))
        
        self._app_name = app_name
        self._locale_dir = locale_dir
        self._app_args = app_args
        self._config = UpdateManagerConfig()

        gettext.bindtextdomain(app_name, locale_dir)
        gettext.textdomain(app_name)
        
        # We need to initialize the BugHandler as early as possile.
        BugHandler.initialize(self)
                

        # We need to load all modules before building the option list
        self._load_frontend(frontend)
        self._load_backend(backend)
        self._load_dist_specific(dist_specific)
                                                          
        option_list = [
            make_option("-l", "--log-level",
                        dest = "loglevel", default="fatal", type="choice",
                        choices=LOGLEVEL_NAME_MAP.keys(),
                        help = _("sets the log level")),
            make_option("-d", "--debug",
                        dest = "loglevel", action="store_const", const="debug",
                        help = _("sets the log level to debug")),
            make_option("-c", "--check",
                        action="store_true", dest="run_check",
                        default=False,
                        help = _("starts an update check"))
            ]

        option_parser = OptParser(option_list = option_list, prog = app_name)
        self._options = None
        self._handle_options(option_parser)
        
        # Frontend gettext initialization
        self._frontend.init_gettext(app_name, locale_dir)

        if self._backend.requires_root():
            # Backend requires root privileges
            if self._frontend.uses_privileged_functions():
                # Frontend uses privileged functions -> check if we are root
                if os.getuid() != 0 and os.geteuid() != 0:
                    LOG.debug('[nonroot] Root privileges required.')
                    args = app_args[:]
                    args.insert(0, sys.argv[0])
                    result = self._frontend.handle_unprivileged_invocation(
                        args)
                    raise ExitProgramException(result)
                else:
                    # We are root already: great.
                    LOG.debug('[got-root] Frontend uses privileged functions.')
                    self._frontend_privileged = True
            else:
                # Frontend does not use privileged functions -> fine with us.
                self._frontend_privileged = False
                LOG.debug('[got-root] Frontend does not use privileged '+
                          'functions.')
        else:
            # The backend does not require root.
            if self._frontend.uses_privileged_functions():
                LOG.info('[non-root] Frontend uses privileged functions')
                self._frontend_privileged = True
            else:
                self._frontend_privileged = False
                LOG.info('[non-root] Frontend does not use privileged '+
                         'functions.')

    ### BEGIN: Helper methods
    def _load_backend(self, backend_name):
        """ Invokes the backend loader and tries to load a backend. """
        if type(backend_name) == str:
            backend_name = self._config.get('defaults', 'backend_name',
                                            default=backend_name)
            self._backend = self._load_meta(BackendLoader, backend_name,
                                            "backend", BackendBase, self)
        else:
            self._backend = backend_name(self)

    def _load_dist_specific(self, dist_name):
        """ Invokes distspecific loader and tries to load the dist specific
        module"""
        if type(dist_name) == str:
            dist_name = self._config.get('defaults', 'dist_name',
                                         default=dist_name)
            self._dist_specific = self._load_meta(DistLoader, dist_name,
                                              "dist_specific", DistBase)
        else:
            self._dist_specific = dist_name()

    def _load_frontend(self, frontend_name):
        """ Invokes frontend loader and tries to load the frontend """
        if type(frontend_name) == str:
            self._frontend = self._load_meta(FrontendLoader, frontend_name,
                                             "frontend", FrontendBase)
        else:
            self._frontend = frontend_name()

    @classmethod
    def _verify_module(cls, module_object, base_class, module_name):
        """ Verifies that a given module_object subclasses a given
        base class

        :param module_object: Module
        :param base_class: Base class
        :param module_name: The module's name
        :raises: :exc:`InvalidBaseClass` if the base class was invalid.
        """
        if not isinstance(module_object, base_class):
            LOG.fatal('Invalid %s: %r is not a subclass of %r', module_name,
                      module_object, base_class)
            raise InvalidBaseClass(module_object, base_class)

    @classmethod
    def _load_meta(cls, loader_class, symbol_name, module_name, base_class,
                   *module_args, **module_kwargs):
        """ Meta loader invocation

        :param loader_class: Loader class
        :param symbol_name: Name of the symbol to load
        :param module_name: Name of the module
        :param base_class: Base class used for verification
        :param *module_args: Arguments to be passed to the module constructor
        :param **module_kwargs: Keyword-Arguments to be passed to the module
          constructor
        :returns: Module object
        :raises: :exc:`UpdateManager.Utils.loader.LoaderException` if
          loading fails.
          :raises: :exc:`InvalidBaseClass` if the base class was invalid.
        """
        loader = loader_class()
        try:
            symbol = loader.get_class(symbol_name)
            obj = symbol(*module_args, **module_kwargs)
            cls._verify_module(obj, base_class, module_name)
            return obj
        except InvalidImplementationName, inval_e:
            LOG.fatal('Invalid implementation name %s', symbol_name)
            raise LoadingFailedException(symbol_name)
        
        except LoaderException, loader_e:
            LOG.fatal('Loading %s %s failed: %s', module_name, symbol_name,
                      loader_e.message)
            
            raise LoadingFailedException(symbol_name)

    def _handle_options(self, option_parser):
        """ Handles the options specified at the command line """
        (options, args) = option_parser.parse_args(self._app_args)
        if args:
            LOG.debug('Additional arguments passed to update-manager: "%s"',
                      ' '.join(args))
        
        self._options = options

        logger = logging.getLogger('UpdateManager')
        loglevel_name = options.loglevel

        loglevel = LOGLEVEL_NAME_MAP[loglevel_name]
        logger.setLevel(loglevel)
        LOG.debug('Loglevel set to %s.', loglevel_name)

    ### END: Helper methods

    ### BEGIN: Backend wrappers
    def abort_operation(self):
        """ Wrapper around the backend's abort_operation method. """
        LOG.debug('Aborting current operation')
        try:
            return self._backend.abort_operation()
        except Exception, ex:
            self._frontend.handle_exception(ex)
    
    def reload_cache(self):
        """ Wrapper around the backend's reload_cache method. """
        LOG.debug('Reloading the package cache.')
        try:
            return self._backend.reload_cache(
                self._frontend.get_cache_handler())
        except Exception, ex:
            self._frontend.handle_exception(ex)

    def reload_package_list(self):
        """ Wrapper around the backend's download_package_lists method. """
        if not self._frontend_privileged:
            LOG.fatal('Frontend did not request privileged operation, but '+
                      ' reload_package_list was called.')
            return False
        LOG.debug('Reloading the package list.')
        try:
            return self._backend.download_package_lists(
                self._frontend.get_list_handler())
        except Exception, ex:
            self._frontend.handle_exception(ex)

    def commit(self, selected_updates, writefd=None):
        """ Wrapper around the backend's commit method.

        :param selected_updates: List of updates that were selected for upgrade
        :param writefd: FD package manager messages get written to,
          may be None.
        """
        if not self._frontend_privileged:
            LOG.fatal('Frontend did not request privileged operation, but '+
                      ' commit was called.')
            return False
         
        LOG.debug('Commit operation started.')
        try:
            return self._backend.commit(selected_updates,
                                        self._frontend.get_commit_handler(),
                                        writefd)
        except Exception, ex:
            self._frontend.handle_exception(ex)

    def is_locked(self, by_us=False):
        """ Wrapper around the backend's is_locked method.

        :param by_us: Check if the lock is held by us.
        """
        try:
            return self._backend.locked(by_us=by_us)
        except Exception, ex:
            self._frontend.handle_exception(ex)

    def get_available_updates(self, dist_upgrade=True):
        """ Wrapper around the backend's get_available_updates method.
        :param dist_upgrade: Defines whether to do a dist upgrade or not.
        
        :returns: A list of :class:`UpdateManager.Backend.PackageInfoBase`
          objects.
          
        .. versionchanged:: 0.200.0~exp1
        """
        try:
            return self._backend.get_available_updates(
                dist_upgrade=dist_upgrade)
        except Exception, ex:
            self._frontend.handle_exception(ex)

    ### END: Backend wrappers

    ### BEGIN: DistSpecific wrappers
    def get_update_category_name(self, cat_id):
        """ Wrapper around the the dist-specific get_update_category_name
        method.

        :param cat_id: The update category's id.
        :returns: The localized update category name.
        """
        return self._dist_specific.get_update_category_name(cat_id)

    def get_update_category(self, pkg_info):
        """ Wrapper around the dist-specific get_update_category method.

        :param pkg_info: :class:`UpdateManager.Backend.PackageInfoBase` object
        :returns: Update category ID
        """
        return self._dist_specific.get_update_category(pkg_info)

    def get_dist_name(self):
        """ Wrapper around the dist-specific get_name method.

        :returns: The distribution's name.
        """
        return self._dist_specific.get_name()

    def get_changelog(self, pkg_info, changelog_handler):
        """ Wrapper around the dist-specific get_changelog method.
        """
        return self._dist_specific.get_changelog(pkg_info, changelog_handler)

    def get_bug_script_name(self):
        """ Wrapper around the dist-specific get_bug_script_name method.

        .. versionadded: 0.200.0~exp1
        """
        return self._dist_specific.get_bug_script_name()
    
    ### END: DistSpecific wrappers

    ### BEGIN: Frontend wrappers

    def uses_privileged_functions(self):
        return self._frontend.uses_privileged_functions()

    ## END: Frontend wrappers

    def get_option(self, option_name):
        """
        Gets the value of a commandline option/switch.

        :param option_name: Option name
        :returns: Value of option
        """
        return getattr(self._options, option_name, None)

    def set_option(self, option_name, value):
        """
        Sets the value of a commandline option/switch.

        :param option_name: Option name
        :param value: New value for option
        """
        setattr(self._options, option_name, value)
                                                                    
    def main(self):
        """
        Initializes the frontend, reloads the package cache and
        runs the frontend's main loop.
        """
        self._backend.init_backend(self)
        if self._frontend_privileged:
            self._backend.acquire_lock()
        self._frontend.init_frontend()
        
        self.reload_cache()
        res = self._frontend.main(self)
        if self._frontend_privileged:
            self._backend.release_lock()
        if type(res) != int:
            LOG.debug('Frontend.main did not return an integer (%r)', res)
            res = 255
        else:
            LOG.debug('Frontend exited with status %s.', res)
        raise ExitProgramException(res)
