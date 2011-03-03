# UpdateManager/Frontend/Gtk/GtkProgress.py 
#  
#  Copyright (c) 2004,2005,2009 Canonical
#                2009 Stephan Peijnik
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
#          Stephan Peijnik <debian@sp.or.at>
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

""" Gtk progress helpers """

import pygtk
pygtk.require('2.0')
import gtk
import gobject

from gettext import gettext as _, ngettext
import logging
import threading
import vte

from UpdateManager.Util.enum import Enum
from UpdateManager.Backend import CacheProgressHandler, ListProgressHandler
from UpdateManager.Backend import CommitProgressHandler
from UpdateManager.Util.humanize import humanize_size, humanize_seconds

LOG = logging.getLogger('UpdateManager.Frontend.Gtk.GtkProgress')

class GtkCacheProgress(CacheProgressHandler):
    """
    Gtk :class:`UpdateManager.Backend.CacheProgressHandler` implementation.
    """
    def __init__(self, host_window, progressbar, status, parent, ui):
        self._parent = parent
        self._window = host_window
        self._status = status
        self._progressbar = progressbar
        self._ui = ui
        self._window.realize()
        host_window.window.set_functions(gtk.gdk.FUNC_MOVE)
        self._window.set_transient_for(parent)
        LOG.debug('GtkOpProgress initialized.')

    def cache_begin(self):
        """ Begin handler """
        def update_func():
            self._parent.set_sensitive(False)
            self._window.show()
            LOG.debug('Cache loading begin.')
        gobject.idle_add(update_func)

    def cache_finished(self):
        """ Finished handler """
        def update_func():
            self._parent.set_sensitive(True)
            self._window.hide()
            if self._ui._application.get_option('run_check'):
                LOG.debug('Checking for updates requested via commandline' +
                          ' switch.')
                self._ui._application.set_option('run_check', False)
                self._ui._application.reload_package_list()
            else:
                self._ui.update_package_list()
        LOG.debug('Cache loading finished.')
        gobject.idle_add(update_func)

    def cache_operation(self, operation):
        def update_func():
            self._status.set_markup("<i>%s</i>" % operation)
        gobject.idle_add(update_func)

    def cache_update(self, progress):
        def update_func():
            self._progressbar.set_fraction(float(progress)/100.0)
        gobject.idle_add(update_func)

