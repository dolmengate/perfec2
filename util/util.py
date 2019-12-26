# # # # # # # # # # # #
# lines and spacing
#
import os
import subprocess
import re
import itertools
import traceback

from javalang.tree import ClassDeclaration, FieldDeclaration, ConstructorDeclaration, CompilationUnit, \
    MethodDeclaration, Annotation, FormalParameter


def last_import_line(cu: CompilationUnit) -> int:
    """
    get the line number of the last import in the file
    :param cu:
    :return:
    """
    return cu.imports[-1].position.line - 1  # off by one


def _clazz(cu: CompilationUnit) -> ClassDeclaration:
    return cu.types[0]


def _add_newline_if_not_empty(i: int, lines: [str], pos: str = 'above') -> [str]:
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


def _indentation(index: int, lines: [str]) -> int:
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
def match_indentation_and_insert(add_lines: [str], index: int, insertee_lines: [str], pos: str = 'above', indent_mod = 0) -> [str]:
    # add amount of indentation to all add_lines equal to the indentation on the line to be inserted at
    if pos != 'below' and pos != 'above':
        raise Exception("Insertion must be either 'below' or 'above' only")
    if pos == 'below':
        pos = 1
    else:
        pos = 0

    # fixme find the indentation of the first line above or below that isn't a newline
    indent = _indentation(index, insertee_lines) + indent_mod
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


# def get_constructor(clazz: ClassDeclaration, args: [str]) -> ConstructorDeclaration:
    # fixme compare constructor args with set
    # return list(filter(lambda c: c, clazz.constructors))


# def constructor_height(fd: ConstructorDeclaration) -> int:
#     todo implement
    # pass


# # # # # # # # # # # #
# method utils
#
# def method_height(method: MethodDeclaration) -> int:
#     return method.position.line + 0 + len(method.annotations) # todo implement


def method_has_annotation(method: MethodDeclaration, anno: str) -> bool:
    annos = filter(lambda a: a.name == anno, method.annotations)
    return any(annos)


def get_method_annotation(method: MethodDeclaration, anno: str) -> Annotation:
    annos = list(filter(lambda a: a.name == anno, method.annotations))
    if annos:
        return annos[0]
    raise Exception(f'Method {method.name} has no annotation {anno}')


def method_lines(acc_mod: str, rettype: str, name: str, args: [str], body: [str], anno: str = None) -> [
    str]:
    return [f'{"@" + anno if anno else ""}\n',
            f'{acc_mod} {rettype + " " if rettype else ""}{name}({", ".join(args)}) {{\n'] + \
           body + \
           ['}\n']


def method_has_param_types(m: MethodDeclaration, type: str, freq: int):
    n = len([p for p in m.parameters if p.type.name == type])
    return n == freq


# # # # # # # # # # # #
#  Entities CRUD
#
def is_getbyuid_web_endpoint(m: MethodDeclaration) -> bool:
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_get = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'GET'])
    one_param = len(m.parameters) == 1
    has_params = method_has_param_types(m, 'UUID', 1)
    return req_map and is_get and one_param and has_anno and has_params


def is_updatebyuid_web_endpoint(m: MethodDeclaration) -> bool:
    # method RequestMethod.PUT, UUID param and @RequestBody param
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_put = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'PUT'])
    has_params = method_has_param_types(m, 'UUID', 1) and method_has_param_types(m, 'BindingResult', 1)
    has_request_body = any(list([p for p in m.parameters if get_parameter_annotation(p, 'RequestBody')]))
    return req_map and is_put and has_anno and has_params and has_request_body


def is_deletebyuid_web_endpoint(m: MethodDeclaration) -> bool:
    # method RequestMethod.DELETE, UUID param
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_deelte = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'DELETE'])
    one_param = len(m.parameters) == 1
    has_params = method_has_param_types(m, 'UUID', 1)
    return req_map and is_deelte and one_param and has_anno and has_params


def is_create_web_endpoint(m: MethodDeclaration) -> bool:
    # todo method RequestMethod.POST, one @RequestBody param
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_post = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'POST'])
    param_number = len(m.parameters) > 1
    has_params = method_has_param_types(m, 'BindingResult', 1) and not method_has_param_types(m, 'UUID', 1)
    has_request_body = any(list([p for p in m.parameters if get_parameter_annotation(p, 'RequestBody')]))
    return req_map and is_post and has_anno and has_params and has_request_body and param_number


