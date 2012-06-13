# UpdateManager/Frontend/Gtk/utils.py 
#  
#  Copyright (c) 2004-2009 Canonical
#                2009 Stephan Peijnik
#  
#  Author: Michael Vogt <mvo@debian.org>
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

""" Human-readable unit conversion utilities """
import locale
import logging

from gettext import gettext as _, ngettext

LOG = logging.getLogger('UpdateManager.Utils.humanize')

def humanize_size(num_bytes):
    """
    Convert a given size in bytes to a nicer better readable unit
    """
    if num_bytes == 0:
        # TRANSLATORS: download size is 0
        return _("0 KB")
    elif num_bytes < 1024:
        # TRANSLATORS: download size of very small updates
        return _("1 KB")
    elif num_bytes < 1024 * 1024:
        # TRANSLATORS: download size of small updates, e.g. "250 KB"
        return locale.format(_("%.0f KB"), float(num_bytes)/1024)
    else:
        # TRANSLATORS: download size of updates, e.g. "2.3 MB"
        return locale.format(_("%.1f MB"), float(num_bytes) / 1024 / 1024)

def humanize_seconds(seconds):
    """
    Convert a duration given in seconds to a human-readable string.

    :param seconds: Seconds as a string
    """
    if seconds < 5:
        return _("< 5 seconds")
    elif seconds < 60:
        return _("%d seconds") % (seconds)
    elif seconds < 3600:
        minutes = seconds/60
        secs = seconds%60
        min_string = ngettext("%d minute", "%d minutes", minutes) % (minutes)
        if secs > 0:
            secs_string = ' ' + ngettext('%d second',
                                         '%d seconds', secs) % (secs)
        else:
            secs_string = ''
        return min_string + secs_string
            
    # Fall-through to hours, minutes and seconds case.        
    hours = seconds/3600
    minutes = (seconds%3600)/60
    secs = seconds%60
    hours_string = ngettext('%d hour', '%d hours', hours) % (hours)
    if minutes > 0:
        minutes_string = ' ' + ngettext('%d minute', '%d minutes',
                                            minutes) % (minutes)
    else:
        minutes_string = ''
        
    if secs > 0:
        secs_string = ' ' + ngettext('%d second', '%d seconds',
                                         secs) % (secs)
    else:
        secs_string = ''

    return hours_string + minutes_string + secs_string
