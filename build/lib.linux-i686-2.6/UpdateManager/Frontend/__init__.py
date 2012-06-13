# UpdateManager/Frontend/__init__.py
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

""" Frontend base code """

class FrontendBase(object):
    """
    Base frontend class.

    This class implements optional methods as described by the
    interface. Inheriting from this class makes sure the implementation
    of the frontend interface is valid, even though you do not
    need some optional methods.

    :param uses_privileged_funcs: Boolean that defines whether the frontend
      uses privileged functions (list updating, commit) or not.
    """
    def __init__(self, uses_privileged_funcs=True):
        self._uses_privileged_funcs = uses_privileged_funcs

    def init_gettext(self, app_name, locale_dir):
        """
        Gettext initialization stub.

        This stub does not do anything and may be overridden to provide
        per-frontend gettext initialization.
        """
        pass

    def init_frontend(self):
        """
        Initialize and show the frontend, called by Application when
        everything else is ready.

        You should not implement your application's main loop
        in here, but rather in :meth:`main`.
        """
        raise NotImplementedError

    def main(self, application):
        """
        Frontend main loop.
        """
        raise NotImplementedError

    def handle_unprivileged_invocation(self, app_args):
        """
        Handling of update-manager being invoked
        by unprivileged (= non-root) user.

        This method should fork out and launch a new
        update-manager instance as privileged user.

        For the Gtk frontend, for example, this means invoking the
        program via gksu.

        :param app_args: Command line arguments.
        """
        raise NotImplementedError

    def uses_privileged_functions(self):
        """
        Returns whether this frontend uses privileged functions (list updating,
        committing).

        The return value of this method can be set via the
        uses_privileged_funcs keyword argument of the :meth:`__init__` method.

        If this method returns False root privileges will not be obtained,
        even though the backend would requires those.
        """
        return self._uses_privileged_funcs

    def get_cache_handler(self):
        """
        Returns an instance of the frontend's
        :class:`UpdateManager.Backend.CacheProgressHandler` implementation.
        """
        raise NotImplementedError

    def get_list_handler(self):
        """
        Returns an instance of the frontend's
        :class:`UpdateManager.Backend.ListProgressHandler` implementation.
        """
        raise NotImplementedError

    def get_commit_handler(self):
        """
        Returns an instance of the frontend's
        :class:`UpdateManager.Backend.CommitProgressHandler` implementation.
        """
        raise NotImplementedError

    def handle_exception(self, exception):
        """
        Handles an uncaught exception.

        :param exception: Exception instance

        .. versionadded: 0.200.1
        """
        raise NotImplementedError
