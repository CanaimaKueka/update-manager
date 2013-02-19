# UpdateManager/Frontend/GtkCommon/__init__.py
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

""" Common Gtk functionality """

import logging
import os.path

LOG = logging.getLogger('UpdateManager.Frontend.GtkCommon')

DATA_DIR = "/usr/share/update-manager/"
""" Data directory (/usr/share/update-manager/) """
DESKTOP_DIR = "/usr/share/applications/"
""" Desktop file directory (/usr/share/applications/) """

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
"""
Absolute path to the directory containing this file
"""
DEVEL_DATA_DIR = os.path.abspath(os.path.join(THIS_PATH, '..', '..', '..',
                                              'data'))
""" Absolute path to development data (THIS_PATH/../../../data/) """

def get_ui_path(ui_filename):
    """ Returns path to an UI file.

    :param ui_filename: UI file name.
    """
    data_dir = DATA_DIR
    if os.path.exists(DEVEL_DATA_DIR):
        data_dir = DEVEL_DATA_DIR
        LOG.debug('Loading ui/%s from development data directory %s.',
                  ui_filename, data_dir)
    return os.path.join(data_dir, 'ui', ui_filename)

def get_desktop_path(desktop_filename):
    """ Returns path to a desktop file.

    :param desktop_filename: Desktop file name
    """
    data_dir = DESKTOP_DIR
    if os.path.exists(DEVEL_DATA_DIR):
        data_dir = DEVEL_DATA_DIR
        LOG.debug('Using desktop file %s in development data directory %s.',
                  desktop_filename, data_dir)
    return os.path.join(data_dir, desktop_filename)
    
