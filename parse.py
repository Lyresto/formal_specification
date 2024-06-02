import ast
import os
import re
import subprocess
import tokenize
from io import BytesIO
from config import config


def parse_tokens(__code: str):
    try:
        return list(tokenize.tokenize(BytesIO(__code.encode('utf-8')).readline))[1:]
    except Exception as e:
        print("[ERROR] syntax error:", e)
        return [""]


def check_func_param_and_return(__code, __entrypoint):
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
    errs = ""
    while True:
        out = process.stdout.readline().decode('utf8').strip()
        err = process.stderr.readline().decode('utf8').strip()
        if len(re.findall('File.*?, line \\d+', err)) == 0 and len(err) > 0:
            errs += err + ', '
        if len(out) > 0 or process.poll() is not None:
            if len(out) == 0:
                raise RuntimeError(errs)
            return ast.literal_eval(out)


def check_specification(__testcases, __specification):
    try:
        return run_template(__testcases, __specification, "standard", "specification_check")
    except RuntimeError as e:
        return [0.0, 0.0, [(*__tc, f'{e}') for __tc in __testcases], []]


def check_generated_testcase(__testcases, __specification):
    try:
        return run_template(__testcases, __specification, "generated", "generated_testcase_check")
    except RuntimeError:
        return [0] * len(__testcases)


def parse_testcase(__testcases):
    return run_template(__testcases, None, "generated", "testcase_parse")


def judge_code(__testcases, __specification, __solution):
    try:
        return run_template(__testcases, __specification, "filtered", "code_judge", __solution)
    except RuntimeError as e:
        return [(*__tc, [None], f'{e}') for __tc in __testcases]


def assemble_solution(__prompt, __code, __entrypoint):
    func_in_prompt = extract_function(__prompt, __entrypoint, keep_intact=True)
    if f'def {__entrypoint}(' not in __code:
        func_sign = list(filter(lambda l: l.startswith('def '), func_in_prompt.split('\n')))[0]
        __code = fix_code(f'{func_sign}\n{__code}')
    func_in_code = extract_function(__code, __entrypoint)
    return f"{__prompt.replace(func_in_prompt, func_in_code)}\n\ncandidate = {__entrypoint}"


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


def extract_function(__content, __func_name, keep_intact=False):
    tokens = parse_tokens(__content)
    start = [(0, 0)]
    end = [(0, 0)]
    indents = 0
    find_func = False
    for i, token in enumerate(tokens[1:]):
        if token.type == tokenize.NAME and token.string == __func_name and tokens[i].string == 'def':
            find_func = True
            start.append(tokens[i].start)
        elif find_func and token.type == tokenize.INDENT:
            indents += 4
        elif find_func and token.type == tokenize.DEDENT:
            indents -= 4
            if indents == 0:
                end.append(token.start)
                find_func = False
    lines = __content.split('\n')[start[-1][0] - 1: end[-1][0] - 1]
    if keep_intact:
        return '\n'.join(lines)
    lines = list(filter(lambda l: not l.strip().startswith('print('), lines))
    import_lines = list(filter(lambda l: l.startswith('import ') or l.startswith('from '), __content.split('\n')))
    return '\n'.join(import_lines + lines)


def extract_specification(__content):
    return '\n\n'.join([extract_function(__content, "preconditions"), extract_function(__content, "postconditions")])


def parse_standard_testcase(__testcase):
    standard_testcase = []
    for tc_input, tc_output in zip(__testcase["input"], __testcase["output"]):
        standard_testcase.append((
            ast.literal_eval(f'[{tc_input}]'),
            ast.literal_eval(f'[{tc_output}]')
        ))
    return standard_testcase


if __name__ == '__main__':
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
