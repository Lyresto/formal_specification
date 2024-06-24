import ast
import copy
import random
import re
from typing import Any, Set, List, Dict, Tuple
import math


def get_step_num():
    choose_num = random.randint(0, 2 ** max_step - 2)
    for choose_step in range(max_step, 0, -1):
        if choose_num <= (2 ** (max_step - choose_step) - 1) * 2:
            return choose_step


def generate_improper_testcases(case_in, case_out):
    case_in = copy.copy(case_in)
    case_out = copy.copy(case_out)
    while (case_in, case_out) in standard_testcases:
        for __i in range(len(case_in)):
            case_in[__i] = filter_empty(randomly_modify_single(case_in[__i], steps=get_step_num()))
        for __i in range(len(case_out)):
            case_out[__i] = filter_empty(randomly_modify_single(case_out[__i], steps=get_step_num()))
    return case_in, case_out


def filter_empty(var):
    var = list(filter(lambda x: not isinstance(x, list) or len(x) > 0, var))
    for i, it in enumerate(var):
        if isinstance(it, list):
            var[i] = list(filter(lambda x: x != '', it))
    return var


printable_ch = [chr(ch) for ch in range(32, 127)]
base_data = [0, 0.0, "", False, None]


def unique_length(it):
    return len(set([str(i) for i in it]))


def get_seed_data(it):
    it = list(it)
    if len(it) >= 1:
        return it[random.randint(0, len(it) - 1)]
    else:
        return base_data[random.randint(0, len(base_data) - 1)]


