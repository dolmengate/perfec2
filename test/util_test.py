import unittest
from undecorated import undecorated
from unittest import mock
from unittest.mock import Mock, PropertyMock

from javalang.tokenizer import Position
from javalang.tree import CompilationUnit, FieldDeclaration

import swap


class TestAddFieldAnnotation(unittest.TestCase):

    def setUp(self) -> None:
        self.testee = undecorated(swap.add_field_annotation)

    def test_happy(self):
        position = PropertyMock()
        position.line = 2
        field = Mock()
        type(field).position = position

        lines = ['one\n', '    two\n', '    three\n', 'four\n']
        anno = 'hello'

        actual = self.testee(field, anno, lines)

        position.assert_called_once_with()
        self.assertTrue(len(lines) == 5, 'Lines didnt increase')
        self.assertTrue(lines[1] == '@hello', 'Annotation is not on the expected line')
        # todo assert returned lines
        # todo tabbing


class TestFindTestee(unittest.TestCase):

    def setUp(self) -> None:
        self.testee = undecorated(swap.find_testee)

    @mock.patch('swap.util.util')
    def test_happy(self, util):
        clazz = Mock()
        fields = PropertyMock()
        decl_name = PropertyMock()
        clazz_name = PropertyMock()

        declr = Mock()
        type(declr).name = decl_name

        type(clazz).name = clazz_name
        type(clazz).fields = fields
        type(clazz).declarators = [declr]

        util.field_has_name.side_effect = [False, False, True]
        util.field_has_anno.side_effect = [False, False, False]

        type(clazz).fields = fields




# mock a dependency method call

# @mock.patch.object(RemovalService, 'rm')
# def test_upload_complete(self, mock_rm):


# mock.create_autospec(RemovalService) what about with req. constructor args?

# class ExampleTest(unittest.TestCase):
#
#     @mock.patch('testee_module.dependency_module2')
#     @mock.patch('testee_module.dependency_module1')
#     @mock.patch.object(DependencyClass, 'class_method_name')
#     def testmethod(self, dependency_module1, dependency_module2):
#
#         dependency_module1.method_called_by_testee.return_value = 'desired return value'
#
#         testmethod()
#
#         self.assertFalse(dependency1.method_called_by_testee.called, "Method wasnt called")
#
#         # verify dependency method was called with certain args
#         dependency1.method_called_by_testee.assert_called_with('args that should have been used')
#


# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
#
# import os
# import os.path
#
# def rm(filename):
#     if os.path.isfile(filename):
#         os.remove(filename)

# from mymodule import rm
#
# import mock
# import unittest
#
#
# class RmTestCase(unittest.TestCase):
#
#     @mock.patch('mymodule.os.path')
#     @mock.patch('mymodule.os')
#     def test_rm(self, mock_os, mock_path):
#         # set up the mock
#         mock_path.isfile.return_value = False
#
#         rm("any path")
#
#         # test that the remove call was NOT called.
#         self.assertFalse(mock_os.remove.called, "Failed to not remove the file if not present.")
#
#         # make the file 'exist'
#         mock_path.isfile.return_value = True
#
#         rm("any path")
#
#         mock_os.remove.assert_called_with("any path")
