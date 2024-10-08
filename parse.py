import ast
import copy
import json
import os
import re
import subprocess
import threading
import tokenize
import warnings
from io import BytesIO
from typing import Any

from config import config, check_docker
from template.test_code import package_test_code

dataset = config["dataset"]


def parse_tokens(__code: str):
    try:
        return list(tokenize.tokenize(BytesIO(__code.encode('utf-8')).readline))[1:]
    except Exception as e:
        if len(__code.split('\n')) == 1:
            print("[ERROR] syntax error:", e)
        return parse_tokens('\n'.join(__code.split('\n')[:-1]))


def load_jsonl(path) -> list[dict]:
    with open(path, 'r', encoding='utf-8') as f:
        data = []
        for line in f:
            data.append(json.loads(line))
        return data


def jsonl_to_dict(data, key) -> dict[str, dict]:
    new_data = dict()
    for line in data:
        new_data[line[key]] = line
    return new_data


# deprecated
def check_func_param_and_return(__code, __entrypoint):
    warnings.warn("deprecated.")
    tokens = parse_tokens(__code)
    func_def_line = False
    next_is_param = False
    depth = 0
    __params = []
    for i, token in enumerate(tokens):
        if token.type == tokenize.NAME and token.string == "def" and tokens[i + 1].string == __entrypoint:
            func_def_line = True
        elif func_def_line and token.type == tokenize.OP and token.string in ["(", "["]:
            depth += 1
            if token.string == "(":
                next_is_param = True
        elif func_def_line and token.type == tokenize.OP and token.string in [")", "]"]:
            depth -= 1
        elif func_def_line and token.type == tokenize.OP and token.string == "," and depth == 1:
            next_is_param = True
        elif func_def_line and token.type == tokenize.NAME and depth == 1 and next_is_param:
            __params.append(token.string)
            next_is_param = False
        elif func_def_line and token.type in [tokenize.NEWLINE, tokenize.NL]:
            break
    return len(__params) > 1, False, __params


def get_data_info(idx, item):
    if dataset in ["humaneval", "humaneval-x"]:
        task_id = item["task_id"]
        prompt = item["prompt"]
        if dataset == "humaneval-x":
            language = task_id.split('/')[0].lower()
            if language == "rust":
                prompt = item["prompt"] + item["declaration"]
            info = parse_func_info_for_humaneval(item["declaration"], language)
            item = load_jsonl('data/humaneval.jsonl')[idx % 164]
            python_prompt = item["prompt"]
        else:
            language = "python"
            python_prompt = prompt
            info = parse_func_info_for_humaneval(
                load_jsonl('data/humaneval-x.jsonl')[656 + idx]["declaration"], language)
        standard_testcases = parse_standard_testcase(item["example_IO"])
    elif dataset == 'code_contests':
        info = {"param_names": ["case_in"], "entrypoint": None}
        task_id = item["name"]
        language = config["language_for_code_contests"]
        python_prompt = prompt = item["description"]
        standard_testcases = parse_standard_testcase(item["public_tests"])
    else:
        raise NotImplementedError()
    info.update({
        "task_id": task_id,
        "language": language,
        "prompt": prompt,
        "python_prompt": python_prompt,
        "standard_testcases": standard_testcases
    })
    return info


