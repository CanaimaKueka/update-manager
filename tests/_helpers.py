# tests/_helpers.py
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

""" test helpers """

class ValidationError(Exception):
    """ Common validation error """
    pass

class NotSubclassError(ValidationError):
    """ Instance is not a subclass of given interface """
    def __init__(self, iface, inst):
        msg = '%s is not a subclass of %s, validation cannot be carried out' %\
            (inst.__name__, iface.__name__)
        ValidationError.__init__(self, msg)

class ValidationFailed(ValidationError):
    def __init__(self, ni_names, sig_names, typ_names):
        msg = 'VALIDATION FAILED\n\n'
        if len(ni_names):
            msg += 'not implemented   : %s\n\n' % ' '.join(ni_names)
        if len(sig_names):
            msg += 'signature mismatch: %s\n\n' % ' '.join(sig_names)
        if len(typ_names):
            msg += 'type mismatch     : %s\n\n' % ' '.join(typ_names)
        plural = ''
        error_count = len(ni_names) + len(sig_names) + len(typ_names)
        if error_count > 1:
            plural = 'S'
        msg += '%d ERROR%s FOUND' % (error_count, plural)
        ValidationError.__init__(self, msg)

class _InternalError(ValidationError):
    pass

class _NotImplementedError(_InternalError):
    pass

class _SignatureMismatch(_InternalError):
    pass

class _FunctionTypeMismatch(_InternalError):
    pass

class InterfaceValidator(object):
    """ Validates a given interface against an implementation """
    def __init__(self, interface, implementation):
        self._iface = interface
        self._impl = implementation

    @staticmethod
    def _validate_common(f_code, iface_code):
        if not InterfaceValidator._is_implemented(f_code):
            raise _NotImplementedError
        elif not InterfaceValidator._compare_signatures(f_code, iface_code):
            raise _SignatureMismatch

    @staticmethod
    def _compare_signatures(f_code, i_code):
        if f_code.co_argcount != i_code.co_argcount:
            return False
        return True

    def _validate_method(self, method_name, iface_code):
        """ Validates a single method """
        meth_code = self._get_method_code(getattr(self._impl, method_name))
        if not meth_code:
            raise _FunctionTypeMismatch

        InterfaceValidator._validate_common(meth_code, iface_code)

    def _validate_static(self, static_name, iface_code):
        """ Validates a single static method """
        static_code = self._get_static_code(getattr(self._impl, static_name))
        if not static_code:
            raise _FunctionTypeMismatch
        InterfaceValidator._validate_common(static_code, iface_code)

    @staticmethod
    def _is_implemented(f_code):
        """ Checks if a given function is implemented or only raises a
        NotImplementedError.
        """
        # Function used for comparing co_code
        def comparison_func():
            raise NotImplementedError
        if f_code.co_code == comparison_func.func_code.co_code:
            return False
        return True

    @staticmethod
    def _get_method_code(func_obj):
        """ Gets the func_code of a method """
        if callable(func_obj) and hasattr(func_obj, 'im_func'):
            return func_obj.im_func.func_code
        return None

    @staticmethod
    def _get_static_code(func_obj):
        """ Gets the func_code of a static method """
        if callable(func_obj) and not hasattr(func_obj, 'im_func'):
            return func_obj.func_code
        return None

    def validate(self):
        """ Validation logic """
        # Validation can only be carried out if _impl is a subclass/instance
        # of _iface.
        if not issubclass(self._impl, self._iface):
            raise NotSubclassError(self._iface, self._impl)

        # This function is used for checking if all mandatory methods of an 
        # interface have been implemented. Requires interface functions to
        # raise a NotImplementedError to work properly.
        def notimplemented(self):
            raise NotImplementedError

        # Find method names in interface and validate each one.
        not_implemented_names = []
        signature_mismatch_names = []
        type_mismatch_names = []
        for attr_name in dir(self._iface):
            attr = getattr(self._iface, attr_name)
            
            # All attributes starting with _ are considered private and
            # can be ignored.
            if attr_name[0] != '_' and callable(attr):
                # The attribute is callable, so it's likely a method
                meth = self._get_method_code(attr)
                static = self._get_static_code(attr)
                try:
                    if meth:
                        self._validate_method(attr_name, meth)
                    elif static:
                        self._validate_static(attr_name, static)

                except _NotImplementedError:
                    not_implemented_names.append(attr_name)
                except _SignatureMismatch:
                    signature_mismatch_names.append(attr_name)
                except _FunctionTypeMismatch:
                    type_mismatch_names.append(attr_name)
            
        if len(not_implemented_names) or len(signature_mismatch_names) or \
                len(type_mismatch_names):
            raise ValidationFailed(not_implemented_names, 
                                   signature_mismatch_names, 
                                   type_mismatch_names)
        


### UNIT TESTS for helpers

### mock interfaces and implementations
class TestIFace(object):
    def method(self, a, b):
        raise NotImplementedError

    @staticmethod
    def static(a, b):
        raise NotImplementedError

    def optional_method(self, a, b):
        pass

    @staticmethod
    def optional_static(a, b):
        pass

class CorrectImpl(TestIFace):
    def method(self, a, b):
        pass

    @staticmethod
    def static(a, b):
        pass

class CorrectImplWithOptional(CorrectImpl):
    def optional_method(self, a, b):
        pass

    @staticmethod
    def optional_static(a, b):
        pass

class CorrectBaseClass(TestIFace):
    pass

class IncorrectType0(TestIFace):
    @staticmethod
    def method(a, b):
        pass
    
    @staticmethod
    def static(a, b):
        pass

class IncorrectType1(TestIFace):
    def method(self, a, b):
        pass

    def static(self, a, b):
        pass

class IncorrectSignatureMethod(TestIFace):
    def method(self, a):
        pass

    @staticmethod
    def static(a, b):
        pass

class IncorrectSignatureStatic(TestIFace):
    def method(self, a, b):
        pass

    @staticmethod
    def static(a):
        pass

### the actual tests
import unittest

loader = unittest.TestLoader()

class InterfaceValidatorCase(unittest.TestCase):
    def test0_all_correct(self):
        try:
            InterfaceValidator(TestIFace, CorrectImpl).validate()
        except ValidationFailed, v_failed:
            self.fail('Validation of correct interface/implementation pair '+\
                          'failed:\n%s' % v_failed.message)

    def test1_all_correct_with_opt(self):
        try:
            InterfaceValidator(TestIFace, CorrectImplWithOptional).validate()
        except ValidationFailed, v_failed:
            self.fail('Validation of correct interface/implementation pair '+\
                          'failed:\n%s' % v_failed.message)

    def test2_incorrect_base_class(self):
        v = InterfaceValidator(TestIFace, object)
        self.assertRaises(NotSubclassError, v.validate)

    def test3_correct_base_class(self):
        v = InterfaceValidator(TestIFace, CorrectBaseClass)
        self.assertRaises(ValidationFailed, v.validate)

    def test4_incorrect_type(self):
        v = InterfaceValidator(TestIFace, IncorrectType0)
        self.assertRaises(ValidationFailed, v.validate)
        v = InterfaceValidator(TestIFace, IncorrectType1)
        self.assertRaises(ValidationFailed, v.validate)

    def test5_incorrect_signature(self):
        v = InterfaceValidator(TestIFace, IncorrectSignatureMethod)
        self.assertRaises(ValidationFailed, v.validate)
        v = InterfaceValidator(TestIFace, IncorrectSignatureStatic)
        self.assertRaises(ValidationFailed, v.validate)

InterfaceValidatorSuite = loader.loadTestsFromTestCase(InterfaceValidatorCase)
