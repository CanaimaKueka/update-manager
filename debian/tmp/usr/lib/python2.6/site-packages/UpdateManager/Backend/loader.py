# UpdateManager/Backend/loader.py
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

""" Backend module loader """

import os.path

from UpdateManager.Backend import BackendBase
from UpdateManager.Util.loader import LoaderBase

class BackendLoader(LoaderBase):
    """ Backend loader """
    def __init__(self):
        LoaderBase.__init__(self, 'UpdateManager.Backend',
                            BackendBase, os.path.dirname(__file__))
