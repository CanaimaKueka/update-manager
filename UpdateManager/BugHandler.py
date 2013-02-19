# UpdateManager/BugHandler.py
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

""" BugHandler module """

import logging
import os
import subprocess
import sys
import tempfile
import threading
import traceback

LOG = logging.getLogger('UpdateManager.BugHandler')

BUG_SCRIPT_DIR = "/usr/share/update-manager/bug_script"
""" Bug script directory (/usr/share/update-manager/bug_script) """
THIS_PATH = os.path.abspath(os.path.dirname(__file__))
""" Absolute path to the directory containing this file """
DEVEL_BUG_SCRIPT_DIR = os.path.abspath(os.path.join(THIS_PATH, '..', 'data',
                                                    'bug_script'))
""" Path to developtment bug script directory """

class ExceptionHandlerBase(object):
    @classmethod
    def pre_handle_exception(cls):
        """ Method to be called before handle_exception is invoked.

        Do any preparation for the actual handling of the exception here.
        This method is optional.
        """
        pass
    
    @classmethod
    def handle_exception(cls, ex_type, ex_value, ex_tb, ex_origin,
                         with_script):
        """ Exception handling method.

        :param ex_type: Exception type
        :param ex_value: Exception value
        :param ex_tb: Exception traceback
        :param ex_origin: Thread this exception originated from
        :param with_script: Set to True if a bug script will be executed.

        .. note::
          This method will be invoked by the special Exception Handler Thread,
          so make sure you do not invoke functions which are not thread-safe.

        .. note::
          If you return from this function execution of all threads will
          be resumed. However, correct execution can not be guaranteed after
          the exception has been raised, so consider using sys.exit
          in the implementation of this method.
        """

