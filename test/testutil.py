import unittest
from undecorated import undecorated
from unittest import mock

import perfec2

class Test__add_newline_if_not_empty(unittest.TestCase):

    def setUp(self) -> None:
        self.testee = undecorated(perfec2.util._add_newline_if_not_empty)

    def test_above(self):
        i = 2
        lines = ['one\n', '    two\n', '    three\n', 'four\n']

        self.testee(i, lines)
        self.assertEqual(['one\n', '    two\n', '\n', '    three\n', 'four\n'], lines,
                         "Expected and result don't match")

    def test_below(self):
        i = 2
        lines = ['one\n', '    two\n', '    three\n', 'four\n']

        self.testee(i, lines, pos='below')
        self.assertEqual(['one\n', '    two\n', '    three\n', '\n', 'four\n'], lines,
                         "Expected and result don't match")

    def test_above_newline_present(self):
        i = 2
        lines = ['one\n', '    two\n', '\n', 'four\n']

        self.testee(i, lines)
        self.assertEqual(['one\n', '    two\n', '\n', 'four\n'], lines,
                         "Expected and result don't match")

    def test_below_newline_present(self):
        i = 2
        lines = ['one\n', '    two\n', '\n', 'four\n']

        self.testee(i, lines, pos='below')
        self.assertEqual(['one\n', '    two\n', '\n', 'four\n'], lines,
                         "Expected and result don't match")

class Test__add_newline(unittest.TestCase):

    def setUp(self) -> None:
        self.testee = undecorated(perfec2.util._add_newline)

    def test_above(self):
        i = 2
        lines = ['one\n', '    two\n', '    three\n', 'four\n']

        self.testee(i, lines)
        self.assertEqual(['one\n', '    two\n', '\n', '    three\n', 'four\n'], lines,
                         "Expected and actual don't match")

    def test_below(self):
        i = 2
        lines = ['one\n', '    two\n', '    three\n', 'four\n']

        self.testee(i, lines, pos='below')
        self.assertEqual(['one\n', '    two\n', '    three\n', '\n', 'four\n'], lines,
                         "Expected and actual don't match")

class Test_match_indentation_and_insert(unittest.TestCase):

    def setUp(self) -> None:
        self.testee = undecorated(perfec2.util.match_indentation_and_insert)

    @mock.patch('util.util._indentation')
    def test_above(self, _indentation):
        add_lines = ['me\n', 'dot\n', 'com\n']
        lines = ['one\n', '   two\n', '   three\n', 'four\n']
        index = 2
        _indentation.return_value = 3
        # todo util._add_newline_if_not_empty.side_effect = []

        self.testee(add_lines, index, lines)
        self.assertEqual(['one\n', '   two\n', '   me\n', '   dot\n', '   com\n', '   three\n', 'four\n'], lines,
                         "Expected and actual don't match")

    @mock.patch('util.util._indentation')
    def test_below(self, _indentation):
        add_lines = ['me\n', 'dot\n', 'com\n']
        lines = ['one\n', '   two\n', '   three\n', 'four\n']
        index = 2
        _indentation.return_value = 3
        # todo util._add_newline_if_not_empty.side_effect = []

        self.testee(add_lines, index, lines, pos='below')

        self.assertEqual(['one\n', '   two\n', '   three\n', '   me\n', '   dot\n', '   com\n', 'four\n'], lines,
                         "Expected and actual don't match")
