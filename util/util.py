# # # # # # # # # # # #
# lines and spacing
#
import itertools
import traceback
from typing import List

from javalang.tree import ClassDeclaration, FieldDeclaration, ConstructorDeclaration, CompilationUnit, MethodDeclaration


def last_import_line(cu: CompilationUnit) -> int:
    """
    get the line number of the last import in the file
    :param cu:
    :return:
    """
    return cu.imports[-1].position.line - 1  # off by one


def _clazz(cu: CompilationUnit) -> ClassDeclaration:
    return cu.types[0]


def _add_newline_if_not_empty(i: int, lines: List[str], pos: str = 'above') -> List[str]:
    if pos == 'above':
        pos_mod = 0
    elif pos == 'below':
        pos_mod = +1
    else:
        raise Exception("fixme ")
    if lines[i] != '\n':
        lines[i+pos_mod:1] = '\n'
    return lines


def _add_newline(i: int, lines: [str], pos: str = 'above') -> [str]:
    if pos == 'above':
        pos_mod = 0
    elif pos == 'below':
        pos_mod = +1
    else:
        raise Exception("fixme ")
    lines[i+pos_mod:1] = '\n'
    return lines


def _indentation(index: int, lines: List[str]) -> int:
    """
    get indent spaces from @line in @lines
    :param lines:
    :param index:
    :return:
    """
    line = lines[index]
    return len([s for s in itertools.takewhile(lambda c: c == ' ', line)])


# fixme reparse?
# fixme indentation should be additive to lines in add_lines
def match_indentation_and_insert(add_lines: [str], index: int, insertee_lines: [str], pos: str = 'above', top_pad: int = 0, bot_pad: int = 0) -> [str]:
    # add amount of indentation to all add_lines equal to the indentation on the line to be inserted at
    if pos != 'below' and pos != 'above':
        raise Exception("Insertion must be either 'below' or 'above' only")
    if pos == 'below':
        pos = 1
    else:
        pos = 0

    # fixme find the indentation of the first line above or below that isn't a newline
    indent = _indentation(index, insertee_lines)
    for i, l in enumerate(add_lines):
        add_lines[i] = l.rjust(len(l)+indent, ' ')
    # insert add_lines into insertee_lines
    final_insertion_index = index + pos
    # _add_newline_if_not_empty(final_insertion_index, insertee_lines, 'above')
    # insertee_lines[final_insertion_index: len(add_lines)] = add_lines
    insertee_lines[final_insertion_index:0] = add_lines
    return insertee_lines


def first_classbody_line(clazz: ClassDeclaration) -> int:
    """
    first line of the class body
    :param clazz:
    :return:
    """
    return clazz.position.line - 1  # off by one


# # # # # # # # # # # #
# field utils
#
def field_has_anno(f: FieldDeclaration, anno_name: str) -> bool:
    return len(list(filter(lambda a: a.name == anno_name, f.annotations))) > 0


def field_has_name(fd: FieldDeclaration, name: str) -> bool:
    return len(list(filter(lambda d: d.name == name, fd.declarators))) > 0


def fields_with_anno(clazz: ClassDeclaration, anno_name: str) -> [FieldDeclaration]:
    """
    FieldDeclarations of type anno_name in this class
    :param clazz:
    :param anno_name:
    :return:
    """
    return list(filter(lambda fd: field_has_anno(fd, anno_name), clazz.fields))


def first_field_line(clazz: ClassDeclaration) -> int:
    num_annos = len(clazz.fields[0].annotations)
    return clazz.fields[0].position.line - num_annos - 1  # off by one


def last_field_line(clazz: ClassDeclaration) -> int:
    num_annos = len(clazz.fields[0].annotations)
    return clazz.fields[-1].position.line + num_annos - 1  # off by one


def field_height(fd: FieldDeclaration) -> int:
    return len(fd.annotations) + 1


def field_with_name(clazz: ClassDeclaration, name: str) -> FieldDeclaration:
    try:
        return list(filter(lambda f: field_has_name(f, name), clazz.fields))[0]
    except Exception as e:
        print(traceback.format_exc())
        print(f'class {clazz.name} has no field {name}')


# def get_constructor(clazz: ClassDeclaration, args: List[str]) -> ConstructorDeclaration:
    # fixme compare constructor args with set
    # return list(filter(lambda c: c, clazz.constructors))


# def constructor_height(fd: ConstructorDeclaration) -> int:
#     todo implement
    # pass


# # # # # # # # # # # #
# method utils
#
# def methods_with_anno(clazz: ClassDeclaration, anno: str) -> [MethodDeclaration]:
#     return [m for m in clazz.methods for a in m.annotations if a.name == anno]


# def method_height(method: MethodDeclaration) -> int:
#     return method.position.line + 0 + len(method.annotations) # todo implement


def method_has_annotation(method: MethodDeclaration, anno: str) -> bool:
    annos = filter(lambda a: a.name == anno, method.annotations)
    return any(annos)


def method_lines(acc_mod: str, rettype: str, name: str, args: List[str], body: List[str], anno: str = None) -> List[
    str]:
    return [f'{"@" + anno if anno else ""}\n',
            f'{acc_mod} {rettype + " " if rettype else ""}{name}({", ".join(args)}) {{\n'] + \
           body + \
           ['}\n']


# # # # # # # # # # # #
# annotation utils
#
def annotation_with_props_lines(name: str, props: dict) -> [str]:
    annoprops_lines = [f'{k}={v},\n' for k, v in props.items()]
    annoprops_lines[-1] = annoprops_lines[-1].replace(',\n', '\n')
    return [f'@{name}(\n'] + \
           annoprops_lines + \
           [')\n']


# # # # # # # # # # # #
# file processing
#
def is_classfile(cu: CompilationUnit) -> bool:
    clazz = cu.types[0]
    if not clazz: return False
    return not clazz.name.endswith('Test')


def is_testfile(cu: CompilationUnit) -> bool:
    clazz = cu.types[0]
    if not clazz: return False
    return 'Test' in clazz.name


def write_file(newlines, file_obj):
    file_obj.seek(0)
    for nl in newlines:
        file_obj.write(nl)
    file_obj.truncate()
