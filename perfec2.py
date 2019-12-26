import traceback
from typing import List, Callable

import javalang
from deprecated import deprecated
from javalang.ast import Node
from javalang.parser import JavaSyntaxError
from javalang.tree import ClassDeclaration, FieldDeclaration, MethodDeclaration, Annotation

from util import util

cu = None


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
def field_spacing(fd: FieldDeclaration, lines: [str]) -> [str]:
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
def add_field(clazz: ClassDeclaration, fieldtype: str, name: str, acc_mod: str, lines: [str], anno_name) -> [str]:
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
def remove_node_annotation(member: Node, anno: str, lines: [str]) -> [str]:
    """ remove an annotation from a field, class or method. wont throw an exception """
    annos = [a for a in member.annotations if a.name == anno]
    if annos:
        del lines[annos[0].position.line - 1]
    else:
        print(f'Member {member.name} has no annotation @{anno}')
    return lines


def get_class_annotation(clazz: ClassDeclaration, anno: str) -> Annotation:
    """ get an annotation from a class or None """
    annos = [a for a in clazz.annotations if a.name == anno]
    if annos:
        return annos[0]


@_reparse
def add_node_annotation(node: Node, anno_name: str, lines: [str], anno_props: dict = None,
                        oneline: bool = False) -> [str]:
    """ add an annotation with optional properties to a class, field, or method """
    if isinstance(node, ClassDeclaration):
        i = util.first_classbody_line(node) - 1
    else:
        i = node.position.line - 1
    if anno_props:
        anno_lines = util.annotation_with_props_lines(anno_name, anno_props, oneline=oneline)
    else:
        anno_lines = [f'@{anno_name}\n']
    lines = util.match_indentation_and_insert(anno_lines, i, lines, pos='above')
    return lines


@_reparse
def remove_all_anno(name: str, lines: [str]) -> [str]:
    """ remove all single-line annotations of name from lines """
    # fixme account for multiline annotations
    for i, l in enumerate(lines):
        if l.find('@' + name) != -1 and l.rfind(';') == -1:
            del lines[i]
    return lines


@deprecated
@_reparse
def add_field_annotation(field: FieldDeclaration, anno: str, lines: [str], props: dict = None) -> [str]:
    """ add an annotation with optional properties to a field"""
    field_index = field.position.line - 1  # off by one
    if props:
        anno_lines = util.annotation_with_props_lines(anno, props)
    else:
        anno_lines = [f'@{anno}']
    lines = util.match_indentation_and_insert(anno_lines, field_index, lines, pos='above')
    return lines


@_reparse
def remove_fields(fields: [FieldDeclaration], lines: [str]) -> [str]:
    for f in fields:
        del lines[f.position.line - 1]  # off by one
        for a in f.annotations:
            del lines[a.position.line - 1]  # off by one
    return lines


def constr_params_from_fielddeclrs(fields: [FieldDeclaration]) -> [str]:
    return [f'{f.type.name} '
            f'{list(f.declarators)[0].name if len(f.declarators) else ""}'
            for f in fields]


@_reparse
def add_constructor(params: [str], clazz: ClassDeclaration, lines: [str]) -> [str]:
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


def replace_annotation_on_members(clazz: ClassDeclaration, member_type: str, lines: [str], target_anno_name: str,
                                  replacement_anno_name: str, gen_props: Callable = None, oneline: bool = False):
    """
    replace an existing annotation with a new one (with or without parameters) on all fields or methods
    :param clazz:                       class to modify
    :param member_type:                 type of member ('fields' or 'methods'
    :param lines:                       java file lines
    :param target_anno_name:           name of the annotation to remove
    :param replacement_anno_name:       name of the annotation to add in place of removed_anno_name
    :param gen_props:                   a function to generate the properties for the replacement annotation
                                        should take the member (some type of Node) as its only argument and return a dict
    :param oneline:                     boolean: annotation should be all on one line
    :return:
    """
    last_m, new_props = None, None

    def remove_target(m, lines) -> [str]:
        if util.method_has_annotation(m, target_anno_name):
            existing_anno = util.get_method_annotation(m, target_anno_name)
            nonlocal last_m, new_props
            new_props = gen_props(m)
            lines = remove_node_annotation(m, existing_anno.name, lines)
            last_m = m
        return lines

    def add_replacement(m, lines) -> [str]:
        if last_m and m.name == last_m.name:
            lines = add_node_annotation(m, replacement_anno_name, lines, anno_props=new_props, oneline=oneline)
        return lines

    return _do_all_class_members(clazz, member_type, lines, [remove_target, add_replacement])


