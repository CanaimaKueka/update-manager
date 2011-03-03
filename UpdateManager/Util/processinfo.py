# UpdateManager/Util/processinfo.py
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

import logging
import os

LOG = logging.getLogger('UpdateManager.Util.procesinfo')

class ProcessInfo(object):
    """ Process info representation """
    def __init__(self, pid):
        assert(type(pid) == int)
        self._pid = pid
        self._owner_uid = None
        self._parent_pid = None
        self._name = None
        self._parent = None
        self._ready = False
        self.__read_info()

    def __read_info(self):
        """ Reads the process info from /proc/<pid>/status """
        path = os.path.join('/proc/', str(self._pid), 'status')
        assert(os.path.exists(path))
        try:
            fp = open(path, 'r')
            for line in fp.readlines():
                data = line.strip().split('\t')
                name = data[0]
                if name == 'PPid:':
                    self._parent_pid = int(data[1])
                elif name == 'Uid:':
                    self._owner_uid = int(data[1])
                    # TODO: What can we use data[2:] for? What does it mean?
                elif name == 'Name:':
                    self._name = data[1]
                    
            fp.close()
        except IOError, e:
            LOG.error('IO Error occured: %s', e)

    @property
    def parent(self):
        """ Parent ProcessInfo object """
        if self._parent is not None:
            return self._parent

        if self._parent_pid != 0:
            self._parent = ProcessInfo(self._parent_pid)
        return self._parent

    @property
    def pid(self):
        """ Process ID """
        return self._pid

    @property
    def owner_uid(self):
        """ Process owner UID """
        return self._owner_uid

    @property
    def name(self):
        """ Process name """
        return self._name

    def __repr__(self):
        return '<ProcessInfo(pid=%d, name=%s, owner_uid=%s, parent_pid=%s)' %\
               (self._pid, self._name, self._owner_uid, self._parent_pid)

def find_nonroot_parent():
    """
    Finds the first parent process that is not owned by root, starting
    at the current process.

    :returns: :class:`ProcessInfo` object or None
    """
    my_pid = os.getpid()
    my_proc = ProcessInfo(my_pid)
    if my_proc.owner_uid != 0:
        return my_proc

    parent_proc = my_proc.parent
    while parent_proc:
        LOG.debug('Proc: %r', parent_proc)
        if parent_proc.owner_uid != 0:
            break

        parent_proc = parent_proc.parent

    return parent_proc