def randomly_modify_single(var: Any, is_character=False, steps=1):
    var = copy.copy(var)
    if steps > 1:
        var = randomly_modify_single(var, steps=steps - 1)
    if random.randint(0, int(1 / keep_rate) - 1) == 0:
        return var
    if var is None:
        return 0
    if isinstance(var, str):
        if len(var) == 1 and is_character:
            new_ch_idx = random.randint(0, len(printable_ch) - 2)
            if new_ch_idx >= printable_ch.index(var):
                new_ch_idx += 1
            return printable_ch[new_ch_idx]
        else:
            new_str = randomly_modify_single(list(var), True)
            if new_str is None or None in new_str:
                return None
            return ''.join(new_str)
    if isinstance(var, bool):
        return not var
    if isinstance(var, int):
        candidate = list({var - 1, var + 1, var - 2, var + 2, -var, var * 2, var // 2, 0} - {var})
        return candidate[random.randint(0, len(candidate) - 1)]
    if isinstance(var, float):
        decimal_len = len(str(var).split('.')[1])
        min_unit = 10 ** -decimal_len
        candidate = list({var - 1, var + 1, var - 2, var + 2, var + 5 * min_unit, var - 5 * min_unit,
                          var + min_unit, var - min_unit, round(var, decimal_len - 1),
                          -var, var * 2, var / 2, 0} - {var})
        return round(candidate[random.randint(0, len(candidate) - 1)], decimal_len)

    # 增、修改、删、交换
    if (isinstance(var, list) or isinstance(var, tuple)) and unique_length(var) >= 2:
        candidate = [1, 1, 1, 1]
        if isinstance(var, tuple) and len(var) == 2:
            candidate = [1, 1, 0, 1]
    elif (not isinstance(var, tuple) and len(var) >= 1) or (isinstance(var, tuple) and len(var) not in [0, 2]):
        candidate = [1, 1, 1, 0]
    elif len(var) >= 1:
        candidate = [1, 1, 0, 0]
    else:
        candidate = [1, 0, 0, 0]

    index = random.randint(0, sum(candidate) - 1)
    operation = 0
    for op, sign in enumerate(candidate):
        if sign == 1:
            if index == 0:
                operation = op
                break
            index -= 1

    empty = random.randint(0, int(1 / empty_rate) - 1) == 0 and len(var) > 0

    if isinstance(var, list) or isinstance(var, tuple):
        origin_type = type(var)
        if isinstance(var, tuple):
            var = list(var)
        if empty:
            var = []
        elif operation == 0:
            for _ in range(2 if origin_type == tuple and len(var) == 0 else 1):
                if is_character:
                    seed_data = " "
                else:
                    seed_data = get_seed_data(var)
                insert_index = random.randint(0, len(var))
                var.insert(insert_index, randomly_modify_single(seed_data, is_character))
        elif operation == 1:
            update_index = random.randint(0, len(var) - 1)
            var[update_index] = randomly_modify_single(var[update_index], is_character)
        elif operation == 2:
            del var[random.randint(0, len(var) - 1)]
        else:
            unique_set_str = list(set([str(item) for item in var]))
            swap_indexes = random.sample(range(len(unique_set_str)), 2)
            for i, index in enumerate(swap_indexes):
                for j, item in enumerate(var):
                    if str(item) == unique_set_str[index]:
                        swap_indexes[i] = j
                        break
            assert str(var[swap_indexes[0]]) != str(var[swap_indexes[1]])
            var[swap_indexes[0]], var[swap_indexes[1]] = var[swap_indexes[1]], var[swap_indexes[0]]
        if origin_type == tuple:
            var = tuple(var)
        return var
    if isinstance(var, set):
        if empty:
            var = {}
        elif operation == 0:
            length = len(var)
            while len(var) == length:
                seed_data = get_seed_data(var)
                var.add(randomly_modify_single(seed_data))
        elif operation == 1:
            lst = list(var)
            update_index = random.randint(0, len(lst) - 1)
            lst[update_index] = randomly_modify_single(lst[update_index])
            var = set(lst)
        else:
            lst = list(var)
            var.remove(lst[random.randint(0, len(lst) - 1)])
        return var
    if isinstance(var, dict):
        if empty:
            var = dict()
        elif operation == 0:
            while True:
                key_seed_data = get_seed_data(var.keys())
                value_seed_data = get_seed_data(var.values())
                new_key = randomly_modify_single(key_seed_data)
                if new_key in var:
                    continue
                var[new_key] = randomly_modify_single(value_seed_data)
                break
        elif operation == 1:
            lst = list(var.items())
            update_index = random.randint(0, len(lst) - 1)
            var[lst[update_index][0]] = randomly_modify_single(lst[update_index][1])
        else:
            lst = list(var.keys())
            del var[lst[random.randint(0, len(lst) - 1)]]
        return var
    else:
        raise NotImplementedError()


standard_testcases = [
    ([[4], [1000000000, 1000000], [1000000000, 1000000], [100000000, 1000000], [1000000000, 1000000]],
     [[1000000000, 1000999999], [1, 1000000], [100000000, 100999999], [1000001, 2000000]]),
    ([[3], [9, 2], [7, 3], [2, 4]], [[9, 10], [1, 3], [4, 7]])
]

test_cases = [
    # basic function test cases
    ([[5], [6, 2], [10, 1], [10, 2], [9, 2], [5, 1]],
     [[6, 7], [10, 10], [1, 2], [3, 4], [5, 5]]),
    ([[2], [10, 3], [9, 2]],
     [[10, 12], [1, 2]]),
    ([[1], [1, 5000000]],
     [[1, 5000000]]),
    # special situation test cases
    ([[1], [1, 1]],
     [[1, 1]]),
    ([[1], [1000000000, 1]],
     [[1000000000, 1000000000]]),
    ([[1], [1000000000, 5000000]],
     [[1000000000, 1004999999]]),
    # boundary and stress test cases
    ([[30], [522692116, 84], [589719489, 488], [662495181, 961], [915956552, 470], [683572975, 271], [498400137, 480],
      [327010963, 181], [200704287, 367], [810826488, 54], [978100746, 208], [345455616, 986], [106372142, 876],
      [446972337, 42], [309349333, 200], [93462198, 543], [167946793, 318], [325598940, 427], [121873339, 459],
      [174934933, 598], [279521023, 655], [739750520, 3], [870850765, 192], [622303167, 400], [471234786, 63],
      [805952711, 18], [349834333, 857], [804873364, 302], [512746562, 39], [533285962, 561], [996718586, 494]],
     [[522692116, 522692199], [589719489, 589719976], [662495181, 662496141], [915956552, 915957021],
      [683572975, 683573245], [498400137, 498400616], [327010963, 327011143], [200704287, 200704653],
      [810826488, 810826541], [978100746, 978100953], [345455616, 345456601], [106372142, 106373017],
      [446972337, 446972378], [309349333, 309349532], [93462198, 93462740], [167946793, 167947110],
      [325598940, 325599366], [121873339, 121873797], [174934933, 174935530], [279521023, 279521677],
      [739750520, 739750522], [870850765, 870850956], [622303167, 622303566], [471234786, 471234848],
      [805952711, 805952728], [349834333, 349835189], [804873364, 804873665], [512746562, 512746600],
      [533285962, 533286522], [996718586, 996719079]]),

    # random test cases
    ([[10], [588, 12], [560, 10], [593, 14], [438, 15], [761, 11], [984, 6], [503, 2], [855, 19], [538, 2], [650, 7]],
     [[588, 599], [560, 569], [1, 14], [438, 452], [761, 771], [984, 989], [503, 504], [855, 873], [538, 539],
      [650, 656]]),
    ([[10], [1, 3], [77, 8], [46, 5], [83, 4], [61, 7], [8, 4], [54, 7], [80, 7], [33, 7], [13, 4]],
     [[1, 3], [77, 84], [46, 50], [4, 7], [61, 67], [8, 11], [54, 60], [12, 18], [33, 39], [19, 22]]),
    ([[20], [360, 26], [475, 17], [826, 12], [815, 23], [567, 28], [897, 26], [707, 20], [1000, 9], [576, 5], [16, 5],
      [714, 16], [630, 17], [426, 26], [406, 23], [899, 25], [102, 22], [896, 8], [320, 27], [964, 25], [932, 18]],
     [[360, 385], [475, 491], [826, 837], [1, 23], [567, 594], [897, 922], [707, 726], [1000, 1008], [24, 28], [29, 33],
      [34, 49], [630, 646], [426, 451], [50, 72], [73, 97], [102, 123], [124, 131], [320, 346], [964, 988],
      [932, 949]]),
]


def preconditions(case_in):
    assert isinstance(case_in, str), "Input is not a string."
    lines = case_in.split('\n')
    assert len(lines[0]) == 1, "The first line of input should only contain one element."
    assert lines[0][0].isdigit(), "n should be integer."
    n = int(lines[0][0])
    assert 1 <= n <= 200, "n is not within the given range"
    assert n == len(lines) - 1, "The input lines is not n+1"
    requests = lines[1:]
    for idx, output in enumerate(requests):
        request = output.split(' ')
        assert len(request) == 2, f"The {idx + 1}th request should only contain two elements."
        for element in request:
            assert element.isdigit(), f"The {idx + 1}th request contains non-integer element {element}."

        s, d = tuple(request)
        s = int(s)
        d = int(d)
        assert 1 <= s <= 1e9, f"The s of {idx + 1}th request is not within the given range."
        assert 1 <= d <= 5e6, f"The d of {idx + 1}th request is not within the given range."


def postconditions(case_in, case_out):
    assert isinstance(case_out, str), "Output is not a string."
    case_in_lines = case_in.split('\n')
    case_out_lines = case_out.split('\n')
    n = int(case_in_lines[0][0])
    assert n == len(case_out_lines), "The number of output lines should be n."
    for idx, results in enumerate(case_out_lines):

        start_day = results.split(' ')[0]
        finish_day = results.split(' ')[1]
        assert start_day.isdigit(), f"The start day to repair the {idx + 1}th car should be integer."
        assert finish_day.isdigit(), f"The finish day to repair the {idx + 1}th car should be integer."
        start_day = int(start_day)
        finish_day = int(finish_day)
        assert start_day <= finish_day, f"The {idx + 1}th request's start day should be earlier than finish day."
        if start_day != case_in_lines[idx + 1][0]:
            assert any(int(output_result.split(' ')[0]) == 1 for output_result in
                       case_out_lines), f"If there is a car which expected start repair time is not equal to the actual start repair time, then there must be a car which actual start repair time is 1."

    case_out_lines.sort(key=lambda x: x[0])
    for i in range(len(case_out_lines) - 1):
        assert case_out_lines[i][1] < case_out_lines[i + 1][
            0], f"A car's actual finish repair time {case_out_lines[i][1]} and the other car's actual start repair time {case_out_lines[i + 1][0]} overlap."


def validate_test_cases(case_in, case_out):
    try:
        preconditions(*case_in)
        postconditions(*case_in, *case_out)
        return 1, ""
    except Exception as e:
        return 0, f"{e}"


def parse_terminal_io(io: str):
    if not isinstance(io, str):
        return io
    parsed_io = []

    def __convert_str_2_var(s):
        try:
            return ast.literal_eval(s)
        except ValueError:
            return s
        except SyntaxError:
            return s

    for line in io.split('\n'):
        if len(line.strip()) == 0:
            continue
        parsed_io.append(list(map(__convert_str_2_var, filter(lambda s: len(s) > 0, line.split(' ')))))
    return parsed_io


def to_terminal_io(io: list[list[Any]]):
    try:
        return '\n'.join(' '.join(str(elem) for elem in line) for line in io)
    except TypeError:
        return to_terminal_io([io])


if __name__ == '__main__':
    generate_num_per_testcase = 10000
    empty_rate = 0.1
    keep_rate = 0.2
    max_step = 4

    pass_num_proper = 0
    pass_num_improper = 0
    proper_testcase_error_message = []
    improper_testcase_pass_spec = []
    case_out_set = set()
    different_case_in_cnt = 0
    if len(standard_testcases) == 0:
        print([1.0, 1.0, [], []])
    for testcase in standard_testcases:
        result, message = validate_test_cases([to_terminal_io(testcase[0][0])], [to_terminal_io(testcase[1][0])])
        if result == 0:
            proper_testcase_error_message.append((*testcase, message))
        pass_num_proper += result
        for _ in range(generate_num_per_testcase):
            improper_testcase = generate_improper_testcases(*testcase)
            if improper_testcase[0] != testcase[0]:
                different_case_in_cnt += 1
            case_out_set.add(str(improper_testcase[1]))
            improper_testcase = ([to_terminal_io(improper_testcase[0][0])], [to_terminal_io(improper_testcase[1][0])])
            result, _ = validate_test_cases(*improper_testcase)
            if result == 1 and improper_testcase not in improper_testcase_pass_spec:
                improper_testcase_pass_spec.append(improper_testcase)
            pass_num_improper += result
    collision_rate = different_case_in_cnt / (generate_num_per_testcase * len(standard_testcases)) / len(case_out_set)
    random_testcase_pass_rate = 1 - pass_num_improper / (generate_num_per_testcase * len(standard_testcases))
    print([pass_num_proper / len(standard_testcases),
           min(1.0, random_testcase_pass_rate + 1.5 * collision_rate),
           proper_testcase_error_message,
           random.sample(improper_testcase_pass_spec, min(5, len(improper_testcase_pass_spec)))
           if len(improper_testcase_pass_spec) > 0 else []])