class BackendProgressHandlerObject(CommitProgressHandler, ListProgressHandler,
                                   gobject.GObject):
    """ Helper class that transfers CommitProgressHandler calls to glib signals
    and emits them """

    __gsignals__ = {
        'preparation_begin': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'requires_removal_or_installation': (gobject.SIGNAL_RUN_LAST,
                                             gobject.TYPE_NONE,
                                             [gobject.TYPE_PYOBJECT,
                                              gobject.TYPE_PYOBJECT]),
        'download_begin': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                           [gobject.TYPE_INT, gobject.TYPE_INT,
                            gobject.TYPE_INT]),
        'download_update': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            [gobject.TYPE_INT, gobject.TYPE_INT,
                             gobject.TYPE_INT]),
        'download_finished': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'download_aborted': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'download_failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            [gobject.TYPE_STRING,]),
        'download_item_finished': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                   [gobject.TYPE_STRING,]),
        'download_item_update': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                 [gobject.TYPE_STRING, gobject.TYPE_INT,
                                  gobject.TYPE_INT]),
        'install_begin': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'install_finished': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'install_failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                           [gobject.TYPE_STRING]),
        'install_update': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                           [gobject.TYPE_STRING, gobject.TYPE_INT,
                            gobject.TYPE_STRING]),
        'list_begin': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'list_finished': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'list_aborted': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'list_failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                        [gobject.TYPE_STRING]),
        'list_update': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                        [gobject.TYPE_INT, gobject.TYPE_INT]),
        'list_item_update': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                             [gobject.TYPE_STRING, gobject.TYPE_INT,
                              gobject.TYPE_INT]),
        'list_item_finished': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                               [gobject.TYPE_STRING]),
        }

    def __init__(self):
        gobject.GObject.__init__(self)
        self._removal_answer = False
        self._removal_event = threading.Event()

    def emit(self, *args):
        """ Emits signal in main thread, using gobject.idle_add.
        
        :param args: Arguments passed to gobject.Gobject.emit
        """
        gobject.idle_add(gobject.GObject.emit, self, *args)

    def preparation_begin(self):
        """ 
        :meth:`UpdateManager.Backend.CommitProgressHandler.preparation_begins`
        implementation.
        
        .. versionadded:: 0.200.0~exp1
        """
        self.emit('preparation_begin')

    def requires_removal_or_installation(self, removals, installs):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.requires_removal_or_installation`
        implementation.

        This method uses a threading.Event object internally and blocks until
        the event is set. This is done by the
        :meth:`answer_removal_or_installation` method.

        .. versionadded:: 0.200.0~exp1.
        """
        self._removal_event.clear()
        self.emit('requires_removal_or_installation', removals, installs)
        self._removal_event.wait()
        self._removal_event.clear()
        return self._removal_answer

    def answer_removal_or_installation(self, answer):
        """ Method for answering a previous emission of the
        requires_removal_or_installation event.

        :param answer: Answer (bool)

        .. versionadded:: 0.200.0~exp1
        """
        self._removal_answer = answer
        self._removal_event.set()
        
    def download_begin(self, download_size, package_count, download_count):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.download_begin`
        implementation.
        """
        self.emit('download_begin', download_size, package_count,
                  download_count)

    def download_update(self, download_speed, eta_seconds, percent):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.download_update`
        implementation.
        """
        self.emit('download_update', download_speed, eta_seconds, percent)

    def download_finished(self):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.download_finished`
        implementation.
        """
        self.emit('download_finished')

    def download_aborted(self):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.download_aborted`
        implementation.
        """
        self.emit('download_aborted')

    def download_failed(self, failure_message):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.download_failed`
        implementation.
        """
        self.emit('download_failed', failure_message)

    def download_item_begin(self, uri, item_size, downloaded_size):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.download_item_begin`
        implementation.
        """
        self.download_item_update(uri, item_size, downloaded_size)

    def download_item_update(self, uri, item_size, downloaded_size):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.download_item_update`
        implementation.
        """
        self.emit('download_item_update', uri, item_size, downloaded_size)

    def download_item_finished(self, uri):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.download_item_finished`
        implementation.
        """
        self.emit('download_item_finished', uri)

    def install_begin(self):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.install_begin`
        implementation.
        """
        self.emit('install_begin')

    def install_update(self, package_name, percent, status_message):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.install_update`
        implementation.
        """
        self.emit('install_update', package_name, percent, status_message)

    def install_finished(self):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.install_finished`
        implementation.
        """
        self.emit('install_finished')

    def install_failed(self, error_message):
        """
        :meth:`UpdateManager.Backend.CommitProgressHandler.install_failed`
        implementation.
        """
        self.emit('install_failed', error_message)

    def list_item_begin(self, item_uri, item_size, item_partial_size):
        """ List item begin handler

        :param item_uri: Item URI
        :param item_size: Item size in bytes
        :param item_partial_size: Number of bytes already downloaded
        """
        self.emit('list_item_update', item_uri, item_size, item_partial_size)

    def list_item_update(self, item_uri, item_size, item_partial_size):
        """ List item update handler

        :param item_uri: Item URI
        :param item_size: Item size in bytes
        :param item_partial_size: Number of bytes already downloaded
        """
        self.emit('list_item_update', item_uri, item_size, item_partial_size)

    def list_item_finished(self, item_uri):
        """ List item finished handler
        
        :param item_uri: Item URI
        """
        self.emit('list_item_finished', item_uri)

    def list_begin(self):
        """ List download begin handler """
        self.emit('list_begin')

    def list_finished(self):
        """ List download finished handler """
        self.emit('list_finished')

    def list_aborted(self):
        """ List download aborted handler """
        self.emit('list_aborted')

    def list_failed(self, failure_message):
        """ List download failed handler """
        self.emit('list_failed', failure_message)

    def list_update(self, download_speed, eta_seconds, percent_done):
        """ List status update handler

        :param download_speed: Current download speed
        :param eta_seconds: Current ETA
        :param percent_done: Current percent done
        """
        self.emit('list_update', int(download_speed), int(eta_seconds))