def annotate_methods_having_annotation(clazz: ClassDeclaration, lines: [str], target_anno: str, add_anno: str,
                                       gen_props: Callable = None) -> [str]:
    """
    annotate all methods on a class that have existing_anno
    :param clazz:           class to have its methods annotated
    :param lines:           class file lines
    :param target_anno:     annotation to select methods by. only methods with this annotation will be annotated with
    :param add_anno:        annotation to add on the same method as target_anno
    :param gen_props:       function to create the properties for each MethodDeclaration. Takes a MethodDeclaration as its
                            only argument and returns a dict of properties
    :return:                java class file lines
    """

    def add_annotation_where_other_anno_exists(m, lines):
        if util.method_has_annotation(m, target_anno):
            props = gen_props(m)
            add_node_annotation(m, add_anno, lines, anno_props=props, oneline=False)
        return lines

    return _do_all_class_members(clazz, 'methods', lines, [add_annotation_where_other_anno_exists])


def _do_all_class_members(clazz: ClassDeclaration, member_type: str, lines: [str], operations: [Callable],
                          args: [dict] = None) -> [str]:
    """
    operate on class members while looping through them
    :param clazz:       class whose members will be operated on
    :param member_type: 'methods' or 'fields'
    :param lines:       java class file lines
    :param operations:  list of Callables performed on each member_type of the clazz. first arg must be a member_type,
                        and have an arg 'lines'. Must return its own 'lines'.
    :param args:        list of other optional arguments to be passed in parallel to operations. useful if you want to
                        just call this function directly rather than defining your operations in a wrapper function
    :return:            java class file lines
    """
    if not getattr(this_clazz(), member_type, None):
        raise Exception(f'Class {clazz.name} has no \'{member_type}\' members')
    completed = []  # names of methods already yielded
    next = 0
    total = len(clazz.methods)  # initial length
    next_m = getattr(clazz, member_type)[next]  # initial member
    ret_lines = lines  # set initial lines
    while True:
        curr_total = len(getattr(this_clazz(), member_type))
        if total != curr_total:  # file was modified since last iteration, restart
            total = curr_total
            completed.clear()
            next = 0
            continue
        # todo accumulate?
        for i, o in enumerate(operations):
            # fixme this doesn't keep up with added/removed members? only changed lines
            """ get [next] repeatedly since lines probably changed in the course of 'operations'"""
            next_m = getattr(this_clazz(), member_type)[next]
            if next_m.name not in completed:
                if args:
                    ret_lines = o(next_m, lines=ret_lines, **args[i])
                else:
                    ret_lines = o(next_m, lines=ret_lines)
        completed.append(next_m.name)
        next += 1
        if next == curr_total:
            return ret_lines


@_reparse
def add_method(acc_mod: str, rettype: str, name: str, args: [str], body: [str], pos: int, lines: [str],
               anno: str = None) -> [str]:
    mlines = util.method_lines(acc_mod, rettype, name, args, body, anno)
    # todo use match_indentation_and_insert
    lines[pos:len(mlines)] = mlines
    return lines


@_reparse
def add_import(path: str, lines: [str]) -> [str]:
    """
    add an import to this class if not already present
    :param lines:
    :param path:
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
def remove_import(path: str, lines: [str]) -> [str]:
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
