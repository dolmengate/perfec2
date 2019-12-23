import traceback
from typing import List, Callable

import javalang
from javalang.parser import JavaSyntaxError
from javalang.tree import ClassDeclaration, FieldDeclaration, MethodDeclaration

from util import util

cu = None


# todo generify this method to work with any property of a class with any condition
def methods_with_anno(clazz, anno: str):
    completed = []  # names of methods already yielded
    name = clazz.name
    next = 0
    total = len(this_clazz().methods)  # initial length
    if this_clazz().name == name:  # limit looping through methods of the desired class only
        while True:
            curr_total = len(this_clazz().methods)
            if total != curr_total:     # file was modified since last iteration, restart
                total = curr_total
                completed.clear()
                next = 0
                continue
            next_m = this_clazz().methods[next]
            if util.method_has_annotation(next_m, anno) and next_m.name not in completed:
                completed.append(next_m.name)
                yield next_m
            next += 1
            if next == curr_total:
                break


def _reparse(func):
    def wrapper(*args, **kwargs):
        lines = func(*args, **kwargs)
        lines_asone = ''.join(lines)
        global cu
        try:
            cu = javalang.parse.parse(lines_asone)
        except JavaSyntaxError as e:
            traceback.format_exc()
        return lines

    return wrapper


@_reparse
def field_spacing(fd: FieldDeclaration, lines: List[str]) -> List[str]:
    """
    add spacing if required above and below a field
    taking into account its annotations
    :param fd:
    :param lines:
    :return:
    """
    height = util.field_height(fd)
    index = fd.position.line - 1

    # have to return lines for 'mock' to know anything was changed
    lines = util._add_newline_if_not_empty(index, lines, pos='bottom')
    lines = util._add_newline_if_not_empty(index - height, lines)

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
            if util.is_classfile(cu):
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


@_reparse
def add_field(clazz: ClassDeclaration, fieldtype: str, name: str, acc_mod: str, lines: List[str], anno_name) -> List[str]:
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
            l_i = util.first_field_line(clazz)
            pos_mod = 'above'
        else:
            l_i = util.first_classbody_line(clazz)
            pos_mod = 'below'

        field_lines = [f'{acc_mod} {fieldtype} {name};\n']
        lines = util.match_indentation_and_insert(field_lines, l_i, lines, pos=pos_mod)
    return lines


@_reparse
def remove_class_anno(clazz: ClassDeclaration, name: str):
    pass


@_reparse
def remove_all_anno(name: str, lines: List[str]) -> List[str]:
    for i, l in enumerate(lines):
        if l.find('@' + name) != -1 and l.rfind(';') == -1:
            del lines[i]
    return lines


@_reparse
def add_field_annotation(field: FieldDeclaration, anno: str, lines: List[str], props: dict = None) -> List[str]:
    field_index = field.position.line - 1  # off by one
    if props:
        anno_lines = util.annotation_with_props_lines(anno, props)
    else:
        anno_lines = [f'@{anno}']
    lines = util.match_indentation_and_insert(anno_lines, field_index, lines, pos='above')
    return lines


# fixme refactor to make props optional
@_reparse
def add_method_annotation_with_props(method: MethodDeclaration, props: dict, anno: str, lines: List[str]) -> List[str]:
    m_line = method.position.line - 1  # off by one
    anno_lines = util.annotation_with_props_lines(anno, props)
    # fixme use match_indentation_and_insert
    util.match_indentation_and_insert(anno_lines, m_line, lines)
    # lines[m_line: len(anno_lines)] = anno_lines  # insert just above the method signature, below other annotations
    return lines


@_reparse
def remove_fields(fields: List[FieldDeclaration], lines: List[str]) -> List[str]:
    for f in fields:
        del lines[f.position.line - 1]  # off by one
        for a in f.annotations:
            del lines[a.position.line - 1]  # off by one
    return lines


def constr_params_from_fielddeclrs(fields: List[FieldDeclaration]) -> List[str]:
    return [f'{f.type.name} '
            f'{list(f.declarators)[0].name if len(f.declarators) else ""}'
            for f in fields]


@_reparse
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

    constructor_lines = util.method_lines('public', '', clazz.name, params, assignments)
    # todo use match_indentation_and_insert
    lines[const_line:len(constructor_lines)] = constructor_lines
    return lines


@_reparse
def add_method(acc_mod: str, rettype: str, name: str, args: List[str], body: List[str], pos: int, lines: List[str],
               anno: str = None) -> List[str]:
    mlines = util.method_lines(acc_mod, rettype, name, args, body, anno)
    # todo use match_indentation_and_insert
    lines[pos:len(mlines)] = mlines
    return lines


@_reparse
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
        # todo use match_indentation_and_insert
        lines[l + 1:1] = [f'import {path};\n']
    return lines


@_reparse
def remove_import(path: str, lines: List[str]) -> List[str]:
    global cu
    del lines[list(filter(lambda i: i.path == path, cu.imports))[0].position.line]
    # fixme
    return lines


def find_testee(testclazz: ClassDeclaration) -> FieldDeclaration:
    # fixme move out of this library
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


def this_clazz():
    global cu
    return util._clazz(cu)
