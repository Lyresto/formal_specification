import ast
import json
import os
import subprocess
import tokenize
from io import BytesIO


with open('config.json') as f:
    config = json.load(f)


def parse_tokens(__code: str):
    return list(tokenize.tokenize(BytesIO(__code.encode('utf-8')).readline))[1:]


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


def run_template(__testcases, __specification, __testcase_type, __file_name):
    with open(f'template/{__file_name}.txt', encoding='utf-8') as __f:
        __template = __f.read()
    __content = __template.replace(
        f"# [TO REPLACE] {__testcase_type}_testcases", f"{__testcase_type}_testcases = {__testcases}"
    )
    if __specification is not None:
        __content = __content.replace(
            "# [TO REPLACE] specification", __specification
        )
    if os.path.exists(f'template/{__file_name}.py'):
        os.remove(f'template/{__file_name}.py')

    with open(f'template/{__file_name}.py', 'w+', encoding='utf-8') as __f:
        __f.write(__content)

    process = subprocess.Popen([config["python3_interpreter_path"],
                                f"{__file_name}.py"], cwd="template/", stdout=subprocess.PIPE)
    while True:
        out = process.stdout.readline().decode('utf8').strip()
        if len(out) > 0 or process.poll() is not None:
            if len(out) == 0:
                raise RuntimeError
            return ast.literal_eval(out)


def parse_testcase(__testcases):
    return run_template(__testcases, None, "generated", "testcase_parse")


def extract_function(__content, __func_name):
    content_list = list(__content + ' ')
    start = __content.find(f'def {__func_name}')
    for i in range(start, len(content_list)):
        if content_list[i] == '\n' and content_list[i + 1] not in ['\n', '\t', ' ']:
            return ''.join(content_list[start:i])
    return ''.join(content_list[start:])


def extract_specification(__content):
    return '\n\n'.join([extract_function(__content, "precondition"), extract_function(__content, "postcondition")])


if __name__ == '__main__':
    # print(ast.literal_eval("[([[1, 3, 5]], []),([[2, 4, 6]], [[2, 0]])]"))
    # exit(-1)
    # print(check_func_param_and_return("def f(a: List, b, c: tuple[List, List]):", "f"))
    # print(parse_tokens("it = 'is bad'"))
    # exit(-1)
    # with open('case/1spec.txt') as f:
    #     spec = f.read()
    #     print(extract_function(spec, "postcondition"))
    # exit(-1)
    with open('one_data.jsonl') as f:
        for line in f:
            data = json.loads(line)
            multi_param, multi_return, params = check_func_param_and_return(data["prompt"], data["entry_point"])
            with open('case/1testcase.txt') as f1:
                testcase = f1.read()
                print(parse_testcase(testcase))