def parse_func_info_for_humaneval(declaration, language):
    """
    cpp: bool has_close_elements(vector<float> numbers, float threshold){
         int max_fill(vector<vector<int>> grid,int capacity){
    go: func HasCloseElements(numbers []float64, threshold float64) bool {
        func MaxFill(grid [][]int, capacity int) int {
    java: public boolean hasCloseElements(List<Double> numbers, double threshold) {
          public int maxFill(List<List<Integer>> grid, int capacity) {
    javascript: const hasCloseElements = (numbers, threshold) => {
                const maxFill = (grid, capacity) => {
    python: def has_close_elements(numbers: List[float], threshold: float) -> bool:
            def max_fill(grid, capacity):
    rust: fn has_close_elements(numbers:Vec<f32>, threshold: f32) -> bool{
          fn max_fill(grid:Vec<Vec<i32>>, capacity:i32) -> i32{
    """
    func_sign = ""
    for line in declaration.split('\n')[::-1]:
        line = line.strip()
        if len(line) == 0 or line.startswith('import ') or line.startswith('from ') or line == '"':
            continue
        func_sign = line
        break
    if language == 'cpp':
        func_sign_pattern = '^(.+?)\\s+([_\\w]+)\\s*\\((.+?)\\)\\s*\\{$'
        ret_entry_param = (1, 2, 3)
        param_pattern = '^(.+?)\\s+([_\\w]+)$'
        type_name = (1, 2)
    elif language == 'go':
        func_sign_pattern = '^func\\s+([_\\w]+)\\s*\\((.+?)\\)\\s*(.+?)\\s*\\{$'
        ret_entry_param = (3, 1, 2)
        param_pattern = '^([_\\w]+)\\s+(.+?)$'
        type_name = (2, 1)
    elif language == 'java':
        func_sign_pattern = '^public\\s+(.+?)\\s+([_\\w]+)\\s*\\((.+?)\\)\\s*\\{$'
        ret_entry_param = (1, 2, 3)
        param_pattern = '^(.+?)\\s+([_\\w]+)$'
        type_name = (1, 2)
    elif language == 'javascript':
        func_sign_pattern = '^const\\s+([_\\w]+)\\s*=\\s*\\((.+?)\\)\\s*=>\\s*\\{$'
        ret_entry_param = (-1, 1, 2)
        param_pattern = '^([_\\w]+)$'
        type_name = (-1, 1)
    elif language == 'python':
        func_sign_pattern = '^def\\s+([_\\w]+)\\s*\\((.+?)\\).*?:$'
        ret_entry_param = (-1, 1, 2)
        param_pattern = '^([_\\w]+)\\s*:?.*$'
        type_name = (-1, 1)
    # elif language == 'rust':
    #     func_sign_pattern = '^fn\\s+([_\\w]+)\\s*\\((.+?)\\)\\s*->\\s*(.+?)\\s*\\{$'
    #     ret_entry_param = (3, 1, 2)
    #     param_pattern = '^([_\\w]+)\\s*:\\s*(.+?)$'
    #     type_name = (2, 1)
    else:
        raise ValueError(f'{language} is not supported')

    matches = re.match(func_sign_pattern, func_sign)
    if ret_entry_param[0] != -1:
        ret_type = matches.group(ret_entry_param[0])
    else:
        ret_type = None
    entrypoint = matches.group(ret_entry_param[1])
    params = matches.group(ret_entry_param[2])
    param_names = []
    param_types = []
    for param in params.split(','):
        matches = re.match(param_pattern, param.strip())
        param_names.append(matches.group(type_name[1]))
        if type_name[0] != -1:
            param_types.append(matches.group(type_name[0]))
        else:
            param_types.append(None)
    return {
        "entrypoint": entrypoint,
        "param_types": param_types,
        "param_names": param_names,
        "ret_type": ret_type,
        "func_sign": func_sign
    }