class Thread(threading.Thread):
    """
    A special implementation of threading.Thread which does not do
    'intelligent' processing of exceptions inside threads.
    """
    def run(self, *args, **kwargs):
        """ This method is the core logic of :class:`Thread`.

        It differs from the original threading.Thread in the way exceptions
        are processed.
        This version doesn't process them, but rather lets sys.excepthook
        do its magic.
        """
        try:
            threading.Thread.run(self, *args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            sys.excepthook(*sys.exc_info())

    def __repr__(self):
        return '<BugHandler.%s>' % (threading.Thread.__repr__(self)[1:-1])

class BugHandler(object):
    """ BugHandler class.

    Provides the excepthook function and all error reporting
    logic.
    """
    INITIALIZED = False
    handler = None
    application = None
    
    @classmethod
    def initialize(cls, application):
        """ Initializes the ExceptionHandler.

        :param application: :class:`UpdateManager.Application.Application`
          object

        """
        cls.application = application
        cls.handler = None
        if sys.excepthook == sys.__excepthook__ or True:
            sys.excepthook = cls.excepthook
            LOG.debug('BugHandler initialized.')
            cls.INITIALIZED = True
        else:
            LOG.debug('BugHandler not initialized: excepthook (%r) present',
                      sys.excepthook)

    @classmethod
    def install_handler(cls, handler):
        """ Installs an exception handler.

        :param handler: :class:`ExceptionHandlerBase` implementation *class*.

        .. note::
          This method takes a class as `handler` parameter, not an instance!
        
        """
        if not cls.INITIALIZED:
            LOG.debug('Not installing exception handler %r: BugHandler '+\
                      'is not initialized.', handler)
            return False
        if cls.handler:
            LOG.debug('Not installing exception handler %r: already '+\
                      'installed.', cls.handler)
            return False
        if not issubclass(handler, ExceptionHandlerBase):
            LOG.debug('Not installing exception handler %r: not a'+\
                      ' subclass of ExceptionHandlerBase.', handler)
            return False
        cls.handler = handler
        handler.application = cls.application
        LOG.debug('Installed exception handler %r.', handler)
        return True

    @classmethod
    def excepthook(cls, ex_type, ex_value, ex_tb):
        """ Exception hook method.

        This method is invoked when an unhandled exception occurs anywhere
        in the program.
        If no exception handler has been installed yet sys.__excepthook__
        will be invoked.

        .. note::
          This method will exit the program through os._exit and this way
          kill every running thread.
        """
        if ex_type == SystemExit or ex_type == KeyboardInterrupt:
            LOG.debug('Passing %r to sys.__excepthook__.', ex_type)
            return sys.__excepthook__(ex_type, ex_value, ex_tb)

        # We need to replace sys.excepthook with the original excepthook.
        sys.excepthook = sys.__excepthook__
        
        if not cls.handler:
            LOG.error('No exception handler installed.')
            return sys.__excepthook__(ex_type, ex_value, ex_tb)
        
        ex_origin = threading.currentThread()
        script_name = cls.application.get_bug_script_name()
        LOG.debug("Bug script name: %s", script_name)
        with_script = False
        path = None
        if script_name:
            path = cls.bug_script_path(script_name)
            with_script = os.path.exists(path)

        res = cls.handler.handle_exception(ex_type, ex_value, ex_tb,
                                           ex_origin, with_script)
        if res is True and with_script and path:
            LOG.debug("Reporting bug...")
            cls.bug_script_invoke(path, ex_type, ex_value,
                                  ex_tb, ex_origin)
        else:
            LOG.debug("Not reporting bug: res=%s,with_script=%s,path=%s",
                      res, with_script, path)

        # Finally we need to exit the program.
        os._exit(3)

    @classmethod
    def bug_script_path(cls, bug_script_name):
        if os.path.exists(DEVEL_BUG_SCRIPT_DIR):
            LOG.debug("Loading bug_script/%s from development bug script "+\
                      "directory %s.", bug_script_name, DEVEL_BUG_SCRIPT_DIR)
            return os.path.join(DEVEL_BUG_SCRIPT_DIR, bug_script_name)
        return os.path.join(BUG_SCRIPT_DIR, bug_script_name)

    @classmethod
    def bug_script_invoke(cls, path, ex_type, ex_value, ex_tb, ex_origin):
        LOG.debug("Writing bug file...")
        info_file = tempfile.NamedTemporaryFile(prefix='update-manager-bug')
        info_file.write("The information below has been automatically "+\
                        "generated.\n")
        info_file.write("Please do not remove this from your bug report.\n\n")
        info_file.write("- Exception Type: %r\n" % ex_type)
        info_file.write("- Exception Value: %r\n" % ex_value)
        info_file.write("- Exception Origin: %r\n" % ex_origin)
        info_file.write("- Exception Traceback:\n%s\n\n" \
                        % "".join(traceback.format_tb(ex_tb)))
        info_file.flush()
        LOG.debug("Bug file written to %s.", info_file.name)
        
        tb_info = traceback.extract_tb(ex_tb)[-1]
        origin_file = "update-manager"
        if tb_info and not os.path.exists(os.path.join(THIS_PATH, '..',
                                                       'setup.py')):
            found_tb_info = False
            # Make sure the file is part of update-manager. If not try
            # finding the origin inside um.
            # If that fails too we need to report a bug against update-manager.
            for i in range(0, len(tb_info)):
                if tb_info[i].startswith(THIS_PATH):
                    origin_file = tb_info[i]
                    LOG.debug("Reporting a bug in file %s.", origin_file)
                    found_tb_info = True
                    break

            if not found_tb_info:
                LOG.debug("Reporting a bug in update-manager (origin: %s).",
                          tb_info[0])
                
        elif os.path.exists(os.path.join(THIS_PATH, '..', 'setup.py')):
            LOG.debug("Reporting a bug for update-manager running from "+\
                      "source.")
        else:
            LOG.debug("No usable traceback")

        description = '[CRASH] Uncaught exception: %s' % (ex_type.__name__)
        if tb_info:
            short_file_name = tb_info[0]
            try:
                idx = short_file_name.index("/UpdateManager/")
                short_file_name = short_file_name[idx+len("/UpdateManager/"):]
            except ValueError:
                pass
            description = '[CRASH] Uncaught exception %s in %s:%d' \
                          % (ex_type.__name__, short_file_name,
                             tb_info[1])

        subject_file = tempfile.NamedTemporaryFile(prefix="update-manager-bug")
        subject_file.write(description)
        subject_file.flush()
        
        LOG.debug("Executing bug script...")
        try:
            args = [path, info_file.name, origin_file, subject_file.name]
            LOG.debug("Subprocess arguments: %s", args)
            subprocess.call(args)
        except OSError, e:
            LOG.debug("OSError from subprocess.call: %s", e)
        LOG.debug("Bug script returned.")
        info_file.close()
        subject_file.close()

