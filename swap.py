import os
from typing import List

import javalang
import traceback
from javalang.tree import ClassDeclaration, FieldDeclaration, CompilationUnit, ConstructorDeclaration

from util.util import field_has_name, is_classfile, is_testfile, write_file, last_field_line, fields_with_anno, \
    get_field, field_has_anno, last_import_line, first_classbody_line, indentation, first_field_line, field_height, \
    enter_line_if_not_empty, get_constructor

repo_path = '/Users/sroman/repos/accountmanagement-entities/'

cu = None


def reparse(func):
    def wrapper(*args, **kwargs):
        lines = func(*args, **kwargs)
        lines_asone = ''.join(lines)
        global cu
        cu = javalang.parse.parse(lines_asone)
        return lines

    return wrapper


def e_handle(func):
    def wrapper(*args, **kwargs):
        try:
            val = func(*args, **kwargs)
            return val
        except Exception as e:
            raise e

    return wrapper


@reparse
def field_spacing(fd: FieldDeclaration, lines: List[str]) -> List[str]:
    """
    add spacing if required above and below a field
    taking into account its annotations
    :param fd:
    :param lines:
    :return:
    """
    height = field_height(fd)
    bottom = fd.position.line - 1
    top = bottom - height + 1

    enter_line_if_not_empty(top - 1, lines)
    enter_line_if_not_empty(bottom + 1, lines)

    return lines


@reparse
@e_handle
def add_field(clazz: ClassDeclaration, fieldtype: str, name: str, acc_mod: str, lines: List[str],
              anno_name: str = None) -> List[str]:
    if not [f for f in clazz.fields
            if field_has_name(f, name)
               and f.type.name == fieldtype
               and filter(lambda m: m == acc_mod, f.modifiers)
               and filter(lambda a: a.name == anno_name, f.annotations)]:

        # where will the field be inserted?:
        if clazz.fields:
            l = first_field_line(clazz)
            top_or_bottom_pad = 0
        else:
            l = first_classbody_line(clazz)
            top_or_bottom_pad = 1

        has_anno = 0
        spaces = indentation(l, lines)
        field_lines = []
        if anno_name:
            field_lines.append(f'{spaces * " " if spaces else ""}@{anno_name}\n')
            has_anno = 1
        field_lines.append(f'{spaces * " " if spaces else ""}{acc_mod} {fieldtype} {name};\n')
        lines[l + top_or_bottom_pad:1 + has_anno] = field_lines
        # fixme add bottom/top spacing
    return lines


@reparse
@e_handle
def add_field_annotation(field: FieldDeclaration, anno: str, lines: List[str]) -> List[str]:
    field_index = field.position.line - 1  # off by one
    lines[field_index:1] = [f'@{anno}']
    # todo fix spacing and tabbing
    return lines


@reparse
@e_handle
def remove_fields(fields: List[FieldDeclaration], lines: List[str]) -> List[str]:
    for f in fields:
        del lines[f.position.line - 1]  # off by one
        for a in f.annotations:
            del lines[a.position.line - 1]  # off by one
    return lines


def constr_params_from_fielddeclrs(fields: List[FieldDeclaration]) -> List[str]:
    return [f'{f.type.name} ' \
            f'{list(f.declarators)[0].name if len(f.declarators) else ""}'
            for f in fields]


@reparse
@e_handle
def add_constructor(params: List[str], clazz: ClassDeclaration, lines: List[str]) -> List[str]:
    """
    add a constructor to this class
    :param params:
    :param lines:
    :param clazz:
    :return:
    """
    const_line = first_classbody_line(clazz) + 1  # line after open brace
    assignments = []
    for i, p in enumerate(params):
        begin = '    '
        end = ';\n' if p == params[i] else ', '
        varname = p.split(" ")[-1]
        assignments.append(f'{begin}this.{varname} = {varname}{end}')

    constructor_lines = methodlines('public', '', clazz.name, params, assignments)
    # todo fix spacing and tabbing
    lines[const_line:len(constructor_lines)] = constructor_lines

    return lines


def methodlines(acc_mod: str, rettype: str, name: str, args: List[str], body: List[str], anno: str = None) -> List[str]:
    return [f'{"@" + anno if anno else ""}\n',
            f'{acc_mod} {rettype + " " if rettype else ""}{name}({", ".join(args)}) {{\n'] + \
               body + \
           ['}\n']


