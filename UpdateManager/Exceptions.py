# UpdateManager/Exceptions.py
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

""" Exceptions module """

from UpdateManager.Util.enum import Enum

EXIT_STATUS_CODES = Enum(
    NO_ERROR="No error occured",
    LOADING_FAILED="Loading of a module failed",
    INVALID_BASE_CLASS="An invalid base class was specified",
    )

class ExitProgramException(Exception):
    """ Program is about to exit """
    def __init__(self, status, msg="Program exited"):
        self.status = status
        Exception.__init__(self, msg)

class LoadingFailedException(ExitProgramException):
    """ Loading of a module failed """
    def __init__(self, module_name):
        msg = "%s could not be loaded" % (module_name)
        ExitProgramException.__init__(self, EXIT_STATUS_CODES.LOADING_FAILED,
                                      msg=msg)

class InvalidBaseClass(ExitProgramException):
    """ Invalid base class exception """
    def __init__(self, instance, base_class):
        self.instance = instance
        self.base_class = base_class
        msg = "%r is not a subclass of %s" % (instance, base_class)
        ExitProgramException.__init__(self,
                                      EXIT_STATUS_CODES.INVALID_BASE_CLASS,
                                      msg=msg)

class InvalidLoglevelName(ExitProgramException):
    """ Invalid loglevel name exception """
    def __init__(self, name):
        self.loglevel_name = name
        msg = "Invalid loglevel name: %s" % name
        ExitProgramException.__init__(self,
                                      EXIT_STATUS_CODES.INVALID_LOGLEVEL_NAME,
                                      msg=msg)
