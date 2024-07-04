import ast
import json
import os
import re
import subprocess
import pandas as pd
from tqdm import tqdm

import config
from parse import load_jsonl, jsonl_to_dict


def evaluate():
    test_file_str = ""
    check_results = dict()
    for item in generation:
        if item[task_key].split('/')[0].lower() == language or dataset == 'code_contests':
            check_results[item[task_key]] = []
            if dataset in ['humaneval', 'humaneval-x']:
                test_file_str += json.dumps({"task_id": item[task_key], "completion": item["generation"],
                                             "test_code": data[item[task_key]]["test"]}) + "\n"
            elif dataset in ['code_contests']:
                testcase = data[item[task_key]]["generated_tests"]
                test_file_str += json.dumps({"task_id": f'{language}/{item[task_key]}', "test_code": item["generation"],
                                             "testcases": list(zip(testcase["input"], testcase["output"]))}) + "\n"
    with open('result/tmp/tmp.jsonl', 'w+') as f:
        f.write(test_file_str)

    docker_base_dir = "/workspace/CodeGeeX"
    cur_path = os.path.abspath('.').replace('\\', '/').replace(':', '')
    cur_path = '/' + cur_path[0].lower() + cur_path[1:]
    if dataset in ['humaneval', 'humaneval-x']:
        cmd = ["docker", "run", "--gpus", "all",
               "-v", f"{cur_path}/result/tmp/tmp.jsonl:{docker_base_dir}/data.jsonl",
               "-v", f"{cur_path}/humaneval-x/codegeex/benchmark/execution.py:"
                     f"{docker_base_dir}/codegeex/benchmark/execution.py",
               "-v", f"{cur_path}/humaneval-x/codegeex/benchmark/evaluate_humaneval_x.py:"
                     f"{docker_base_dir}/codegeex/benchmark/humaneval-x/evaluate_humaneval_x.py",
               "rishubi/codegeex", "bash", "-c",
               f'{docker_base_dir}/scripts/evaluate_humaneval_x.sh {docker_base_dir}/data.jsonl {language} 4']
    elif dataset == 'code_contests':
        cmd = ["docker", "run", "--gpus", "all",
               "-v", f"{cur_path}/result/tmp/tmp.jsonl:{docker_base_dir}/data.jsonl",
               "-v", f"{cur_path}/humaneval-x/codegeex/benchmark/execution_code_contests.py:"
                     f"{docker_base_dir}/codegeex/benchmark/execution.py",
               "-v", f"{cur_path}/humaneval-x/codegeex/benchmark/evaluate_code_contests.py:"
                     f"{docker_base_dir}/codegeex/benchmark/humaneval-x/evaluate_humaneval_x.py",
               "rishubi/codegeex", "bash", "-c",
               f'{docker_base_dir}/scripts/evaluate_humaneval_x.sh {docker_base_dir}/data.jsonl {language} 1']
    else:
        raise NotImplementedError()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    bar = tqdm(desc='Evaluating... ', total=len(generation))
    while True:
        out = process.stdout.readline().decode('utf8').strip()
        # print(out)
        if out.startswith('[RESULT') or process.poll() is not None:
            if out.startswith('[RESULT'):
                matches = re.match('\\[RESULT_(.*?)] (.*)', out)
                task_id = matches.group(1).strip()
                output = ast.literal_eval(matches.group(2).strip())
                check_results[task_id].extend(output)
                bar.update(len(output))
            else:
                break
    print(f'Write evaluation results to {result_path}.')
    with open(result_path, 'w+') as f:
        json.dump(check_results, f, indent=4)
    bar.close()


if __name__ == '__main__':
    # Config
    dataset = 'code_contests'
    language = 'python'
    generation_path = 'result/code_contests_gpt-3.5-turbo_python.jsonl'

    if dataset in ['humaneval', 'humaneval-x']:
        data_path = f'data/{dataset}.jsonl'
        task_key = "task_id"
        result_path = f'{".".join(generation_path.split(".")[:-1])}_{language}_result.json'
        data = jsonl_to_dict(load_jsonl(data_path), task_key)
    elif dataset == 'code_contests':
        data_path = f'data/code_contests/testset.parquet'
        task_key = "name"
        result_path = f'{".".join(generation_path.split(".")[:-1])}_result.json'
        data = jsonl_to_dict(pd.read_parquet(data_path).to_dict(orient='records'), task_key)
    else:
        raise NotImplementedError()
    generation = load_jsonl(generation_path)

    evaluate()
