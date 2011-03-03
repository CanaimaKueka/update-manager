# tests/Frontend/Util/humanize.py
#
#  Copyright (c) 2009 Stephan Peijnik
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
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import unittest

from gettext import gettext as _, ngettext
import locale

from UpdateManager.Util.humanize import humanize_size, humanize_seconds

loader = unittest.TestLoader()

class HumanizeSizeCase(unittest.TestCase):
    def test0_null_bytes(self):
        self.assertEquals(_("0 KB"), humanize_size(0))

    def test1_less_than_1024_bytes(self):
        for i in range(1, 1023):
            self.assertEquals(_("1 KB"), humanize_size(i))

    def test2_kilobytes(self):
        for i in range(1, 1023, 256):
            self.assertEquals(locale.format(_("%.0f KB"), i),
                              humanize_size(i*1024))

    def test3_megabytes(self):
        for i in range(1024, 1024*5, 256):
            self.assertEquals(locale.format(_("%.1f MB"), float(i)/1024),
                              humanize_size(1024*i))

HumanizeSizeSuite = loader.loadTestsFromTestCase(HumanizeSizeCase)


class HumanizeSecondsCase(unittest.TestCase):
    def test0_less_than5_seconds(self):
        for i in range(0, 5):
            self.assertEquals(humanize_seconds(i), _("< 5 seconds"))

    def test1_seconds(self):
        for i in range(5, 60):
            self.assertEquals(humanize_seconds(i), _("%d seconds") % (i))

    def test2_minutes(self):
        self.assertEquals(humanize_seconds(60), _("%d minute") % (1))
        for i in range(121, 3600, 7):
            mins = i/60
            secs = i%60
            mins_str = ngettext("%d minute", "%d minutes", mins) % (mins)
            if secs > 0:
                secs_str = ' ' + ngettext("%d second", "%d seconds",
                                          secs) % (secs)
            else:
                secs_str = ''
            self.assertEquals(humanize_seconds(i), mins_str + secs_str)

    def test3_hours(self):
        self.assertEquals(humanize_seconds(3600), _("%d hour") % (1))

        for i in range(7261, 10800, 1201):
            hours = i/3600
            mins = (i%3600)/60
            secs = i%60

            hours_str = ngettext("%d hour", "%d hours", hours) % (hours)

            if mins == 0:
                mins_str = ''
            else:
                mins_str = ' ' + ngettext("%d minute", "%d minutes", mins) \
                           % (mins)
                

            if secs == 0:
                secs_str = ''
            else:
                secs_str = ' ' + ngettext("%d second", "%d seconds", secs) \
                           % (secs)

            self.assertEquals(humanize_seconds(i), hours_str+mins_str+secs_str)
            

HumanizeSecondsSuite = loader.loadTestsFromTestCase(HumanizeSecondsCase)

HumanizeSuite = unittest.TestSuite([HumanizeSizeSuite,
                                    HumanizeSecondsSuite])
