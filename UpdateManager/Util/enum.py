# UpdateManager/Util/enum.py
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

""" Implementation of autodoc-aware Enum for Python """

class Enum(object):
    """ Simple autodoc-aware C-like enumeration.

    All enumeration names must be upper case and may not contain spaces, see
    below for examples.
    
    >>> ReturnCodes = Enum('SUCCESS', ERROR='A non-fatal error occured',
                           FATAL='A fatal error occured')
    >>> ReturnCodes.SUCCESS
    0


    .. note:: When using values with docstring the values are ordered
      alphabetically by their name. This is caused by how the dict type
      works.
      
    """

    _enum_name = ':class:`Enum<UpdateManager.Util.enum.Enum>`'
    _allowed_characters = None
    
    def __init__(self, *names, **names_with_doc):
        """
        Creates an enumeration and updates the docstring of the generated
        object.

        :param *names: A list of enumeration names without a docstring.
        :param **names_with_doc: A dictionary of enumeration names and their
          docstrings. The key forms the name, whilst the value represents
          the docstring.

        All enumeration names must be upper case and may not contain spaces.

        Example::
          ReturnCodes = Enum('SUCCESS', ERROR='A non-fatal error occured',
                             FATAL='A fatal error occured')
          NegativeCodes = Enum('UI_ERROR', negative=True,
                               BACKEND_ERROR='Backend error')
        """
        self.__doc__ = '''%s:

''' % (self._enum_name)

        for i in range(0, len(names)):
            value = self._nodoc_id_to_value(i)
            
            self._name_sanity_check(names[i])

            self.__dict__[names[i]] = value
            self.__doc__ += '''**%s** = *%d*

''' % (names[i], value)

        i = self._doc_first_value(len(names))
            
        for name in names_with_doc.keys():
            self._name_sanity_check(name)
            
            self.__dict__[name] = i
            docstring = names_with_doc[name]

            if type(docstring) != str:
                raise TypeError('Values of kwargs must be (doc-)strings.')
            
            self.__doc__ += '''**%s** = *%d*
  %s

''' % (name, i, names_with_doc[name])
            
            i = self._doc_next_value(i)
        
        self.__doc__ += '\n'
        
    @classmethod
    def _nodoc_id_to_value(cls, identity):
        """ Map ids of names without a docstring to a value

        :param id: Name id
        """
        return identity

    @classmethod
    def _doc_next_value(cls, value):
        """ Gets the next value """
        return value+1

    @classmethod
    def _doc_first_value(cls, nodoc_max_value):
        """ Gets the first value """
        return nodoc_max_value

    def _name_sanity_check(self, name):
        """ Checks an enum name for sanity.

        Names may only consist of uppercase, characters and are limited
        to the values A-Z, 0-9 and _ (underscore).
        """
        if getattr(self, '_allowed_characters', None):
            allowed_characters = self._allowed_characters
        else:
            allowed_characters = '_'

            # Build the allowed character list.
            for i in range(ord('A'), ord('Z')+1):
                allowed_characters += chr(i)
            for i in range(ord('0'), ord('9')+1):
                allowed_characters += chr(i)
        
        for i in range(0, len(name)):
            char = name[i]
            if char not in allowed_characters:
                e_msg = 'Enumeration names may only consist of '+\
                        'uppercase letters, numbers and underscores:\n'
                e_msg += '%s\n' % (name)
                j = 0
                while (j < i):
                    e_msg += ' '
                    j += 1
                    
                e_msg += '^'
                raise TypeError(e_msg)

    def __getattr__(self, name):
        """ Custom attribute resolution """
        if name in self.__dict__:
            return self.__dict__['name']
        raise AttributeError(name)
        

    def __setattr__(self, name, value):
        """ Only the __doc__ attribute may be set """
        if name != '__doc__':
            raise TypeError('Cannot set values of %s objects.' \
                            % (self.__class__.__name__))
        else:
            self.__dict__['__doc__'] = value

    def __delattr__(self, name):
        """ No attributes may be deleted """
        raise TypeError('Cannot delete values of %s objects.' \
                        % (self.__class__.__name__))
                
class NegativeEnum(Enum):
    """
    Simple autodoc-aware C-like negative enumeration.

    The difference to :class:`Enum` is that values are assigned starting at
    *-1* downwards.

    >>> NegativeCodes = Enum('UI_ERROR', negative=True,
                             BACKEND_ERROR='Backend error')
    >>> NegativeCodes.UI_ERROR
    -1
    
    """
    _enum_name = ':class:`NegativeEnum<UpdateManager.Util.enum.NegativeEnum>`'

    @classmethod
    def _nodoc_id_to_value(cls, identity):
        """ Map ids of names without a docstring to a value
        
        :param id: Name id
        """
        return -(identity+1)

    @classmethod
    def _doc_next_value(cls, value):
        """ Gets next value """
        return value-1

    @classmethod
    def _doc_first_value(cls, nodoc_max_value):
        """ Gets first value """
        return (nodoc_max_value*-1)-1
