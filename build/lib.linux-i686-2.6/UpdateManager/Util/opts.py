# UpdateManager/Util/opts.py
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

import optparse

from UpdateManager import __version__
from UpdateManager.Exceptions import ExitProgramException

make_option = optparse.make_option

class OptParser(optparse.OptionParser):
    """ Extended version of optparse.OptionParser """
    def __init__(self, *args, **kwargs):
        ver_str = '%prog: version ' + __version__
        optparse.OptionParser.__init__(self, version=ver_str, *args, **kwargs)
        
    def exit(self, status=0, msg=None):
        """
        Overridde exit so the option parser does not call sys.exit directly,
        but rather raises an
        :exc:`UpdateManager.Application.ExitProgramException`.
        """
        raise ExitProgramException(status, msg=msg)
    
        
