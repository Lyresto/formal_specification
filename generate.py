import json
import os.path

from chatgpt import start_conversation
from parse import check_generated_testcase, extract_specification, check_specification, parse_testcase, \
    assemble_solution, judge_code, parse_standard_testcase, check_func_param_and_return
from prompts import specification_prompt, requirement_refine_prompt, specification_modify_prompt_for_proper_testcase, \
    specification_modify_prompt_for_improper_testcase, testcase_prompt, code_prompt_for_iteration
from config import config

item_idx = 0


def log(*values):
    print(f'[INFO ITEM {item_idx}]', *values)


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
    alpha = 0.6
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
    # log(score_for_standard_testcase, score_for_improper_testcase)
    return [(__specifications[i][0], alpha * it[0] + (1 - alpha) * it[1]) for i, it in
            enumerate(zip(score_for_standard_testcase, score_for_improper_testcase))]


def choose_specification_and_testcase(__specifications, __testcases):
    __specifications = calculate_score_for_specification(__specifications)
    __check_results = []
    for __specification, _ in __specifications:
        __check_results.append(check_generated_testcase(__testcases, __specification))
        log("testcase pass specification:", __check_results[-1])
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
    log("specification scores:", dual_scores)
    max_index = dual_scores.index(max(dual_scores))
    log("best specification index:", max_index)
    return __specifications[max_index][0], \
        [__tc for __i, __tc in enumerate(__testcases) if __check_results[max_index][__i] == 1]


def get_specifications(idx, prompt, standard_testcase, params):
    # with open('case/10spec.json') as f:
    #     specifications = json.load(f)
    # for specification in specifications:
    #     check_result = check_specification(standard_testcase, specification)
    #     log(check_result)
    #     log(specification_modify_prompt_for_improper_testcase(params, remove_duplicate_testcase(check_result[3])))
    # exit(-1)
    specifications = []
    refine_threshold = 3
    break_threshold = 3
    max_specification = 10
    for turn in range(2):
        specification_count = 0
        conversation_count = 0
        standard_testcase_not_pass_count = []
        refine = False
        if turn == 1:
            log("Refine!!")
        while specification_count < max_specification:
            conversation = start_conversation(
                save_path=f'conversation/{conversation_path}/specification/{idx}-{turn}-{conversation_count}.pkl',
                load_if_exist=True
            )
            specification_metric_within_conversation = []
            if len(conversation.messages) > 0:
                for j in range(1, len(conversation.messages) - 1, 2):
                    specification = extract_specification(conversation.messages[j]["content"])
                    check_result = check_specification(standard_testcase, specification)
                    specifications.append((specification, check_result))
                    log(check_result)
                    specification_count += 1
                    standard_testcase_not_pass_count.append(int(check_result[0] != 1.0))
                    specification_metric_within_conversation.append(str(check_result[:2]))
                specification = conversation.messages[-1]["content"]
            else:
                refined_description = ""
                if turn == 1:
                    refine_conversation = start_conversation(
                        save_path=f'conversation/{conversation_path}/refine/{idx}.pkl',
                        load_if_exist=True
                    )
                    if len(refine_conversation.messages) > 0:
                        refined_description = refine_conversation.messages[-1]["content"]
                    else:
                        refined_description = refine_conversation.chat(requirement_refine_prompt(prompt))
                specification = conversation.chat(specification_prompt(prompt, refined_description))

            while True:
                specification = extract_specification(specification)
                check_result = check_specification(standard_testcase, specification)
                specifications.append((specification, check_result))
                log(check_result)
                specification_count += 1
                standard_testcase_not_pass_count.append(int(check_result[0] != 1.0))
                specification_metric_within_conversation.append(str(check_result[:2]))
                if check_result[:2] == [1.0, 1.0] or specification_count >= max_specification:
                    break
                if sum(standard_testcase_not_pass_count) >= refine_threshold and \
                        0 not in standard_testcase_not_pass_count[:refine_threshold] and turn == 0:
                    refine = True
                    break
                if len(specification_metric_within_conversation) >= break_threshold and \
                        len(set(specification_metric_within_conversation[-3:])) == 1:
                    log(f"{break_threshold} continuously same specifications!")
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
    return specifications


