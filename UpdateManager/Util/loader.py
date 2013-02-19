# UpdateManager/Util/loader.py
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

""" Module loader """

import logging
import os

LOG = logging.getLogger('UpdateManager.Util.loader')

class LoaderException(Exception):
    """ Base loader exception """
    pass

class InvalidLoaderClassName(LoaderException):
    """ Invalid loader class name exception """
    def __init__(self, class_name):
        msg = 'Invalid loader class name (does not end in "Loader"): %s' \
              % (class_name)
        LoaderException.__init__(self, msg)

class InvalidImplementationName(LoaderException):
    """ Invalid implementation name """
    def __init__(self, impl_name):
        msg = 'Invalid implementation name %s' % (impl_name)
        LoaderException.__init__(self, msg)

class LoaderBase(object):
    """ Base symbol loader class """
    def __init__(self, module_prefix, interface_class, basedir):
        self._module_prefix = module_prefix
        self._interface_class = interface_class
        self._cls_name = self.__class__.__name__

        if not self._cls_name.endswith('Loader'):
            raise InvalidLoaderClassName(self._cls_name)

        self._name_suffix = self._cls_name[:-6]
        self._basedir = basedir
        self._modules = {}
        self._find_modules()

    def _find_modules(self):
        """ Tries to find all available modules and adds them to
        the module list.
        """
        mod_names = []

        def __recursive_mod_find(dir, prefix):
            LOG.debug('[%s] Checking directory %s (prefix=%s)',
                      self._cls_name, dir, prefix)
            for name in os.listdir(dir):
                full_path = os.path.join(dir, name)
                if name == '__init__.py' or name == 'loader.py':
                    continue
                if os.path.isdir(full_path) or \
                       (name.endswith('.py') and os.path.isfile(full_path)):
                    if name.endswith('.py'):
                        name = name[:-3]

                    mod_names.append('%s.%s' % (prefix, name))
                    LOG.debug('[%s] Found module %s.%s',
                              self._cls_name, prefix, name)
        __recursive_mod_find(self._basedir, self._module_prefix)

        for mod_name in mod_names:
            try:
                LOG.debug('[%s] Importing %s', self._cls_name, mod_name)
                module = __import__(mod_name, fromlist=['*',])
                for symbol_name in dir(module):
                    sym = getattr(module, symbol_name)
                    if type(sym) == module:
                        continue
                    
                    try:
                        if not sym is self._interface_class and \
                               issubclass(sym, self._interface_class) and \
                               symbol_name.endswith(self._name_suffix):
                            noprefix_symbol_name = symbol_name.replace(\
                                self._name_suffix, '')
                            self._modules[noprefix_symbol_name] = sym
                            LOG.debug('[%s] Found implementation %s.%s (%s)',
                                      self._cls_name, mod_name,
                                      symbol_name, sym)
                    except TypeError:
                        LOG.debug('[%s] Ignored symbol %s.%s (type error)',
                                  self._cls_name,
                                  mod_name, symbol_name)
                    except:
                        pass
                    
            except ImportError, e:
                LOG.debug('[%s] Could not load module %s (%s).',
                          self._cls_name, mod_name, e)

    def get_implementations(self):
        """ Returns list of implementation names """
        return self._modules.keys()

    def get_class(self, name):
        """ Returns symbol for given implementation name

        :param name: Implementation name
        """
        if not name in self._modules.keys():
            LOG.debug('[%s] Unknown implementation: %s',
                      self._cls_name, name)
            raise InvalidImplementationName(name)
        return self._modules[name]
            
