#!/usr/bin/env python

from distutils.core import setup, Extension
import glob
import os
from DistUtilsExtra.command import *

from UpdateManager import __version__

disabled = []

setup(name='update-manager',
      version=__version__,
      url="http://update-manager.alioth.debian.org",
      author="Stephan Peijnik",
      author_email="debian@sp.or.at",

      packages=[
                'UpdateManager',
                'UpdateManager.Frontend',
                'UpdateManager.Frontend.Gtk',
                'UpdateManager.Frontend.GtkCommon',
                'UpdateManager.Backend',
                'UpdateManager.DistSpecific',
                'UpdateManager.DistSpecific.Debian',
                'UpdateManager.DistSpecific.Ubuntu',
		'UpdateManager.DistSpecific.Canaima',
                'UpdateManager.Util'
                ],
      package_dir={
                   '': '.',
                  },
      scripts=[
               'update-manager', 
               'update-manager-text', 
               ],
      data_files=[
                  ('share/update-manager/ui',
                   glob.glob("data/ui/*.ui")
                  ),
                  ('share/update-manager/bug_script',
                   glob.glob("data/bug_script/*")
                  ),
                  ('share/man/man8',
                   glob.glob('data/*.8')
                  ),
                  ],
      cmdclass = { "build" : build_extra.build_extra,
                   "build_i18n" :  build_i18n.build_i18n,
                   "build_help" :  build_help.build_help,
                   "build_icons" :  build_icons.build_icons }
      )