def get_generated_testcase(idx, prompt, standard_testcase):
    conversation = start_conversation(
        save_path=f'conversation/{conversation_path}/testcase/{idx}.pkl', load_if_exist=True
    )
    if len(conversation.messages) > 0:
        raw_testcase = conversation.messages[-1]["content"]
    else:
        raw_testcase = conversation.chat(
            testcase_prompt(prompt, standard_testcase[0] if len(standard_testcase) > 0 else None)
        )
    # log(raw_testcase)
    generated_testcase = remove_duplicate_testcase(parse_testcase(raw_testcase))
    # exit(-1)
    # with open('case/1testcase.txt') as f:
    #     generated_testcase = parse_testcase(f.read())
    # generated_testcase = remove_duplicate_testcase(generated_testcase)
    return generated_testcase


def get_solution(idx, prompt, entrypoint, specification, generate_testcases, params):
    max_generation = 10
    codes = []
    conversation = start_conversation(
        save_path=f'conversation/{conversation_path}/code/{idx}.pkl', load_if_exist=True
    )
    count = 0
    if len(conversation.messages) > 0:
        for i in range(1, len(conversation.messages) - 1, 2):
            code = conversation.messages[i]["content"]
            solution = assemble_solution(prompt, code, entrypoint)
            judge_result = judge_code(generate_testcases, specification, solution)
            log(judge_result)
            codes.append((code, 1 - len(judge_result) / len(generate_testcases)))
            count += 1
        code = conversation.messages[-1]["content"]
    else:
        code = conversation.chat(prompt)
    while True:
        solution = assemble_solution(prompt, code, entrypoint)
        judge_result = judge_code(generate_testcases, specification, solution)
        log(judge_result)
        codes.append((code, 1 - len(judge_result) / len(generate_testcases)))
        count += 1
        if count == max_generation or codes[-1][1] == 1.0:
            break
        code = conversation.chat(code_prompt_for_iteration(params, judge_result), [0, -1])
    best_code = max(codes, key=lambda x: x[1])
    return best_code


def main():
    global item_idx
    for item_idx, item in enumerate(data):
        if item_idx < completions:
            log('skip')
            continue
        if item_idx >= 58:
            break
        log('starts generation')
        # standard_testcase = [
        #     ([[4, 2, 3]], [[2, 1]]),
        #     ([[1, 2, 3]], [[2, 1]]),
        #     ([[]], [[]]),
        #     ([[5, 0, 3, 0, 4, 2]], [[0, 1]])
        # ]
        # standard_testcase = [
        #     ([3], [[3, 5, 7]]),
        #     ([2], [[2, 4]])
        # ]
        # standard_testcase = [(["Example"], ["Example"]), (["Example 1"], ["Example_1"]),
        #                      ([" Example 2"], ["_Example_2"]),
        #                      ([" Example   3"], ["_Example-3"])]
        # standard_testcase = [([[[0,0,1,0], [0,1,0,0], [1,1,1,1]], 1], [6]),
        #                      ([[[0,0,1,1], [0,0,0,0], [1,1,1,1], [0,1,1,1]], 2], [5]),
        #                      ([[[0,0,0], [0,0,0]], 5], [0])]
        standard_testcase = parse_standard_testcase(item["example_IO"])
        prompt = item["prompt"]
        entrypoint = item["entry_point"]
        task_id = item["task_id"]
        multi_param, multi_return, params = check_func_param_and_return(prompt, entrypoint)

        generated_testcase = get_generated_testcase(item_idx, prompt, standard_testcase)
        specifications = get_specifications(item_idx, prompt, standard_testcase, params)

        final_specification, filtered_testcases = choose_specification_and_testcase(specifications, generated_testcase)
        log("filtered testcases:", filtered_testcases)
        final_testcases = remove_duplicate_testcase(filtered_testcases + standard_testcase)

        best_code, ps_rate = get_solution(item_idx, prompt, entrypoint, final_specification, final_testcases, params)
        log('pass rate =', ps_rate)

        with open(result_path, 'a') as result_file:
            result_file.write(f'{json.dumps({"task_id": task_id, "completion": best_code})}\n')


if __name__ == '__main__':
    source_data_path = config["data_path"]
    conversation_path = f'{config["dataset"]}/{config["model"]}'
    result_path = f'result/{config["dataset"]}_{config["model"]}.jsonl'

    with open(source_data_path) as f:
        data = []
        for line in f:
            data.append(json.loads(line))
    completions = 0
    if os.path.exists(result_path):
        with open(result_path) as f:
            for line in f:
                if line.strip() != "":
                    completions += 1
    main()
