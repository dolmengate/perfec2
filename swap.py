import os
from typing import List

import javalang
from javalang.tree import ClassDeclaration, FieldDeclaration, CompilationUnit

repo_path = '/Users/sroman/repos/accountmanagement-entities/'

cu = None


def re_parse(func):
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
        except Exception as e:
            raise e
        return val

    return wrapper


def field_has_anno(f: FieldDeclaration, anno_name: str) -> bool:
    return len(list(filter(lambda a: a.name == anno_name, f.annotations))) > 0


@re_parse
@e_handle
def add_field(clazz: ClassDeclaration, fieldtype: str, name: str, acc_mod: str, lines: List[str],
              anno_name: str = None) -> str:
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


@re_parse
@e_handle
def add_field_annotation(field: FieldDeclaration, anno: str, lines: List[str]) -> List[str]:
    field_index = field.position.line - 1  # off by one
    lines[field_index:1] = f'@{anno}'
    return lines


def first_field_line(clazz: ClassDeclaration) -> int:
    num_annos = len(clazz.fields[0].annotations)
    return clazz.fields[0].position.line - num_annos - 1  # off by one


def last_field_line(clazz: ClassDeclaration) -> int:
    num_annos = len(clazz.fields[0].annotations)
    return clazz.fields[-1].position.line + num_annos - 1  # off by one


@re_parse
@e_handle
def remove_fields(fields: List[FieldDeclaration], lines: List[str]) -> List[str]:
    for f in fields:
        del lines[f.position.line - 1]  # off by one
        for a in f.annotations:
            del lines[a.position.line - 1]  # off by one
        return lines
    return []


def field_has_name(fd: FieldDeclaration, name: str) -> bool:
    return len(list(filter(lambda d: d.name == name, fd.declarators))) > 0


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


def autowired_fields(clazz: ClassDeclaration) -> [FieldDeclaration]:
    """
    all fields with the @Autowired annotation
    :param clazz:
    :return:
    """
    return fields_with_anno(clazz, 'Autowired')


def constr_params_from_fielddeclrs(fields: List[FieldDeclaration]) -> List[str]:
    return [f'{f.type.name} ' \
            f'{list(f.declarators)[0].name if len(f.declarators) else ""}'
            for f in fields]


@re_parse
@e_handle
def add_constructor(params: List[str], clazz: ClassDeclaration, lines: List[str]) -> List[str]:
    """
    add a constructor to this class
    :param lines:
    :param const:
    :param clazz:
    :return:
    """
    const_line = first_classbody_line(clazz) + 1  # line after open brace
    params_str = ', '.join(params)
    assignments = []
    for i, p in enumerate(params):
        begin = '    '
        end = ';\n' if p == params[i] else ', '
        varname = p.split(" ")[-1]
        assignments.append(f'{begin}this.{varname} = {varname}{end}')

    # todo indent based on above line indentation
    constructor_lines = methodlines('public', '', clazz.name, params, assignments)
    # todo add bottom/top spacing
    lines[const_line:len(constructor_lines)] = constructor_lines

    return lines


def methodlines(acc_mod: str, rettype: str, name: str, args: List[str], body: List[str]):
    return [f'{acc_mod} {rettype + " " if rettype else ""}{name}({", ".join(args)}) {{\n'] + \
           body + \
           ['}\n']


def last_import_line(cu: CompilationUnit) -> int:
    """
    get the line number of the last import in the file
    :param cu:
    :return:
    """
    return cu.imports[-1].position.line - 1  # off by one


def clazz(cu: CompilationUnit) -> ClassDeclaration:
    return cu.types[0]


@re_parse
@e_handle
def add_import(path: str, cu: CompilationUnit, lines: [str]) -> List[str]:
    """
    add an import to this class
    :param lines:
    :param path:
    :param cu:
    :return:
    """
    l = last_import_line(cu)
    lines[l + 1:1] = [path + '\n']
    return lines


@re_parse
def enter_line_if_not_empty(lines: List[str], line: int) -> List[str]:
    if lines[line] != '\n':
        lines[line:1] = '\n'
    return lines


def mock_in_tests():
    pass


# @re_parse
# @e_handle
# def remove_news(test_class: ClassDeclaration) -> List[str]:
#     """
#     remove new whatever() calls from test_class
#     :param test_class:
#     :return:
#     """
#     # use @InjectMocks to find
#     fields = fields_with_anno(test_class, 'InjectMocks')
#     # fixme
#     pass
#