def run_template(__testcases, __specification, __testcase_type, __file_name, __solution=None):
    with open(f'template/{__file_name}.txt', encoding='utf-8') as __f:
        __template = __f.read()
    __content = __template.replace(
        f"# [TO REPLACE] {__testcase_type}_testcases", f"{__testcase_type}_testcases = {__testcases}"
    )
    if __specification is not None:
        __content = __content.replace(
            "# [TO REPLACE] specification", __specification
        )
    if __solution is not None:
        __content = __content.replace(
            "# [TO REPLACE] solution", __solution
        )
    if os.path.exists(f'template/{__file_name}.py'):
        os.remove(f'template/{__file_name}.py')

    with open(f'template/{__file_name}.py', 'w+', encoding='utf-8') as __f:
        __f.write(__content)

    process = subprocess.Popen([config["python3_interpreter_path"], f"{__file_name}.py"],
                               cwd="template/", stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def terminate(__process):
        __process.terminate()
        raise RuntimeError("timeout")

    timer = threading.Timer(120, terminate, args=[process])
    timer.start()

    errs = ""
    while True:
        out = process.stdout.readline().decode('utf8').strip()
        err = process.stderr.readline().decode('utf8').strip()
        if len(re.findall('File.*?, line \\d+', err)) == 0 and len(err) > 0:
            errs += err + ', '
        if len(out) > 0 or process.poll() is not None:
            timer.cancel()
            if len(out) == 0:
                raise RuntimeError(errs)
            return ast.literal_eval(out)


def check_specification(__testcases, __specification):
    suffix = '_code_contests' if dataset == 'code_contests' else ''
    try:
        return run_template(__testcases, __specification, "standard", f"specification_check{suffix}")
    except RuntimeError as e:
        if 'MemoryError' in f'{e}':
            raise RuntimeError(e)
        return [0.0, 0.0, [(*__tc, f'{e}') for __tc in __testcases], []]


def check_generated_testcase(__testcases, __specification):
    __testcases = copy.copy(__testcases)
    if dataset == 'code_contests':
        for i, __tc in enumerate(__testcases):
            __testcases[i] = (
                [to_terminal_io(__tc[0][0])],
                [to_terminal_io(__tc[1][0])]
            )
    try:
        return run_template(__testcases, __specification, "generated", "generated_testcase_check")
    except RuntimeError:
        return [0] * len(__testcases)


# deprecated
def parse_testcase(__testcases):
    warnings.warn("deprecated.")
    try:
        parsed_testcases = run_template(extract_testcase(__testcases), None, "generated", "testcase_parse")
        if dataset == 'code_contests':
            for i, __testcase in enumerate(parsed_testcases):
                try:
                    to_terminal_io(__testcase[0])
                    to_terminal_io(__testcase[1])
                    parsed_testcases[i] = ([__testcase[0]], [__testcase[1]])
                except TypeError:
                    parsed_testcases[i] = None
            parsed_testcases = list(filter(lambda x: x is not None, parsed_testcases))
        return parsed_testcases
    except RuntimeError:
        return []


def cut_closed_parentheses(string):
    parentheses_map = {
        '(': ('(', ')'),
        '[': ('[', ']'),
        '{': ('{', '}'),
    }
    if string[0] not in parentheses_map:
        return string.split(',')[0]
    if string[0] in ['"', "'"]:
        return string[:string.find(string[0], 1) + 1]
    left_parentheses, right_parentheses = parentheses_map[string[0]]
    depth = 0
    for i, ch in enumerate(string):
        if ch == left_parentheses:
            depth += 1
        elif ch == right_parentheses:
            depth -= 1
        if depth == 0:
            return string[:i + 1]
    return ''


def parse_testcase_v2(__raw_testcases, __entrypoint):
    parsed_testcases = []
    if dataset in ['humaneval', 'humaneval-x']:
        matches = re.findall(f'\\nassert\\s+{__entrypoint}(\\(.+\\))\\s*==\\s*(.+)', '\n' + __raw_testcases)
        for match in matches:
            try:
                params = eval(match[0])
                if isinstance(params, tuple):
                    params = list(params)
                else:
                    params = [params]
                return_value = eval(cut_closed_parentheses(match[1]))
                parsed_testcases.append((params, [return_value]))
            except (SyntaxError, NameError):
                pass
    elif dataset == 'code_contests':
        matches = re.findall('<input>\n(.+?)\n</input>.*?\n.*?<output>\n(.+?)\n</output>', __raw_testcases, re.DOTALL)
        for match in matches:
            parsed_testcases.append((
                [parse_terminal_io(match[0])],
                [parse_terminal_io(match[1])]
            ))
    return parsed_testcases


def extract_testcase(__raw_testcases):
    lines = []
    found = False
    left_bracket = right_bracket = 0
    for line in __raw_testcases.split('\n'):
        if line.startswith('test_case'):
            found = True
        if found:
            lines.append(line)
            left_bracket += line.count('[')
            right_bracket += line.count(']')
        if left_bracket == right_bracket > 0:
            break
    return '\n'.join(lines)


# deprecated
def judge_code(__testcases, __specification, __solution):
    warnings.warn("deprecated.")
    try:
        return run_template(__testcases, __specification, "filtered", "code_judge", __solution)
    except RuntimeError as e:
        return [(*__tc, [None], f'{e}') for __tc in __testcases]


def remove_space(s):
    return ''.join(s.strip().split(' '))


def extract_completed_code(__raw_code, __info):
    if dataset in ['humaneval', 'humaneval-x']:
        func_sign_prefix = __info["func_sign"].split('(')[0].strip() + '('
        if __raw_code is None:
            return __raw_code
        if __info["language"] == 'python':
            __raw_code = __raw_code.strip('\n')
            if __raw_code.startswith('    ') or __raw_code.startswith('\t'):
                __raw_code = __info["func_sign"] + '\n' + __raw_code
            completed_code_with_func_sign = extract_function(__raw_code, __info["entrypoint"], __info["param_names"])
            return '\n'.join(completed_code_with_func_sign.split('\n')[1:])
        else:
            lineno = 0
            for lineno, line in enumerate(__raw_code.split('\n')):
                if remove_space(func_sign_prefix) in remove_space(line) and '`' not in line:
                    break
            filtered_lines = __raw_code.split('\n')[lineno + 1:]
            left_braces = 1
            right_braces = 0
            final_lines = []
            for line in filtered_lines:
                final_lines.append(line)
                left_braces += line.count('{')
                right_braces += line.count('}')
                if left_braces == right_braces:
                    break
            if __info["language"] in ['java']:
                final_lines.append('}')
            return '\n'.join(final_lines)
    elif dataset == 'code_contests':
        if '```' in __raw_code:
            try:
                return re.findall('```.*?\n(.+?)```', __raw_code, flags=re.DOTALL)[0]
            except IndexError:
                return re.findall('```.*?\n(.*)', __raw_code, flags=re.DOTALL)[0]
        return __raw_code


def judge_code_v2(__testcases, __specification, __raw_code, __info):
    docker_base_dir = "/workspace/CodeGeeX"
    cur_path = os.path.abspath('.').replace('\\', '/').replace(':', '')
    cur_path = '/' + cur_path[0].lower() + cur_path[1:]
    language = 'js' if __info["language"] == 'javascript' else __info["language"]
    solution_outputs: list = [None] * len(__testcases)
    if dataset in ["humaneval", "humaneval-x"]:
        if dataset == "humaneval":
            task_id = f'Python/{__info["task_id"].split("/")[1]}'
        else:
            task_id = __info["task_id"]
        completed_code = extract_completed_code(__raw_code, __info)
        test_code = package_test_code(__testcases, __info)
        with open('result/tmp/tmp.jsonl', 'w+') as f:
            json.dump({"task_id": task_id, "completion": completed_code, "test_code": test_code}, f)
        cmd = ["docker", "run", "--gpus", "all",
               "-v", f"{cur_path}/result/tmp/tmp.jsonl:{docker_base_dir}/data.jsonl",
               "-v", f"{cur_path}/humaneval-x/codegeex/benchmark/execution.py:"
                     f"{docker_base_dir}/codegeex/benchmark/execution.py",
               "-v", f"{cur_path}/humaneval-x/codegeex/benchmark/evaluate_humaneval_x.py:"
                     f"{docker_base_dir}/codegeex/benchmark/humaneval-x/evaluate_humaneval_x.py",
               "rishubi/codegeex", "bash", "-c",
               f'{docker_base_dir}/scripts/evaluate_humaneval_x.sh {docker_base_dir}/data.jsonl {language} 4']
        check_docker()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        while True:
            out = process.stdout.readline().decode('utf8').strip()
            # err = process.stderr.readline().decode('utf8').strip()
            if out.startswith('[SOLUTION OUTPUT') or process.poll() is not None:
                if out.startswith('[SOLUTION OUTPUT'):
                    matches = re.match('\\[SOLUTION OUTPUT (\\d+)] (.*)', out)
                    output = matches.group(2).strip()
                    try:
                        solution_outputs[int(matches.group(1))] = ast.literal_eval(output)
                    except ValueError:
                        output = output.replace('true', 'True')
                        output = output.replace('false', 'False')
                        solution_outputs[int(matches.group(1))] = ast.literal_eval(output)
                else:
                    break
        triphase_testcases = [(*tc, [sol_out]) for tc, sol_out in zip(__testcases, solution_outputs)]
    elif dataset == 'code_contests':
        testcases_str = []
        for tc_input, tc_output in __testcases:
            testcases_str.append([to_terminal_io(tc_input[0]), to_terminal_io(tc_output[0])])
        task_id = f'{__info["language"]}/{__info["task_id"]}'
        completed_code = extract_completed_code(__raw_code, __info)
        with open('result/tmp/tmp.jsonl', 'w+') as f:
            json.dump({"task_id": task_id, "test_code": completed_code, "testcases": testcases_str}, f)
        cmd = ["docker", "run", "--gpus", "all",
               "-v", f"{cur_path}/result/tmp/tmp.jsonl:{docker_base_dir}/data.jsonl",
               "-v", f"{cur_path}/humaneval-x/codegeex/benchmark/execution_code_contests.py:"
                     f"{docker_base_dir}/codegeex/benchmark/execution.py",
               "-v", f"{cur_path}/humaneval-x/codegeex/benchmark/evaluate_code_contests.py:"
                     f"{docker_base_dir}/codegeex/benchmark/humaneval-x/evaluate_humaneval_x.py",
               "rishubi/codegeex", "bash", "-c",
               f'{docker_base_dir}/scripts/evaluate_humaneval_x.sh {docker_base_dir}/data.jsonl {language} 4']
        check_docker()
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True, text=True)
        out, err = process.communicate()
        for idx in range(len(__testcases)):
            matches = re.findall(f'<TESTCASE OUTPUT {idx}>\n(.*?)\n</TESTCASE OUTPUT {idx}>', out, flags=re.DOTALL)
            assert len(matches) <= 1
            if len(matches) == 1:
                solution_outputs[idx] = parse_terminal_io(matches[0].strip())
        triphase_testcases = [([tc[0]], [tc[1]], [to_terminal_io(sol_out)]) for tc, sol_out in
                              zip(testcases_str, solution_outputs)]
    else:
        raise NotImplementedError()
    try:
        return run_template(triphase_testcases, __specification, "triphase", "code_judge_2"), completed_code
    except RuntimeError:
        return [], completed_code


