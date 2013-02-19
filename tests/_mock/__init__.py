# tests/_mock/__init__.py
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

import sys
import time

class MockCallInfo(object):
    def __init__(self, f, args=[], kwargs={}):
        self._f = f
        self._args = args
        self._kwargs = kwargs
        self._time = time.time()

    @property
    def tb_size(self):
        f = self._f
        i = 0
        while f:
            f = f.f_back
            i += 1
            
        return i

    @property
    def invocation_time(self):
        return self._time

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    def _nth_frame(self, n):
        f = self._f
        for i in range(0, n):
            f = f.f_back
        return f
    
    def get_filename(self, n=0):
        f = self._nth_frame(n)
        return tb.tb_frame.f_code.co_filename

    def get_lineno(self, n=0):
        f = self._nth_frame(n)
        return tb.tb_lineno

    def get_caller(self, n=0):
        f = self._nth_frame(n+1)
        return tb.tb_frame.f_code.co_name

    def get_instruction(self, n=0):
        f = self._nth_frame(n)
        return tb.tb_lasti

class MockCallHandler(object):
    def __init__(self, func_name):
        self._func_name = func_name
        self._call_info = []
        self._override = None

    def __call__(self, *args, **kwargs):
        f = sys._getframe()
        self._call_info.append(MockCallInfo(f, args=args, kwargs=kwargs))

        if self._override:
            return self._override(*args, **kwargs)

    @property
    def was_invoked(self):
        return len(self._call_info) > 0

    @property
    def invocation_count(self):
        return len(self._call_info)

    def get_last_info(self):
        return self._call_info[-1]

    def get_nth_info(self):
        return self._call_info[n]

    def set_override(self, override):
        self._override = override
        
class MockGenerator(object):
    def __init__(self, interface, *init_args, **init_kwargs):
        self._interface = interface
        self._call_hdlrs = {}
        self._init_args = init_args
        self._init_kwargs = init_kwargs
        self._cls = None
        self.__create_cls()

    @property
    def cls(self):
        return self._cls

    def __create_cls(self):
        gen = self
        init_args = gen._init_args
        init_kwargs = gen._init_kwargs
        iface = self._interface

        class MockImplementation(iface):
            def __init__(self, *args, **kwargs):
                iface.__init__(self, *init_args, **init_kwargs)
                self._gen = gen

                for func_name in dir(iface):
                    if not func_name.startswith('__') and \
                           callable(getattr(self, func_name)):
                        ch = MockCallHandler(func_name)
                        setattr(self, func_name, ch)
                        gen._call_hdlrs[func_name] = ch
                        # Support for method overriding.
                        override = getattr(gen, '_override__' + func_name,
                                           None)
                        if override and callable(override):
                            ch.set_override(override)

            def __repr__(self):
                return '<MockImplementation of %r>' % (self._gen._interface)
            
        self._cls = MockImplementation
        
    def get_call_handler(self, function_name):
        if function_name in self._call_hdlrs.keys():
            return self._call_hdrls[function_name]
        return None
