# UpdateManager/Config.py
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

import os.path
from ConfigParser import SafeConfigParser

SYS_CONFFILE_PATH = '/etc/update-manager/settings.conf'
USER_CONFFILE_PATH = os.path.expanduser('~/.update-manager/user.conf')
DEV_CONFFILE_PATH = os.path.join(os.path.dirname(__file__),
                               '..', 'data', 'settings.conf')

class UpdateManagerConfig(SafeConfigParser):
    """ Update Manager config file class """
    def __init__(self):
        SafeConfigParser.__init__(self)
        self.read([DEV_CONFFILE_PATH, USER_CONFFILE_PATH, SYS_CONFFILE_PATH])

    def get(self, section, option, default=None):
        """ Get an option value for a given section

        :param section: Section name
        :param option: Option name
        :param default: Default value to return if option is not present in
          config file
        """
        if not self.has_option(section, option):
            return default
        return SafeConfigParser.get(self, section, option)

    def getboolean(self, section, option, default=False):
        """ Get a boolean option value for a given section

        :param section: Section name
        :param option: Option name
        :param default: Default value to return if option is not present in
          config file
        """
        if not self.has_option(section, option):
            return default
        return SafeConfigParser.getboolean(self, section, option)

    def getint(self, section, option, default=0):
        """ Get an integer option value for a given section

        :param section: Section name
        :param option: Option name
        :param default: Default value to return if option is not present int
          config file
        """
        if not self.has_option(section, option):
            return default
        return SafeConfigParser.getint(self, section, option)

    def getfloat(self, section, option, default=0.0):
         """ Get a float option value for a given section
         
         :param section: Section name
         :param option: Option name
         :param default: Default value to return if option is not present int
           config file
         """
         if notself.has_option(section, option):
             return default
         return SafeConfigParser.getfloat(self, section, option)
                     
    
        
