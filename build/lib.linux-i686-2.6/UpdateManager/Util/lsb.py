# UpdateManager/Util/lsb.py
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

""" Wrappers around lsb_release """

import logging
import subprocess

LOG = logging.getLogger('UpdateManager.Util.lsb')

LSB_RELEASE_PATH = "/usr/bin/lsb_release"
""" Path to the lsb_release binary """

class LSBError(Exception):
    """ lsb_release error representation """
    def __init__(self, err):
        msg = 'lsb_release returned error: %s' % (err)
        Exception.__init__(self, msg)

def _invoke_lsb_release(args):
    """ Helper function that invokes lsb_release with the given
    arguments and returns its output.

    :param args: Arguments to lsb_release
    :returns: Output of lsb_release
    :raises: :exc:`LSBError` if an error occurs
    """
    if type(args) != list:
        args = list([args, ])
        
    args.insert(0, LSB_RELEASE_PATH)
    pipe = subprocess.Popen(args, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    out, err = pipe.communicate()
    if err:
        raise LSBError(err)
    return str(out).strip()

def get_distribution_name():
    """ Gets the distribution name via lsb_release

    :returns: Distribution name
    """
    distribution_name = _invoke_lsb_release('-si')
    LOG.debug('lsb_release reported distribution name %s'
              % (distribution_name))
    return distribution_name

def get_distribution_release():
    """ Gets the distribution release via lsb_release

    :returns: Distribution release
    """
    release = _invoke_lsb_release('-sr')
    LOG.debug('lsb_release reported distribution release %s'
              % (release))
    return release

def get_distribution_codename():
    """ Gets the distribution codename via lsb_release

    :returns: Distribution codename
    """
    codename = _invoke_lsb_release('-sc')
    LOG.debug('lsb_release reported distribution codename %s'
              % (codename))
    return codename