@reparse
@e_handle
def add_import(path: str, cu: CompilationUnit, lines: [str]) -> List[str]:
    """
    add an import to this class if not already present
    :param lines:
    :param path:
    :param cu:
    :return:
    """
    imports = set([i.path for i in cu.imports])
    if path not in imports:
        l = last_import_line(cu)
        lines[l + 1:1] = [f'import {path};\n']
    return lines


@reparse
@e_handle
def remove_import(cu: CompilationUnit, path: str, lines: List[str]) -> List[str]:
    del lines[list(filter(lambda i: i.path == path, cu.imports))[0].position.line]
    # fixme
    return lines


@reparse
@e_handle
def add_method(acc_mod: str, rettype: str, name: str, args: List[str], body: List[str], pos: int, lines: List[str],
               anno: str = None) -> List[str]:
    mlines = methodlines(acc_mod, rettype, name, args, body, anno)
    lines[pos:len(mlines)] = mlines
    # todo fix spacing and tabbing
    return lines


@e_handle
def find_testee(testclazz: ClassDeclaration) -> FieldDeclaration:
    # has @Spy or named 'testee' or type is in class name
    # fixme: prioritize 'testee' name as selection criteria

    fields = testclazz.fields
    testees = []
    if fields:
        testees = list(filter(lambda f: field_has_name(f, 'testee') or
                                        f.declarators[0].name.upper() in testclazz.name.upper() or
                                        field_has_anno(f, 'Spy'), fields))
    if not testees:
        raise Exception(f'Testee for test class {testclazz.name} not found')
    return testees[0]


@reparse
@e_handle
def remove_all_anno(name: str, lines: List[str]) -> List[str]:
    for i, l in enumerate(lines):
        if l.find('@' + name) != -1 and l.rfind(';') == -1:
            del lines[i]
    return lines


def refactor_classfile(lines: List[str]):
    global cu
    print(f'processing class {cu.types[0].name}')

    get_constructor(cu.types[0], [])

    # add Logger field
    # todo return added field
    add_field(cu.types[0], 'Logger', 'log', 'private', lines)
    field_spacing(get_field(cu.types[0], 'log'), lines)

    # find @Autowired fields
    aw_fields = fields_with_anno(cu.types[0], 'Autowired')

    # remove all @Autowired
    remove_all_anno('Autowired', lines)

    # remove all @Slf4j
    remove_all_anno('Slf4j', lines)

    # add constructor with those fields plus the logger field
    field_strs = constr_params_from_fielddeclrs(aw_fields)
    add_constructor(['Logger log'] + field_strs, cu.types[0], lines)

    # add noarg constructors
    add_constructor([], cu.types[0], lines)

    # add imports:
    return add_import('org.slf4j.Logger', cu, lines)


def refactor_testfile(lines: List[str]) -> List[str]:
    global cu
    print(f'Refactoring {cu.types[0].name}')

    # add Logger with @Mock
    add_field(cu.types[0], 'Logger', 'log', 'private', lines, 'Mock')
    field_spacing(get_field(cu.types[0], 'log'), lines)

    # check if @InjectMocks required
    if not fields_with_anno(cu.types[0], 'InjectMocks'):
        # add @InjectMocks to testee
        add_field_annotation(find_testee(cu.types[0]), 'InjectMocks', lines)
        field_spacing(find_testee(cu.types[0]), lines)

        # also add @Before init mocks
        lfield = last_field_line(cu.types[0])
        add_method('public', 'void', 'init', [], ['MockitoAnnotations.initMocks(this);\n'], lfield + 1, lines, 'Before')

        add_import('org.mockito.InjectMocks', cu, lines)
        add_import('org.mockito.MockitoAnnotations', cu, lines)
        add_import('org.junit.Before', cu, lines)

    # add mock import
    add_import('org.slf4j.Logger', cu, lines)
    return add_import('org.mockito.Mock', cu, lines)


def process_file(path: str):
    global cu
    with open(path, 'r+') as jf:

        lines = jf.readlines()
        as_str = ''.join(lines)
        cu = javalang.parse.parse(as_str)

        if is_classfile(cu) and list(filter(lambda a: a.name == 'Slf4j', cu.types[0].annotations)):
            newlines = refactor_classfile(lines)
            write_file(newlines, jf)
        elif is_testfile(cu):
            try:
                newlines = refactor_testfile(lines)
                write_file(newlines, jf)
            except Exception as e:
                print(traceback.format_exc())


def main():
    cwd = os.path.dirname(os.path.abspath(__file__))
    global cu

    for root, dirs, files in os.walk(repo_path + 'src/'):
        for f in files:
            if f.endswith('.java'):
                process_file(os.path.join(root, f))


if __name__ == '__main__':
    main()
