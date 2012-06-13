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

""" Gtk Utitilies and Helpers """

import apt_pkg
import locale
import logging
import os
import sys
import threading
import urllib2

import gtk

from gettext import gettext as _

LOG = logging.getLogger('UpdateManager.Frontend.Gtk.utils')

def init_proxy(gconfclient=None):
    """ init proxy settings 
    
    * first check for http_proxy environment (always wins),
    * then check the apt.conf http proxy, 
    * then look into synaptics conffile
    * then into gconf  (if gconfclient was supplied)
    """
    synaptic_conf_file = "/root/.synaptic/synaptic.conf"
    proxy = None
    use_proxy = False
    # generic apt config wins
    apt_pkg.init_config()
    if apt_pkg.config.find("Acquire::http::Proxy") != '':
        proxy = apt_pkg.config.find("Acquire::http::Proxy")
        # then synaptic
    elif os.path.exists(synaptic_conf_file):
        cnf = apt_pkg.Configuration()
        apt_pkg.read_config_file(cnf, synaptic_conf_file)
        use_proxy = cnf.find_b("Synaptic::useProxy", False)
        
    if use_proxy:
        proxy_host = cnf.find("Synaptic::httpProxy")
        proxy_port = str(cnf.find_i("Synaptic::httpProxyPort"))
        if proxy_host and proxy_port:
            proxy = "http://%s:%s/" % (proxy_host, proxy_port)
    # then gconf
    elif gconfclient:
        try: # see LP: #281248
            host = None
            port = 0
            if gconfclient.get_bool("/system/http_proxy/use_http_proxy"):
                host = gconfclient.get_string("/system/http_proxy/host")
                port = gconfclient.get_int("/system/http_proxy/port")
                use_auth = gconfclient.get_bool("/system/http_proxy/"+\
                                                "use_authentication")
            if host and port:
                if use_auth:
                    auth_user = gconfclient.get_string("/system/http_proxy/"+\
                                                       "authentication_user")
                    auth_pw = gconfclient.get_string("/system/http_proxy/"+\
                                                     "authentication_password")
                    proxy = "http://%s:%s@%s:%s/" % (auth_user, auth_pw, host,
                                                     port)
                else:
                    proxy = "http://%s:%s/" % (host, port)
        except Exception, exc:
            sys.stdout.write("error from gconf: %s" % exc)
            sys.stdout.flush()
      
    # if we have a proxy, set it
    if proxy:
        # basic verification
        if not proxy.startswith("http://"):
            return
        proxy_support = urllib2.ProxyHandler({"http":proxy})
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)
        os.putenv("http_proxy", proxy)
