import os
import subprocess

from chatgpt import *
from parse import *
from prompts import *

source_data_path = 'one_data.jsonl'

data = []
with open(source_data_path) as f:
    for line in f:
        data.append(json.loads(line))


def check_specification(__testcases, __specification):
    try:
        return run_template(__testcases, __specification, "standard", "specification_check")
    except RuntimeError:
        return 0.0, 0.0, [], []


def check_generated_testcase(__testcases, __specification):
    try:
        return run_template(__testcases, __specification, "generated", "generated_testcase_check")
    except RuntimeError:
        return [0] * len(__testcases)


def remove_duplicate_testcase(__testcases):
    str_set = set()
    after_remove = []
    for tc in __testcases:
        str_tc = str(tc)
        if str_tc not in str_set:
            after_remove.append(tc)
            str_set.add(str_tc)
    return after_remove


def calculate_score_for_specification(__specifications):
    alpha = 0.9
    score_for_standard_testcase = []
    score_for_improper_testcase = []
    for _, __check_result in __specifications:
        score_for_standard_testcase.append(__check_result[0])
        score_for_improper_testcase.append(__check_result[1])

    def __normalize(lst):
        if max(lst) == min(lst):
            return [1] * len(lst)
        return [(it - min(lst)) / (max(lst) - min(lst)) for it in lst]

    score_for_standard_testcase = __normalize(score_for_standard_testcase)
    score_for_improper_testcase = __normalize(score_for_improper_testcase)
    # print(score_for_standard_testcase, score_for_improper_testcase)
    return [(__specifications[i][0], alpha * it[0] + (1 - alpha) * it[1]) for i, it in
            enumerate(zip(score_for_standard_testcase, score_for_improper_testcase))]


def choose_specification_and_testcase(__specifications, __testcases):
    __specifications = calculate_score_for_specification(__specifications)
    __check_results = []
    for __specification, _ in __specifications:
        __check_results.append(check_generated_testcase(__testcases, __specification))
        print(__check_results[-1])
    result_dict = dict()
    for __it in __check_results:
        str_it = str(__it)
        if str_it not in result_dict:
            result_dict[str_it] = 1
        else:
            result_dict[str_it] += 1
    dual_scores = []
    for __i, __it in enumerate(__check_results):
        dual_scores.append(__specifications[__i][1] * sum(__it) * result_dict[str(__it)])
    print(dual_scores)
    max_index = dual_scores.index(max(dual_scores))
    print(max_index)
    return __specifications[max_index], \
        [__tc for __i, __tc in enumerate(__testcases) if __check_results[max_index][__i] == 1]


for idx, item in enumerate(data):
    standard_testcase = [
        ([[4, 2, 3]], [[2, 1]]),
        ([[1, 2, 3]], [[2, 1]]),
        ([[]], [[]]),
        ([[5, 0, 3, 0, 4, 2]], [[0, 1]])
    ]
    prompt = item["prompt"]
    entrypoint = item["entry_point"]
    multi_param, multi_return, params = check_func_param_and_return(prompt, entrypoint)

    # conversation = start_conversation(save_path=f'conversation/testcase/{idx}.pkl')
    # # print(testcase_prompt(item["prompt"]))
    # raw_testcase = conversation.chat(testcase_prompt(item["prompt"], standard_testcase[0]))
    # print(raw_testcase)
    # exit(-1)
    with open('case/1testcase.txt') as f:
        generated_testcase = parse_testcase(f.read())
    generated_testcase = remove_duplicate_testcase(generated_testcase)

    # with open('case/10spec.json') as f:
    #     specifications = json.load(f)
    # for specification in specifications:
    #     check_result = check_specification(standard_testcase, specification)
    #     print(check_result)
    #     print(specification_modify_prompt_for_improper_testcase(params, remove_duplicate_testcase(check_result[3])))
    # exit(-1)
    specifications = []
    refine_threshold = 3
    max_amount = 10
    for turn in range(2):
        specification_count = 0
        conversation_count = 0
        standard_testcase_not_pass_count = []
        refine = False
        if turn == 1:
            print("refine!!")
        while specification_count < max_amount:
            conversation = start_conversation(
                save_path=f'conversation/specification/{idx}-{turn}-{conversation_count}.pkl',
                load_if_exist=True
            )
            if len(conversation.messages) > 0:
                for j in range(1, len(conversation.messages) - 1, 2):
                    specification = extract_specification(conversation.messages[j]["content"])
                    check_result = check_specification(standard_testcase, specification)
                    specifications.append((specification, check_result))
                    print(check_result)
                    specification_count += 1
                    standard_testcase_not_pass_count.append(int(check_result[0] != 1.0))
                specification = conversation.messages[-1]["content"]
            else:
                refined_description = ""
                if turn == 1:
                    refine_conversation = start_conversation(save_path=f'conversation/refine/{idx}.pkl', load_if_exist=True)
                    if len(refine_conversation.messages) > 0:
                        refined_description = refine_conversation.messages[-1]["content"]
                    else:
                        refined_description = refine_conversation.chat(requirement_refine_prompt(prompt))
                specification = conversation.chat(specification_prompt(prompt, refined_description))
            while True:
                specification = extract_specification(specification)
                check_result = check_specification(standard_testcase, specification)
                specifications.append((specification, check_result))
                print(check_result)
                specification_count += 1
                standard_testcase_not_pass_count.append(int(check_result[0] != 1.0))
                if check_result[:2] == [1.0, 1.0] or specification_count == max_amount:
                    break
                if sum(standard_testcase_not_pass_count) >= refine_threshold and \
                        0 not in standard_testcase_not_pass_count[:refine_threshold] and turn == 0:
                    refine = True
                    break
                if check_result[0] != 1.0:
                    specification = conversation.chat(
                        specification_modify_prompt_for_proper_testcase(params, check_result[2]),
                        [0, -1]
                    )
                elif check_result[1] != 1.0:
                    specification = conversation.chat(
                        specification_modify_prompt_for_improper_testcase(
                            params,
                            remove_duplicate_testcase(check_result[3])
                        ),
                        [0, -1]
                    )
            if refine:
                break
            conversation_count += 1
        if refine:
            specifications = []
        else:
            break

    final_specification, filtered_testcases = choose_specification_and_testcase(specifications, generated_testcase)
    print(len(filtered_testcases))

    # with open('case/10spec.json', 'w+') as f:
    #     json.dump(specifications, f)