def fix_code(__code):
    indent = ["if", "elif", "else", "for", "while", "def", "try", "except"]
    coll = [",", "(", "[", "{", "\\", ":"]
    codes = __code.split("\n")
    up_space = 0
    up_ident = False
    up_collection = False
    in_note = False
    for i in range(len(codes)):
        c = codes[i]
        if c.strip() == 'if __name__ == "__main__":':
            codes = codes[: i]
            break
        cur_space = len(c) - len(c.lstrip())
        if (c.strip().startswith("'''") or c.strip().startswith("\"\"\"")) and not in_note:
            in_note = True
            continue
        elif (c.strip().endswith("'''") or c.strip().endswith("\"\"\"")) and in_note:
            in_note = False
            continue
        if len(c.strip()) == 0 or c.strip().startswith('#') or in_note:
            continue
        if (up_ident and cur_space - up_space != 4) or \
                (not up_ident and cur_space > up_space and not up_collection):
            if up_ident:
                dist = up_space + 4 - cur_space
            else:
                dist = up_space - cur_space
            for j in range(i, len(codes)):
                if dist > 0:
                    codes[j] = ''.join([' '] * dist) + codes[j]
                else:
                    space = len(codes[j]) - len(codes[j].lstrip())
                    codes[j] = codes[j][min(abs(dist), space):]
        c = codes[i]
        up_space = len(c) - len(c.lstrip())
        up_ident = any(c.strip().startswith(ide) for ide in indent)
        up_collection = any(c.strip().endswith(col_) for col_ in coll)
    return '\n'.join(codes)