# # # # # # # # # # # #
#  Entities associate
#
def is_associate_web_endpoint(m: MethodDeclaration) -> bool:
    # todo method RequestMethod.PUT, two UUID params
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_put = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'PUT'])
    two_params = len(m.parameters) > 1
    has_params = method_has_param_types(m, 'UUID', 2) or method_has_param_types(m, 'UUID', 3)
    return is_put and two_params and has_anno and has_params


def is_disassociate_web_endpoint(m: MethodDeclaration) -> bool:
    # todo method RequestMethod.DELETE, two UUID params
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_delete = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'DELETE'])
    two_params = len(m.parameters) > 1
    has_params = method_has_param_types(m, 'UUID', 2) or method_has_param_types(m, 'UUID', 3)
    return is_delete and two_params and has_anno and has_params


def is_create_and_associate_web_endpoint(m: MethodDeclaration) -> bool:
    # todo method RequestMethod.POST, one UUID param, one @RequestBody
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_post = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'POST'])
    params_number = len(m.parameters) > 1
    has_params = method_has_param_types(m, 'UUID', 1)
    has_request_body = any(list([p for p in m.parameters if get_parameter_annotation(p, 'RequestBody')]))
    return is_post and params_number and has_anno and has_params and has_request_body


def is_get_associations_web_endpoint(m: MethodDeclaration) -> bool:
    # todo method RequestMethod.POST, one UUID param, one @RequestBody
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_post = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'GET'])
    params_number = len(m.parameters) > 1
    has_params = method_has_param_types(m, 'UUID', 1) or method_has_param_types(m, 'UUID', 2) or method_has_param_types(m, 'UUID', 3)
    return is_post and params_number and has_anno and has_params


# # # # # # # # # # # #
#  Types CRUD
#
def is_get_type_by_key_web_endpoint(m: MethodDeclaration) -> bool:
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_get = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'GET'])
    has_key_in_mapping = any([e for e in req_map.element if e.name == 'value' and 'key'.upper() in e.value.value.upper()])
    params_number = len(m.parameters) == 1
    has_params = method_has_param_types(m, 'String', 1)
    return is_get and params_number and has_anno and has_params and has_key_in_mapping


def is_delete_type_by_key_web_endpoint(m: MethodDeclaration) -> bool:
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_delte = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'DELETE'])
    has_key_in_mapping = any([e for e in req_map.element if e.name == 'value' and 'key'.upper() in e.value.value.upper()])
    params_number = len(m.parameters) == 1
    has_params = method_has_param_types(m, 'String', 1)
    return is_delte and params_number and has_anno and has_params and has_key_in_mapping


def is_update_type_by_key_web_endpoint(m: MethodDeclaration) -> bool:
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_update = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'PUT'])
    has_key_in_mapping = any([e for e in req_map.element if e.name == 'value' and 'key'.upper() in e.value.value.upper()])
    params_number = len(m.parameters) >= 1
    has_params = method_has_param_types(m, 'String', 1) and method_has_param_types(m, 'BindingResult', 1)
    has_request_body = any(list([p for p in m.parameters if get_parameter_annotation(p, 'RequestBody')]))
    return is_update and params_number and has_anno and has_params and has_key_in_mapping and has_request_body


def is_create_type_by_key_web_endpoint(m: MethodDeclaration) -> bool:
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    is_post = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'POST'])
    params_number = len(m.parameters) == 2
    has_params = method_has_param_types(m, 'BindingResult', 1)
    has_request_body = any(list([p for p in m.parameters if get_parameter_annotation(p, 'RequestBody')]))
    return is_post and params_number and has_anno and has_params and has_request_body


# # # # # # # # # # # #
#  Types Association
#

def is_associate_type_with_entity_web_endpoint(m: MethodDeclaration) -> bool:
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    has_key_in_mapping = any([e for e in req_map.element if e.name == 'value' and 'key'.upper() in e.value.value.upper()])
    is_method = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'PUT'])
    params_number = len(m.parameters) == 2
    has_params = method_has_param_types(m, 'String', 1) and method_has_param_types(m, 'UUID', 1)
    return is_method and params_number and has_anno and has_params and has_key_in_mapping


