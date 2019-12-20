import traceback
from typing import List, Callable

import javalang
from javalang.tree import ClassDeclaration, FieldDeclaration, MethodDeclaration

from util import util

cu = None


def reparse(func):
    def wrapper(*args, **kwargs):
        lines = func(*args, **kwargs)
        lines_asone = ''.join(lines)
        global cu
        cu = javalang.parse.parse(lines_asone)
        return lines

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
    height = util.field_height(fd)
    bottom = fd.position.line - 1
    top = bottom - height + 1

    util.enter_line_if_not_empty(top - 1, lines)
    util.enter_line_if_not_empty(bottom + 1, lines)

    return lines


def process_file(path: str, classfile_op: Callable, testfile_op: Callable = lambda x: x):
    """
    the the file at path and do either classfile_op or testfile_op to it, then overwrite the file and save it
    does nothing if the file doesn't contain any defined Java types
    :param path:
    :param classfile_op:
    :param testfile_op:
    :return:
    """
    global cu
    with open(path, 'r+') as jf:
        lines = jf.readlines()
        as_str = ''.join(lines)
        cu = javalang.parse.parse(as_str)
        if cu.types:
            if util.is_classfile(cu) and list(filter(lambda a: a.name == 'Slf4j', cu.types[0].annotations)):
                newlines = classfile_op(lines)
                util.write_file(newlines, jf)
            elif util.is_testfile(cu):
                try:
                    newlines = testfile_op(lines)
                    util.write_file(newlines, jf)
                except Exception as e:
                    print(traceback.format_exc())
        else:
            print(f'file {path} has no defined Types')


@reparse
def add_field(clazz: ClassDeclaration, fieldtype: str, name: str, acc_mod: str, lines: List[str],
              anno_name: str = None) -> List[str]:
    """
    Add a field to a class
    :param clazz:
    :param fieldtype:
    :param name:
    :param acc_mod:
    :param lines:
    :param anno_name:
    :return:
    """
    if not [f for f in clazz.fields
            if util.field_has_name(f, name)
               and f.type.name == fieldtype
               and filter(lambda m: m == acc_mod, f.modifiers)
               and filter(lambda a: a.name == anno_name, f.annotations)]:

        # where will the field be inserted?:
        if clazz.fields:
            l = util.first_field_line(clazz)
            top_or_bottom_pad = 0
        else:
            l = util.first_classbody_line(clazz)
            top_or_bottom_pad = 1

        has_anno = 0
        spaces = util.indentation(l, lines)
        field_lines = []
        if anno_name:
            field_lines.append(f'{spaces * " " if spaces else ""}@{anno_name}\n')
            has_anno = 1
        field_lines.append(f'{spaces * " " if spaces else ""}{acc_mod} {fieldtype} {name};\n')
        lines[l + top_or_bottom_pad:1 + has_anno] = field_lines
        # fixme add bottom/top spacing
    return lines


@reparse
def add_field_annotation(field: FieldDeclaration, anno: str, lines: List[str]) -> List[str]:
    field_index = field.position.line - 1  # off by one
    lines[field_index:1] = [f'@{anno}']
    # todo fix spacing and tabbing
    return lines


@reparse
def add_method_annotation_with_props(field: MethodDeclaration, props: dict, anno: str, lines: List[str]) -> List[str]:
    """
    add an annotation to a method when the annotation has its own properties
    :param field:
    :param props:
    :param anno:
    :param lines:
    :return:
    """
    return lines


@reparse
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
def add_constructor(params: List[str], clazz: ClassDeclaration, lines: List[str]) -> List[str]:
    """
    add a constructor to this class
    :param params:
    :param lines:
    :param clazz:
    :return:
    """
    const_line = util.first_classbody_line(clazz) + 1  # line after open brace
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
def add_import(path: str, lines: [str]) -> List[str]:
    """
    add an import to this class if not already present
    :param lines:
    :param path:
    :param cu:
    :return:
    """
    global cu
    imports = set([i.path for i in cu.imports])
    if path not in imports:
        l = util.last_import_line(cu)
        lines[l + 1:1] = [f'import {path};\n']
    return lines


@reparse
def remove_import(path: str, lines: List[str]) -> List[str]:
    global cu
    del lines[list(filter(lambda i: i.path == path, cu.imports))[0].position.line]
    # fixme
    return lines


@reparse
def add_method(acc_mod: str, rettype: str, name: str, args: List[str], body: List[str], pos: int, lines: List[str],
               anno: str = None) -> List[str]:
    mlines = methodlines(acc_mod, rettype, name, args, body, anno)
    lines[pos:len(mlines)] = mlines
    # todo fix spacing and tabbing
    return lines


def find_testee(testclazz: ClassDeclaration) -> FieldDeclaration:
    # has @Spy or named 'testee' or type is in class name
    fields = testclazz.fields
    testees = []
    if fields:
        testees = list(filter(lambda f: util.field_has_name(f, 'testee') or
                                        f.declarators[0].name.upper() in testclazz.name.upper() or
                                        util.field_has_anno(f, 'Spy'), fields))
    if not testees:
        raise Exception(f'Testee for test class {testclazz.name} not found')
    return testees[0]


@reparse
def remove_all_anno(name: str, lines: List[str]) -> List[str]:
    for i, l in enumerate(lines):
        if l.find('@' + name) != -1 and l.rfind(';') == -1:
            del lines[i]
    return lines


def this_clazz():
    global cu
    return util.clazz(cu)
