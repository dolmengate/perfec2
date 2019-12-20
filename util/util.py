# # # # # # # # # # # #
# lines and spacing
#
import traceback
import javalang
from typing import List

from javalang.tree import ClassDeclaration, FieldDeclaration, ConstructorDeclaration, CompilationUnit


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


def last_import_line(cu: CompilationUnit) -> int:
    """
    get the line number of the last import in the file
    :param cu:
    :return:
    """
    return cu.imports[-1].position.line - 1  # off by one


def clazz(cu: CompilationUnit) -> ClassDeclaration:
    return cu.types[0]


def enter_line_if_not_empty(line: int, lines: List[str]) -> List[str]:
    if lines[line] != '\n':
        lines[line:1] = '\n'
    return lines


def indentation(line: int, lines: List[str]) -> int:
    """
    get number of columns from left for line
    :param lines:
    :param line:
    :return:
    """
    line = lines[line]
    if line.startswith(' '):
        line.rstrip()
        return line.rfind(' ') + 1


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


def get_field(clazz: ClassDeclaration, name: str) -> FieldDeclaration:
    try:
        return list(filter(lambda f: field_has_name(f, name), clazz.fields))[0]
    except Exception as e:
        print(traceback.format_exc())
        print(f'class {clazz.name} has no field {name}')


def get_constructor(clazz: ClassDeclaration, args: List[str]) -> ConstructorDeclaration:
    # fixme compare constructor args with set
    return list(filter(lambda c: c, clazz.constructors))


def constructor_height(fd: ConstructorDeclaration) -> int:
    pass

# # # # # # # # # # # #
# method utils
#


def find_method_by_name(clazz: ClassDeclaration, name: str) -> int:
    methods = clazz.methods
    return methods[0].position.line - 1


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