def is_disassociate_type_with_entity_web_endpoint(m: MethodDeclaration) -> bool:
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    has_key_in_mapping = any([e for e in req_map.element if e.name == 'value' and 'key'.upper() in e.value.value.upper()])
    is_method = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'DELETE'])
    params_number = len(m.parameters) == 2
    has_params = method_has_param_types(m, 'String', 1) and method_has_param_types(m, 'UUID', 1)
    return is_method and params_number and has_anno and has_params and has_key_in_mapping


def is_get_type_associations_web_endpoint(m: MethodDeclaration) -> bool:
    has_anno = method_has_annotation(m, 'RequestMapping')
    if not has_anno:
        return False
    req_map = get_method_annotation(m, 'RequestMapping')
    has_key_in_mapping = any([e for e in req_map.element if e.name == 'value' and 'key'.upper() in e.value.value.upper()])
    is_method = any([e for e in req_map.element if e.name == 'method' and e.value.member == 'GET'])
    params_number = len(m.parameters) > 2
    has_params = method_has_param_types(m, 'String', 1) and method_has_param_types(m, 'Pageable', 1)
    has_request_body = any(list([p for p in m.parameters if get_parameter_annotation(p, 'RequestBody')]))
    return is_method and params_number and has_anno and has_params and has_request_body and has_key_in_mapping


# # # # # # # # # # # #
# annotation utils
#
def annotation_with_props_lines(name: str, props: dict, oneline: bool = False) -> [str]:
    annoprops_lines = [f'    {k} = {v}, \n' for k, v in props.items()]
    annoprops_lines[-1] = annoprops_lines[-1].replace(', \n', ' \n')
    block_lines = [f'@{name}(\n'] + \
           annoprops_lines + \
           [')\n']
    if oneline:
        the_line = []
        for i, l in enumerate(block_lines):
            if i < len(block_lines) - 1:    # last line of block
                the_line.append(l.lstrip().rstrip(' \n'))
            else:
                the_line.append(l.lstrip())
        return [''.join(the_line)]
    return block_lines


def get_annotation_property(anno: Annotation, prop_name: str = 'value', member_or_string: str = 'string') -> str:
    """ annotation properties are either a string or a 'member' (class reference or constant or something)
        'value' is always the default required property on any Java annotation """
    prop_val = [e.value.value if member_or_string == 'string' else e.member.value
                for e in anno.element if e.name == prop_name]
    if prop_val:
        return prop_val[0]
    raise Exception(f'Annotation {anno.name} has no {member_or_string} property {prop_name}')


def get_parameter_annotation(p: FormalParameter, anno: str) -> Annotation:
    annos = [a for a in p.annotations if a.name == anno]
    return annos[0] if annos else None


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


# # # # # # # # # # # #
# command line
#
def cli_simple(cmd: str, timeout: int, location: str = os.getcwd()):
    print(f'executing command: {cmd} at {location}')
    try:
        with subprocess.Popen(
                cmd, shell=True, cwd=location, universal_newlines=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        ) as p:
            o,e = p.communicate(timeout=timeout)
            if e:
                print(e)
                raise Exception(f'Execution of command {cmd} failed')
            else:
                return o
    except subprocess.CalledProcessError as err:
        print(traceback.format_exc())


def set_entities_version(version: str, repo_path: str):
    print(f'setting entities to version {version} in project {repo_path.split("/")[-1]}')
    matcher = re.compile(r'(\s*<acctmgmt.entities.version>)(.*)(</acctmgmt.entities.version>\s*\n)')
    with open(f'{repo_path}/pom.xml', 'r+') as f:
        lines = f.readlines()
        for i, l in enumerate(lines):
            match = matcher.match(l)
            if match:
                lines[i] = f'{match.group(1)}{version}{match.group(3)}'
                break
        write_file(lines, f)


def git_add_src_files(path: str):
    print(f'adding source files to staging for repo {path.split("/")[-1]}')
    return cli_simple('git add src/main/java', 1, path)


def git_add_test_files(path: str):
    print(f'adding test files to staging for repo {path.split("/")[-1]}')
    return cli_simple('git add src/test/java', 1, path)


def mvn_clean_test(path: str):
    print(f'testing jar for repo {path.split("/")[-1]}')
    return cli_simple('mvn clean test', 20, path)


def mvn_clean_compile(path: str):
    print(f'compiling repo {path.split("/")[-1]}')
    return cli_simple('mvn clean compile', 15, path)


def mvn_clean_install(path: str):
    print(f'compiling repo {path.split("/")[-1]}')
    return cli_simple('mvn clean install', 30, path)