def fields_with_anno(clazz: ClassDeclaration, anno_name: str) -> [FieldDeclaration]:
    """
    FieldDeclarations of type anno_name in this class
    :param clazz:
    :param anno_name:
    :return:
    """
    return list(filter(lambda fd: field_has_anno(fd, anno_name), clazz.fields))


@re_parse
@e_handle
def remove_import(cu: CompilationUnit, path: str, lines: List[str]) -> List[str]:
    del lines[list(filter(lambda i: i.path == path, cu.imports))[0].position.line]
    # fixme
    return lines


@re_parse
@e_handle
def add_method(acc_mod: str, rettype: str, name: str, args: List[str], body: List[str], pos: int, lines: List[str],
               anno: str = None) -> List[str]:
    mlines = methodlines(acc_mod, rettype, name, args, body)
    # todo annotation
    lines[pos:len(mlines)] = mlines


def find_testee(testclazz: ClassDeclaration) -> FieldDeclaration:
    fields = testclazz.fields
    try:
        # has @Spy or named 'testee' or type is in class name
        return list(filter(
            lambda f: field_has_anno(f, 'Spy') or field_has_name(f,
                                                                 'testee') or f.name.upper() in testclazz.name.upper(),
            testclazz.fields))[0]
    except Exception as e:
        print(f'Testee for test class {testclazz.name} not found')


@re_parse
@e_handle
def remove_all_anno(name: str, lines: List[str]) -> List[str]:
    for i, l in enumerate(lines):
        if l.find('@' + name) != -1 and l.rfind(';') == -1:
            del lines[i]
    return lines


def refactor_classfile(lines: List[str], cu: ClassDeclaration):
    clazz = cu.types[0]
    print(f'processing class {clazz.name}')

    # add Logger field
    add_field(clazz, 'Logger', 'log', 'private', lines)

    # find @Autowired fields
    aw_fields = autowired_fields(clazz)

    # remove all @Autowired
    remove_all_anno('Autowired', lines)

    # remove all @Slf4j
    remove_all_anno('Slf4j', lines)

    # add constructor with those fields plus the logger field
    field_strs = constr_params_from_fielddeclrs(aw_fields)
    add_constructor(['Logger log'] + field_strs, clazz, lines)

    # add noarg constructors
    add_constructor([], clazz, lines)

    # add imports:
    return add_import('import org.slf4j.Logger;', cu, lines)


def refactor_testfile(lines: List[str], cu: CompilationUnit) -> List[str]:
    clazz = cu.types[0]
    testee = find_testee(clazz)

    # add Logger with @Mock
    add_field(clazz, 'Logger', 'log', 'private', lines, 'Mock')

    # check if @InjectMocks required
    if not fields_with_anno(clazz, 'InjectMocks'):
        # add @InjectMocks to testee
        add_field_annotation(testee, 'InjectMocks', lines)

        # also add @Before init mocks
        lfield = last_field_line(clazz)
        add_method('public', 'void', 'init', [], ['MockitoAnnotations.initMocks(this);\n'], lfield + 1, lines)

        # add InjectMocks import
        add_import('import org.mockito.InjectMocks;', cu, lines)
        # add Mockito import org.mockito.MockitoAnnotations;
        add_import('import org.mockito.MockitoAnnotations;', cu, lines)

    # add mock import
    add_import('import org.slf4j.Logger;', cu, lines)
    return add_import('import org.mockito.Mock;', cu, lines)


def is_classfile(cu: CompilationUnit) -> bool:
    clazz = cu.types[0]
    if not clazz: return False
    return not clazz.name.endswith('Test')


def is_testfile(cu: CompilationUnit) -> bool:
    clazz = cu.types[0]
    if not clazz: return False
    return clazz.name.endswith('Test')


def update_file(newlines, file_obj):
    file_obj.seek(0)
    for nl in newlines:
        file_obj.write(nl)
    file_obj.truncate()


def process_file(path: str):
    with open(path, 'r+') as jf:

        lines = jf.readlines()
        as_str = ''.join(lines)
        cu = javalang.parse.parse(as_str)

        if is_classfile(cu) and list(filter(lambda a: a.name == 'Slf4j', cu.types[0].annotations)):
            newlines = refactor_classfile(lines, cu)
            update_file(newlines, jf)
        elif is_testfile(cu):
            try:
                newlines = refactor_testfile(lines, cu)
                update_file(newlines, jf)
            except Exception as e:
                print('something went wrong', e)


def main():
    cwd = os.path.dirname(os.path.abspath(__file__))
    global cu

    for root, dirs, files in os.walk(repo_path + 'src/'):
        for f in files:
            if f.endswith('.java'):
                process_file(os.path.join(root, f))


if __name__ == '__main__':
    main()