class GtkListProgress(BackendProgressHandlerObject):
    """ Gtk list progress handler implementation """
    LIST_COL = Enum('PERCENTAGE', 'SOURCE', 'FILE_NAME', 'PART_SIZE',
                    'FILE_SIZE')
    MODE = Enum(UNKNOWN="Unknown mode", DOWNLOAD_PKG="Package download mode",
                DOWNLOAD_LIST="List download mode", HIDDEN="Hidden mode",
                INSTALL="Install mode",
                INSTALL_FINISHED="Install finished mode")
    
    def __init__(self, host_window, progressbar, summary, status, expander,
                 cancel_button, treeview, vb_details, scrolled, parent):
        BackendProgressHandlerObject.__init__(self)
        self._mode = self.MODE.HIDDEN
        self._scrolled = scrolled
        self._summary = summary
        self._progressbar = progressbar
        self._status = status
        self._parent = parent
        self._treeview = treeview
        self._expander = expander
        self._vb_details = vb_details
        self._cancel_button = cancel_button
        self._window = host_window
        self._store = gtk.ListStore(int, str, str, int, int)
        self._treeview.set_model(self._store)
        self._treeview.set_headers_clickable(False)
        self._download_size = 0
        self._package_count = 0
        self._download_count = 0
        self._packages_finished = 0
        self._installed_count = 0
        self._cur_install_package = None
        
        self._expander.connect("notify::expanded", self._expander_toggled)

        # List columns
        progress_renderer = gtk.CellRendererProgress()
        column_progress = gtk.TreeViewColumn(_("Progress"), progress_renderer)
        column_progress.set_cell_data_func(progress_renderer,
                                           self._progress_col_data_func)
        column_source = gtk.TreeViewColumn(_("Source"), gtk.CellRendererText(),
                                           markup=self.LIST_COL.SOURCE)
        column_file = gtk.TreeViewColumn(_("File name"),
                                         gtk.CellRendererText(),
                                         markup=self.LIST_COL.FILE_NAME)
        partial_renderer = gtk.CellRendererText()
        column_partial = gtk.TreeViewColumn(_("Downloaded"),
                                            partial_renderer)
        column_partial.set_cell_data_func(partial_renderer,
                                          self._partial_col_data_func)

        size_renderer = gtk.CellRendererText()
        column_size = gtk.TreeViewColumn(_("Size"), size_renderer)
        column_size.set_cell_data_func(size_renderer, self._size_col_data_func)
        
        self._treeview.append_column(column_progress)
        self._treeview.append_column(column_source)
        self._treeview.append_column(column_file)
        self._treeview.append_column(column_partial)
        self._treeview.append_column(column_size)

        self._window.set_title(_('Checking for updates'))
        self._status.set_markup('')
        
        self._window.realize()
        self._window.window.set_functions(
            gtk.gdk.FUNC_MOVE|gtk.gdk.FUNC_RESIZE)
        self._window.set_transient_for(parent.window_main)
        self._finish_event = threading.Event()
        self._finish_event.clear()
        self._store_map = {}
        self._terminal = vte.Terminal()
        self._current_items = {}

        # Connect list signals
        self.connect("list_begin", self._sig_list_begin)
        self.connect("list_finished", self._sig_list_finished)
        self.connect("list_aborted", self._sig_list_aborted)
        self.connect("list_failed", self._sig_list_failed)
        self.connect("list_update", self._sig_list_update)
        self.connect("list_item_update", self._sig_item_update)
        self.connect("list_item_finished", self._sig_item_finished)

        # Connect download signals
        self.connect('download_begin', self._sig_download_begin)
        self.connect('download_update', self._sig_download_update)
        self.connect('download_finished', self._sig_download_finished)
        self.connect('download_aborted', self._sig_download_aborted)
        self.connect('download_failed', self._sig_download_failed)
        self.connect('download_item_finished', self._sig_item_finished)
        self.connect('download_item_update', self._sig_item_update)

        # Connect install signals
        self.connect('preparation_begin', self._sig_preparation_begin)
        self.connect('requires_removal_or_installation',
                     self._sig_removal_or_install)
        self.connect('install_begin', self._sig_install_begin)
        self.connect('install_finished', self._sig_install_finished)
        self.connect('install_failed', self._sig_install_failed)
        self.connect('install_update', self._sig_install_update)

        self._cancel_button.connect("clicked", self._sig_cancel_clicked)
        self._change_mode(reload_cache=False)
        
        
    def _partial_col_data_func(self, cell_layout, renderer, model, iterator):
        """ Column data function for partial size column """
        part_size = self._store.get_value(iterator, self.LIST_COL.PART_SIZE)
        if part_size != 0:
            size_str = humanize_size(part_size)
        else:
            size_str = _("Unknown")
        renderer.set_property("text", size_str)

    def _progress_col_data_func(self, cell_layout, renderer, model, iterator):
        """ Column data function for progress column """
        percentage = self._store.get_value(iterator, self.LIST_COL.PERCENTAGE)
        renderer.set_property("value", percentage)
        renderer.set_property("text", '%.0f%%' % (percentage))

    def _size_col_data_func(self, cell_layout, renderer, model, iterator):
        """ Data function for the size column.

        Invokes :func:`humanize_size` if the file size is known for
        a row and shows the result of the function call.
        """
        file_size = self._store.get_value(iterator, self.LIST_COL.FILE_SIZE)
        if file_size != 0:
            size_str = humanize_size(file_size)
        else:
            size_str = _("Unknown")
        renderer.set_property("text", size_str)

    def _expander_toggled(self, expander, data):
        """ Expander toggle handler """
        expanded = self._expander.get_expanded()

        self._vb_details.set_child_packing(self._expander, expanded,
                                           expanded, 0, gtk.PACK_END)

    def _set_status(self, time_remaining, download_speed=None):
        """ Status label setter function
        
        :param time_remaining: Time remaining in seconds (integer)
        :param download_speed: Current download speed in bytes per second.
        """
        text = ''
        if download_speed:
            # TRANSLATORS: This is the download rate in bytes, kilobytes
            # or megabytes per second (hence the trailing /s).
            text = _('Download rate: %s/s') % (humanize_size(download_speed))
            
        if time_remaining:
            if time_remaining < 5:
                text += '\n' + ('Less than 5 seconds remaining')
            else:
                eta_string = humanize_seconds(time_remaining)
                text += '\n' + ('About %s remaining') % (eta_string)

        self._status.set_markup(text)
        
    def _sig_cancel_clicked(self, widget):
        """ Cancel button click signal handler """
        if self._cancel_button.get_label() == 'gtk-close':
            self._mode = self.MODE.HIDDEN
            self._cancel_button.set_label('gtk-cancel')

            def reload_cache_helper():
                self._parent._application.reload_cache()
            
            gobject.idle_add(reload_cache_helper)
            self._change_mode()
            self._terminal.reset(True, True)
        else:
            self._parent._application.abort_operation()

    def _sig_list_begin(self, src):
        """ List begin signal handler """
        self._mode = self.MODE.DOWNLOAD_LIST
        self._set_status(0)
        self._summary.set_markup('<b>%s</b>' % _('Checking for updates...'))
        self._progressbar.set_text('')
        self._progressbar.pulse()
        self._finish_event.clear()
        self._store.clear()
        self._change_mode()
        gobject.timeout_add(150, self._pulsate,
                            priority=gobject.PRIORITY_DEFAULT_IDLE)

    @classmethod
    def _is_remote_uri(cls, item_uri):
        """ Helper classmethod that checks whether a given URI is remote or
        local.

        :param item_uri: Item URI
        """
        if item_uri.startswith('gpgv:/') or item_uri.startswith('bzip2:/') \
               or item_uri.startswith('gzip:/') \
               or item_uri.startswith('rred:/'):
            return False
        return True
    
    def _sig_list_finished(self, src):
        """ List finished signal handler """
        self._mode = self.MODE.HIDDEN
        self._change_mode()
        self._finish_event.set()
        self._store.clear()
        self._store_map = {}
        self._current_items = {}

    def _sig_list_aborted(self, src):
        """ List aborted signal handler """
        self._sig_list_finished(src)

    def _sig_list_failed(self, src, message):
        """ List failed signal handler """
        md = gtk.MessageDialog(parent=self._window,
                               flags=gtk.DIALOG_MODAL,
                               type=gtk.MESSAGE_ERROR,
                               buttons=gtk.BUTTONS_OK)
        md.set_markup("<b>%s</b>" %\
                      _("An internal error has occured and the operation has been aborted."))

        md.format_secondary_markup("<b>%s</b>\n%s" %\
                                   (_("Error message:"),
                                    message))
        md.run()
        md.hide()
        md.unrealize()
        self._sig_list_finished(src)

    def _sig_list_update(self, src, download_speed, eta_seconds):
        """ List update signal handler
        :param download_speed: Current download speed
        :param eta_seconds: ETA
        """
        self._set_status(eta_seconds, download_speed)

    def _sig_item_update(self, src, item_uri, item_size,
                             item_partial_size):
        """ List item update signal handler

        :param item_uri: Item URI
        :param item_size: File size in bytes
        :param item_partial_size: Number of bytes already downloaded
        """
        self._handle_first_download_item()
        if item_size:
            percent = int(float(item_partial_size)/item_size*100)
            self._current_items[item_uri] = percent
        else:
            percent = 0
            
        if self._is_remote_uri(item_uri): 
            if not item_uri in self._store_map:
                try:
                    uri_source, uri_file = item_uri.rsplit('/', 1)
                    if uri_file.endswith('Release') or \
                       uri_file.endswith('Release.gpg') or \
                       uri_file.endswith('Index'):
                        return False
                    uri_source += '/'
                    it = self._store.prepend([percent, uri_source, uri_file,
                                              item_partial_size, item_size])
                    self._store_map[item_uri] = it
                except ValueError, v_err:
                    LOG.debug('Splitting uri %s failed: %s', item_uri,
                              v_err.message)
            else:
                it = self._store_map[item_uri]
                percent_old = self._store.get_value(it,
                                                    self.LIST_COL.PERCENTAGE)
                if percent_old < percent:
                    self._store.set_value(it, self.LIST_COL.PERCENTAGE,
                                          percent)
                    self._store.set_value(it, self.LIST_COL.PART_SIZE,
                                          item_partial_size)
                    self._store.set_value(it, self.LIST_COL.FILE_SIZE,
                                          item_size)
            self._update_percent()
        else:
            # Local URI means remote side has finished, let's try to find
            # the matching remote uri.
            try:
                remote_uri_part = item_uri.rsplit('/', 1)[1].replace('_', '/')
                remote_uri_part2 = remote_uri_part + '.bz2'
            except ValueError, v_err:
                LOG.debug('Splitting uri %s failed: %s', item_uri, v_err)
                return False
            
            for uri in self._store_map:
                try:
                    proto, uri_part = uri.rsplit('//', 1)
                    if uri_part == remote_uri_part or \
                           uri_part == remote_uri_part2:
                        it = self._store_map[uri]
                        percent = self._store.get_value(
                            it, self.LIST_COL.PERCENTAGE)
                        if percent < 100:
                            self._store.set_value(
                                it, self.LIST_COL.PERCENTAGE, 100)
                            size = self._store.get_value(
                                it, self.LIST_COL.FILE_SIZE)
                            self._store.set_value(
                                it, self.LIST_COL.PART_SIZE, size)
                        break
                except ValueError, v_err:
                    LOG.debug('Could not split uri %s: %s', uri, v_err.message)
                
        return False

    def _sig_item_finished(self, src, item_uri):
        """ Item finished signal handler

        :param item_uri: Item URI
        """
        if not self._is_remote_uri(item_uri):
            return

        
        self._handle_first_download_item()
        if item_uri in self._current_items:
            del self._current_items[item_uri]
            
        if item_uri in self._store_map:
            it = self._store_map[item_uri]
            size = self._store.get_value(it, self.LIST_COL.FILE_SIZE)
            self._store.set_value(it, self.LIST_COL.PART_SIZE, size)
            self._store.set_value(it, self.LIST_COL.PERCENTAGE, 100)
        else:
            try:
                uri_source, uri_file = item_uri.rsplit('/', 1)
                uri_source += '/'
                it = self._store.prepend([100, uri_source, uri_file, 0, 0])
                self._store_map[item_uri] = it
            except ValueError, v_err:
                LOG.debug('Splitting uri %s failed: %s', item_uri,
                          v_err)
                
        if self._mode == self.MODE.DOWNLOAD_PKG:
            self._packages_finished += 1
        
        return False
    
    def _pulsate(self):
        """ Pulsate helper method """
        if self._progressbar.get_text() != '':
            self._progressbar.set_text('')
        self._progressbar.pulse()

        if self._finish_event.isSet():
            self._progressbar.set_fraction(0.0)

        if self._finish_event.isSet() and self._mode == self.MODE.DOWNLOAD_PKG:
            self._update_percent()
        
        return not self._finish_event.isSet()

    def _update_percent(self, package_percent=0):
        """ Helper method that updates the done percentage for
        commit operations
        """
        pct = 0.0
        if self._mode == self.MODE.DOWNLOAD_PKG:
            pct = (float(self._packages_finished)/ \
                   self._download_count)
            for uri in self._current_items.keys():
                item_percent = self._current_items[uri]
                pct += (float(item_percent)/100)/self._download_count
        elif self._mode == self.MODE.DOWNLOAD_LIST:
            # In list download mode we *have* to ignore this as updating
            # the progress bar whilst pulsating looks ugly and makes
            # pulsating useless.
            return False
        else:
            pct = float(package_percent)/100

        self._progressbar.set_fraction(pct)
        self._progressbar.set_text('%.0f%%' % (pct*100))

    def _handle_first_download_item(self):
        """ Helper method that updates the UI after we get information
        on our first download item
        """
        if not self._finish_event.isSet() \
               and self._mode == self.MODE.DOWNLOAD_PKG:
            self._finish_event.set()
            self._summary.set_markup('<b>%s</b>' % _('Downloading updates'))
            self._status.set_markup('')

    def _sig_removal_or_install(self, src, removals, installs):
        """ Handler for the requires_removal_or_installation signal

        .. versionadded:: 0.200.0~exp1
        """

        # We first need to create the store and treeview
        store = gtk.ListStore(str)
        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        treeview = gtk.TreeView()
        treeview.set_headers_visible(False)
        treeview.set_model(store)
        treeview.set_sensitive(False)
        renderer = gtk.CellRendererText()
        column_changes = gtk.TreeViewColumn(_("Changes"), renderer, markup=0)
        treeview.append_column(column_changes)

        for pkg_info in removals:
            ### TRANSLATORS: This is an entry in the package removal or
            # new installation dialog's changes list.      
            store.append(["<b>%s</b>" % _('Remove %s') \
                          % (pkg_info.get_package_name())])

        for pkg_info in installs:
            ### TRANSLATORS: This is an entry in the package removal or
            # new installation dialog's changes list.
            store.append(["<b>%s</b>" % _('Install %s') \
                          % (pkg_info.get_package_name())])

        # ... and now the dialog
        dialog_title = _("Removal or installation of packages")
        dialog = gtk.Dialog(parent=self._window, title=dialog_title,
                            flags=gtk.DIALOG_MODAL, buttons=(gtk.STOCK_YES,
                                                             gtk.RESPONSE_YES,
                                                             gtk.STOCK_NO,
                                                             gtk.RESPONSE_NO))

        label = gtk.Label()
        label.set_markup("%s\n%s\n\n%s\n" \
                         % (_("Installation of the selected upgrades requires removal or installation of new packages."),
                            _("You can find a list of these changes below."),
                            _("Do you want to continue?")))

        content_area = dialog.get_content_area()
        content_area.add(label)
        scrolled.add(treeview)
        content_area.add(scrolled)
        
        dialog.show_all()
        res = dialog.run()
        dialog.hide_all()
        if res == gtk.RESPONSE_YES:
            self.answer_removal_or_installation(True)
        else:
            self.answer_removal_or_installation(False)
            self._mode = self.MODE.HIDDEN
            self._change_mode()

    def _sig_preparation_begin(self, src):
        """ Commit preparation begin handler
        
        .. versionadded:: 0.200.0~exp1
        """
        self._window.set_title(_('Preparing upgrade'))
        self._mode = self.MODE.DOWNLOAD_PKG
        self._finish_event.clear()
        self._summary.set_markup('<b>%s</b>' % _('Preparing upgrade'))
        self._status.set_markup(_('This operation may take some time.'))
        self._progressbar.set_fraction(0.0)
        self._progressbar.pulse()
        gobject.timeout_add(150, self._pulsate,
                            priority=gobject.PRIORITY_DEFAULT_IDLE)
        self._change_mode()
        
    def _sig_download_begin(self, src, download_size, package_count,
                           download_count):
        """ Download begin handler

        :param download_size: Overall download size in bytes
        :param package_count: Number of packages to be downloaded
        """
        self._window.set_title(_('Preparing upgrade'))
        self._download_size = download_size
        self._download_count = download_count
        self._package_count = package_count
        self._packages_finished = 0
        self._install_percent = 0
        self._change_mode()
        
    def _sig_download_finished(self, src):
        """ Download finished handler

        :param src: Source
        """
        self._packages_finished = self._package_count
        self._summary.set_markup('<b>%s</b>' % _('Downloading finished'))
        self._status.set_markup('')
        self._finish_event.clear()
        self._progressbar.set_fraction(0.0)
        gobject.timeout_add(150, self._pulsate,
                            priority=gobject.PRIORITY_DEFAULT_IDLE)
        self._store.clear()
        self._mode = self.MODE.INSTALL
        self._change_mode()

    def _sig_download_failed(self, src, failure_message):
        """ Download failed handler

        :param src: Source
        :param failure_message: Failure message
        """
        md = gtk.MessageDialog(parent=self._window,
                               flags=gtk.DIALOG_MODAL,
                               type=gtk.MESSAGE_ERROR,
                               buttons=gtk.BUTTONS_OK)
        md.set_markup("<b>%s</b>" %\
                      _("An error has occured and downloading has been aborted."))

        md.format_secondary_markup("<b>%s</b>\n%s" %\
                                   (_("Error message:"),
                                    failure_message))
        md.run()
        md.hide()
        md.unrealize()
        self._mode = self.MODE.HIDDEN
        self._change_mode()

    def _sig_download_update(self, src, download_speed, eta_seconds, percent):
        """ Download update handler

        :param src: Source
        :param download_speed: Overall download speed
        :param eta_seconds: ETA for download to finish, in seconds.
        :param percent: Overall percentage done.
        """
        self._set_status(eta_seconds, download_speed)

    def _sig_install_begin(self, src):
        """ Install begin handler

        :param src: Source
        """
        self._installed_count = 0
        self._window.set_title(_('Installing updates'))
        self._summary.set_markup('<b>%s</b>' % _('Preparing installation...'))
        self._status.set_markup('')
        self._update_percent()
        self._progressbar.set_fraction(0.0)
        self._mode = self.MODE.INSTALL
        self._change_mode()

    def _sig_install_update(self, src, package_name, percent, status_message):
        """ Install update handler

        :param src: Source
        :param package_name: The current package's name
        :param percent: Overall percent done
        :param status_message: Status message string
        """
        if self._cur_install_package != package_name \
               and not 'trigger' in status_message \
               and not 'dpkg-exec' in status_message:
            # This might need adjusting to work with i18n!
            self._installed_count += 1
            self._cur_install_package = package_name
            
        self._status.set_markup('<i>%s</i>' % (status_message))
        self._update_percent(percent)
        self._cancel_button.set_sensitive(False)
        self._finish_event.set()

    def _sig_install_finished(self, src):
        """ Install finished handler

        :param src: Source
        """
        self._mode = self.MODE.INSTALL_FINISHED
        self._change_mode()
        summary_txt = ngettext('Applied %d update', 'Applied %d updates',
                               self._package_count) \
                               % (self._package_count)
        self._summary.set_markup('<big><b>%s</b></big>' \
                                 % (summary_txt))
        update_count = self._parent.update_list.store_get_update_count()
        updates_remaining = update_count - self._package_count
        if updates_remaining == 0:
            self._status.set_markup(_('Your system is now up-to-date.'))
        else:
            text = ngettext('There is %d more update available.',
                            'There are %d more updates available.',
                            updates_remaining) % (updates_remaining)
            text += '\n<i>'
            text +=  _('Software updates correct errors and eliminate security vulnerabilities.')
            text += '\n' + _('Please consider installing all available updates.')
            text += '</i>'
            self._status.set_markup(text)
        self._cancel_button.set_label('gtk-close')
        self._cancel_button.set_sensitive(True)

    def _sig_install_failed(self, src, error_message):
        """ Install failed handler

        :param src: Source
        :param error_message: Error message string
        """
        md = gtk.MessageDialog(parent=self._window,
                               flags=gtk.DIALOG_MODAL,
                               type=gtk.MESSAGE_ERROR,
                               buttons=gtk.BUTTONS_OK)
        md.set_markup("<b>%s</b>" %\
                      _("An error has occured and installing has been aborted."))

        md.format_secondary_markup("<b>%s</b>\n%s" %\
                                   (_("Error message:"),
                                    error_message))             
        md.run()
        md.hide()
        md.unrealize()
        self._mode = self.MODE.HIDDEN
        self._change_mode()
         
    def _sig_download_aborted(self, src):
        """ Download abort handler

        :param src: Source
        """
        # When aborting the operation we simply hide the window for now.
        self._mode = self.MODE.HIDDEN
        self._change_mode()
        gobject.idle_add(self._parent.update_package_list)

    def _change_mode(self, reload_cache=True):
        """ Display mode changing helper.

        This method uses the value in self._mode to switch to a new display
        mode.

        It is responsible for hiding/showing widgets and setting the UI up
        correctly.

        :param reload_cache: Defines whether to reload the cache or not.
        """
        self._parent.window_main.set_sensitive(False)
        if self._mode in [self.MODE.DOWNLOAD_LIST, self.MODE.DOWNLOAD_PKG]:
            self._current_items = {}
            self._store_map = {}
            LOG.debug('Changing to download mode.')
            self._expander.set_label(_('Show progress of individual files'))
            self._show_widgets('expander', 'treeview', 'progressbar',
                               'summary', 'status', 'window')
            
            self._hide_widgets('terminal')
            self._treeview.columns_autosize()
            if self._terminal.is_ancestor(self._scrolled):
                self._scrolled.remove(self._terminal)
            if not self._treeview.is_ancestor(self._scrolled):
                self._scrolled.add(self._treeview)
        elif self._mode == self.MODE.INSTALL:
            self._current_items = {}
            self._store_map = {}
            self._expander.set_label(_('Show terminal'))
            self._summary.set_markup('<b>%s</b>'  % _('Installing updates'))
            LOG.debug('Changing to install mode')
            self._show_widgets('expander', 'terminal', 'progressbar',
                               'summary', 'status', 'window')
            
            self._hide_widgets('treeview')
            if self._treeview.is_ancestor(self._scrolled):
                self._scrolled.remove(self._treeview)
            if not self._terminal.is_ancestor(self._scrolled):
                self._scrolled.add(self._terminal)
            self._cancel_button.set_sensitive(False)
        elif self._mode == self.MODE.INSTALL_FINISHED:
            self._current_items = {}
            self._store_map = {}
            self._expander.set_label(_('Show terminal'))
            LOG.debug('Changing to install finished mode.')
            self._show_widgets('expander', 'terminal', 'progressbar',
                               'summary', 'status', 'window')
            
            self._hide_widgets('treeview', 'progressbar')
            self._cancel_button.set_sensitive(True)
        elif self._mode == self.MODE.HIDDEN:
            self._current_items = {}
            self._store_map = {}
            LOG.debug('Changing to hidden mode.')
            self._hide_widgets('treeview', 'progressbar', 'terminal',
                               'expander', 'progressbar', 'summary', 'status',
                               'window')
            if self._terminal.is_ancestor(self._scrolled):
                self._scrolled.remove(self._terminal)
            if not self._treeview.is_ancestor(self._scrolled):
                self._scrolled.add(self._treeview)
            self._parent.window_main.set_sensitive(True)
            self._store.clear()

            # Schedule cache reloading, so the main window's treeview
            # gets updated.
            def reload_cache_helper():
                self._parent._application.reload_cache()
                return False
            if reload_cache:
                gobject.idle_add(reload_cache_helper)
                                            
        else:
            LOG.debug('Unknown mode: %d', self._mode)
    

    def _hide_widgets(self, *widget_list):
        """ Widget hiding helper.

        Takes names of widgets to hide as argument(s), tries to
        get the self._<widget_name> attribute and calls the hide method
        on the returned widget.

        :param *widget_list: Names of widgets to hide
        """
        for widget_name in widget_list:
            widget = getattr(self, '_' + widget_name, None)
            if not widget:
                LOG.fatal('Widget %s not found.', widget_name)
                continue
            widget.hide()

    def _show_widgets(self, *widget_list):
        """ Widget showing helper.

        Takes names of widgets to show as argument(s), tries to
        get the self._<widget_name> attribute and calls the show method
        on the returned widget.

        :param *widget_list: Names of widgets to show
        """
        for widget_name in widget_list:
            widget = getattr(self, '_' + widget_name, None)
            if not widget:
                LOG.fatal('Widget %s not found.', widget_name)
                continue
            widget.show()

    def get_terminal_fork_func(self):
        """ Returns the terminal's fork function """
        return self._terminal.forkpty        
                         
        