def extract_function(__content, __func_name, __param_names=None):
    if '```' in __content:
        try:
            blocks = re.findall('```.*?\n(.+?)```', __content, flags=re.DOTALL)
        except IndexError:
            blocks = re.findall('```.*?\n(.*)', __content, flags=re.DOTALL)
    else:
        blocks = [__content]
    __content = '\n' + '\n'.join(blocks)
    functions = list(map(lambda f: 'def ' + f, __content.split('\ndef ')[1:]))
    candidate_functions = list(filter(lambda f: f.startswith('def ' + __func_name + '('), functions))
    other_functions = list(filter(lambda f: not f.startswith('def ' + __func_name + '('), functions))
    if len(candidate_functions) == 0:
        raise ValueError(f'No such function: {__func_name}')
    if config['select_type'] == 'last':
        chosen_func = candidate_functions[-1]
    elif config['select_type'] == 'first':
        chosen_func = candidate_functions[0]
    else:
        raise NotImplementedError()

    lines = chosen_func.split('\n')
    if __param_names is not None:
        code_param_names = parse_func_info_for_humaneval(chosen_func.split('\n')[0], 'python')['param_names']
        if __param_names != code_param_names and len(code_param_names) == len(__param_names):
            tokens = parse_tokens(chosen_func)
            replace_pos = {}
            for i, token in enumerate(tokens[1:]):
                if token.type == tokenize.NAME and token.string in code_param_names:
                    replaced_name = __param_names[code_param_names.index(token.string)]
                    # print(replaced_line[0:token.start[1]])
                    if token.start[0] - 1 not in replace_pos:
                        replace_pos[token.start[0] - 1] = []
                    replace_pos[token.start[0] - 1].append((token.start[1], token.end[1], replaced_name))
            for lineno, pos in replace_pos.items():
                pos = sorted(pos, key=lambda x: x[0])
                line = lines[lineno]
                new_line = ''
                pos_lst = [0]
                for start, end, _ in pos:
                    pos_lst.append(start)
                    pos_lst.append(end)
                pos_lst.append(len(line))
                for __i in range(len(pos_lst) - 1):
                    if __i % 2 == 0:
                        new_line += line[pos_lst[__i]:pos_lst[__i + 1]]
                    else:
                        new_line += pos[__i // 2][2]
                lines[lineno] = new_line

    import_lines = list(filter(lambda l: l.startswith('import ') or l.startswith('from '), __content.split('\n')))
    if len(lines) <= 1:
        space = 0
    elif lines[1].startswith(' '):
        space = len(lines[1]) - len(lines[1].lstrip())
    else:
        space = (len(lines[1]) - len(lines[1].lstrip())) * 4
    if len(other_functions) > 0:
        other_functions = '\n\n' + '\n'.join(import_lines) + '\n\n' + '\n\n'.join(other_functions)
    else:
        other_functions = ''
    import_lines = list(set(map(lambda l: ''.join([' '] * space) + l, import_lines)))
    extract_code = '\n'.join([lines[0]] + import_lines + lines[1:]) + other_functions
    extract_code = re.sub(r'print\(.*', 'pass', extract_code)
    return extract_code


def extract_specification(__content):
    return '\n\n'.join([extract_function(__content, "preconditions"), extract_function(__content, "postconditions")])


def parse_standard_testcase(__testcase):
    standard_testcase = []
    for tc_input, tc_output in zip(__testcase["input"], __testcase["output"]):
        if dataset in ['humaneval', 'humaneval-x']:
            standard_testcase.append((
                ast.literal_eval(f'[{tc_input}]'),
                ast.literal_eval(f'[{tc_output}]')
            ))
        elif dataset == 'code_contests':
            standard_testcase.append((
                [parse_terminal_io(tc_input)],
                [parse_terminal_io(tc_output)]
            ))
    return standard_testcase


def parse_terminal_io(io: str):
    parsed_io = []

    def __convert_str_2_var(s):
        try:
            return ast.literal_eval(s)
        except (SyntaxError, ValueError):
            return s

    for line in io.split('\n'):
        if len(line.strip()) == 0:
            continue
        parsed_io.append(list(map(__convert_str_2_var, filter(lambda s: len(s) > 0, line.split(' ')))))
    return parsed_io


def to_terminal_io(io: list[list[Any]], inline=False):
    if io is None:
        return None
    if inline:
        join_str = '\\n'
    else:
        join_str = '\n'
    return join_str.join(' '.join(str(elem) for elem in line) for line in io)

if __name__ == '__main__':
    code = '''
ewofh
```python
def f(x, yy):
    import sys
    a = g(yy)
    return a * yy + x - yy
    
import typing  
    
def g():
    return 1
```

eoivjo, wef
```
def f(x, yy):
    print(111)
    return 112 + yy

print(f(1, 2
```
efc
    '''
    dataset = 'humaneval'
    print(extract_completed_code(code, {
        'entrypoint': 'f',
        'param_names': ['x', 'y205'],
        'func_sign': 'def f(x, y205):',
        'language': 'python',
    }))
    # print(to_terminal_io([[1, 2], ["qqq"]]))
    # print(parse_func_info_for_humaneval("fn max_fill(grid:Vec<Vec<i32>>, capacity:i32) -> i32{", "rust"))
    # print(ast.literal_eval("[([[1, 3, 5]], []),([[2, 4, 6]], [[2, 0]])]"))
    # exit(-1)
    # print(check_func_param_and_return("def f(a: List, b, c: tuple[List, List]):", "f"))
    # print('\n'.join(str(it) for it in parse_tokens(st)))
    # exit(-1)
    # with open('case/1spec.txt') as f:
    #     spec = f.read()
    #     print(extract_function(spec, "postcondition"))
    # exit(-1)
    # with open('one_data.jsonl') as f:
    #     for line in f:
    #         data = json.loads(line)
    #         multi_param, multi_return, params = check_func_param_and_return(data["prompt"], data["entry_point"])
    #         with open('case/1testcase.txt') as f1:
    #             testcase = f1.read()
    #             print(parse_testcase(testcase))
    pass
