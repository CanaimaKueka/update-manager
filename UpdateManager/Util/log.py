# UpdateManager/Util/log.py
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

""" Logging initialization and helpers """

import logging
import os

LOGLEVEL_NAME_MAP = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'fatal': logging.FATAL,
    }
""" Loglevel name to loglevel mapping """

DEFAULT_LOGLEVEL = logging.ERROR
""" Default loglevel """

def init_logging():
    """ Initializes update-manager logging. """
    early_debug = os.environ.has_key("DEBUG_UPDATE_MANAGER")
    logger = logging.getLogger('UpdateManager')
    hdlr = logging.StreamHandler()
    fmt = logging.Formatter('[%(levelname)8s:%(name)-20s] %(message)s')
    hdlr.setFormatter(fmt)
    # Remove all other handlers
    for hdlr in logger.handlers:
        logger.removeHandler(hdlr)

    logger.addHandler(hdlr)

    if not early_debug:
        logger.setLevel(DEFAULT_LOGLEVEL)
    else:
        logger.setLevel(logging.DEBUG)
        logger.debug('Early debug logging activated.')
