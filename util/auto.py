import os
import subprocess
import traceback
import re
import util.util


def cli_simple(cmd: str, timeout: int, location: str = os.getcwd()):
    print('executing command: ' + ' '.join(cmd) + ' at ' + location)
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
        util.util.write_file(lines, f)


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

