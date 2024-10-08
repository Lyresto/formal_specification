import json
import os.path
import pandas as pd

from chatgpt import start_conversation, load_intermediate_results
from config import config
from parse import check_generated_testcase, extract_specification, check_specification, parse_testcase, \
    load_jsonl, get_data_info, judge_code_v2, parse_testcase_v2
from prompts import specification_prompt, requirement_refine_prompt, testcase_prompt, code_prompt_for_iteration, \
    natural_language_specification_prompt, constraints_modify_prompt_for_proper_testcase, \
    constraints_modify_prompt_for_improper_testcase, initial_prompt

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


def get_python_specification(idx, turn, count, param_names, example_testcase, conversation_context):
    conversation = start_conversation(
        save_path=f'conversation/{middle_path}/python-specification/{idx}-{turn}-{count}.pkl',
        load_if_exist=True
    )
    assert len(conversation.messages) in [0, 4]
    if len(conversation.messages) == 0:
        conversation.messages = conversation_context
        specification = conversation.chat(specification_prompt(None, param_names, example_testcase=example_testcase,
                                                               has_nl_specification=True))
    else:
        specification = conversation.messages[-1]["content"]
    return extract_specification(specification)


def get_specifications(idx, prompt, standard_testcase, param_names):
    specifications = []
    refine_threshold = 3
    break_threshold = 3
    max_specification = 10
    example_testcase = standard_testcase[0] if len(standard_testcase) > 0 else None
    for turn in range(2):
        specification_count = 0
        conversation_count = 0
        standard_testcase_not_pass_count = []
        refine = False
        if turn == 1:
            log("Refine!!")
        while specification_count < max_specification:
            conversation = start_conversation(
                save_path=f'conversation/{middle_path}/nl-specification/{idx}-{turn}-{conversation_count}.pkl',
                load_if_exist=True
            )
            specification_metric_within_conversation = []
            if len(conversation.messages) > 0:
                for j in range(1, len(conversation.messages) - 1, 2):
                    specification = get_python_specification(idx, turn, specification_count,
                                                             param_names, example_testcase,
                                                             [conversation.messages[0], conversation.messages[j]])
                    check_result = check_specification(standard_testcase, specification)
                    specifications.append((specification, check_result))
                    log("specification check result:", check_result)
                    specification_count += 1
                    standard_testcase_not_pass_count.append(int(check_result[0] != 1.0))
                    specification_metric_within_conversation.append(str(check_result[:2]))
            else:
                refined_description = ""
                if turn == 1:
                    refine_conversation = start_conversation(
                        save_path=f'conversation/{middle_path}/refine/{idx}.pkl',
                        load_if_exist=True
                    )
                    if len(refine_conversation.messages) > 0:
                        refined_description = refine_conversation.messages[-1]["content"]
                    else:
                        refined_description = refine_conversation.chat(requirement_refine_prompt(prompt))

                conversation.chat(natural_language_specification_prompt(prompt, refined_description))

            while True:
                specification = get_python_specification(idx, turn, specification_count,
                                                         param_names, example_testcase,
                                                         [conversation.messages[0], conversation.messages[-1]])
                check_result = check_specification(standard_testcase, specification)
                specifications.append((specification, check_result))
                log("specification check result:", check_result)
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
                    conversation.chat(
                        constraints_modify_prompt_for_proper_testcase(param_names, check_result[2]),
                        [0, -1]
                    )
                elif check_result[1] != 1.0:
                    conversation.chat(constraints_modify_prompt_for_improper_testcase(
                        param_names,
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


def get_generated_testcase(idx, prompt, standard_testcase, entrypoint):
    max_trials = 5
    trials = 0
    minimum_testcases = 5
    while True:
        conversation = start_conversation(
            save_path=f'conversation/{middle_path}/testcase/{idx}-{trials}.pkl', load_if_exist=True
        )
        if len(conversation.messages) > 0:
            raw_testcase = conversation.messages[-1]["content"]
        else:
            raw_testcase = conversation.chat(
                testcase_prompt(prompt, standard_testcase[0] if len(standard_testcase) > 0 else None)
            )
        raw_testcase = parse_testcase_v2(raw_testcase, entrypoint)
        trials += 1
        if len(raw_testcase) >= minimum_testcases or trials >= max_trials:
            break
    # log(raw_testcase)
    generated_testcase = remove_duplicate_testcase(raw_testcase)
    return generated_testcase


def get_solution(idx, info, specification, generate_testcases):
    prompt = info["prompt"]
    param_names = info["param_names"]

    max_generation = 10
    codes = []
    conversation = start_conversation(
        save_path=f'conversation/{middle_path}/code/{idx}.pkl', load_if_exist=True
    )
    count = 0
    if len(conversation.messages) > 0:
        for i in range(1, len(conversation.messages) - 1, 2):
            code = conversation.messages[i]["content"]
            judge_result, comp_code = judge_code_v2(generate_testcases, specification, code, info)
            log("failed testcases:", judge_result)
            codes.append((comp_code, 1 - len(judge_result) / len(generate_testcases)))
            count += 1
        code = conversation.messages[-1]["content"]
    else:
        code = conversation.chat(initial_prompt(prompt, info["language"]))
    while True:
        judge_result, comp_code = judge_code_v2(generate_testcases, specification, code, info)
        log("failed testcases:", judge_result)
        if len(generate_testcases) != 0:
            codes.append((comp_code, 1 - len(judge_result) / len(generate_testcases)))
        else:
            codes.append((comp_code, 1.0))
        count += 1
        if count == max_generation or codes[-1][1] == 1.0:
            break
        code = conversation.chat(code_prompt_for_iteration(param_names, judge_result), [0, -1])
    best_code = max(codes, key=lambda x: x[1])
    return {
        "generation": best_code[0],
        "pass_rate": best_code[1],
        "generation_times": count,
        "initial_pass_rate": codes[0][1]
    }


def main():
    global item_idx
    for item_idx, item in enumerate(data):
        if item[task_key] in completions:
            log('skip')
            continue

        # if item_idx < 29:
        #     continue

        # if not item["task_id"].startswith('Java'):
        #     continue
        # if int(item["task_id"].split('/')[1]) >= 3:
        #     break
        log('starts generation')

        info = get_data_info(item_idx, item)
        python_prompt = info["python_prompt"]
        standard_testcases = info["standard_testcases"]

        intermediate_results = load_intermediate_results(f'conversation/{middle_path}/intermediate/{item_idx}.pkl')
        if not intermediate_results.has_results():
            generated_testcase = get_generated_testcase(item_idx, python_prompt, standard_testcases, info["entrypoint"])
            specifications = get_specifications(item_idx, python_prompt, standard_testcases, info["param_names"])
            final_specification, filtered_testcases = \
                choose_specification_and_testcase(specifications, generated_testcase)
            intermediate_results.save(final_specification, filtered_testcases)
        else:
            log("use cached intermediate results")
            final_specification = intermediate_results.specification
            filtered_testcases = intermediate_results.testcases

        log("filtered testcases:", filtered_testcases)
        final_testcases = remove_duplicate_testcase(filtered_testcases + standard_testcases)

        solution_info = get_solution(item_idx, info, final_specification, final_testcases)
        log('pass rate =', solution_info["pass_rate"])

        with open(result_path, 'a') as result_file:
            generation_result = {task_key: info["task_id"]}
            generation_result.update(solution_info)
            result_file.write(f'{json.dumps(generation_result)}\n')


if __name__ == '__main__':
    source_data_path = config["data_path"]
    dataset = config["dataset"]
    model = config["model"]

    print("Config:\n", json.dumps(config, indent=4))

    if dataset in ['humaneval', 'humaneval-x']:
        data = load_jsonl(source_data_path)
        task_key = "task_id"
        middle_path = f'{dataset}/{model}'
        result_path = f'result/{dataset}_{model}.jsonl'
    elif dataset == 'code_contests':
        data = pd.read_parquet(source_data_path).to_dict(orient='records')
        task_key = "name"
        language = config["language_for_code_contests"]
        middle_path = f'{dataset}/{model}/{language}'
        result_path = f'result/{dataset}_{model}_{language}.jsonl'
    else:
        raise NotImplementedError()
    completions = set()
    if os.path.exists(result_path):
        with open(result_path) as f:
            for line in f:
                if line.strip() != "":
                    completions.add(json.loads(line)[task_key])
    main()
