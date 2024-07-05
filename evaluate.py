import ast
import json
import os
import re
import subprocess
import threading
import time
from collections import Counter
from typing import Union

import pandas as pd
from tqdm import tqdm

import config
from parse import load_jsonl, jsonl_to_dict


class Timer:
    lock = threading.Lock()

    def __init__(self, seconds, info):
        self.lock.acquire()
        self.bar = tqdm(desc=f'Time Costed ({info})', unit='s', total=seconds)
        self.info = info

        def run():
            while True:
                if self.signum == 0:
                    return
                time.sleep(1)
                self.bar.update(1)

        self.signum = 1
        self.thread = threading.Thread(target=run)
        self.thread.setDaemon(True)
        self.thread.start()

    def close(self):
        self.signum = 0
        self.bar.close()
        print(f'Evaluation of {self.info} ends, {remains} remaining.')
        self.lock.release()


def evaluate():
    test_file_str = ""
    global remains
    if os.path.exists(result_path):
        with open(result_path) as f:
            check_results = json.load(f)
    else:
        check_results = dict()
    counter = Counter()
    for item in generation:
        task_id = item[task_key]
        if task_id.split('/')[0].lower() == language or dataset == 'code_contests':
            if task_id not in check_results:
                check_results[task_id] = []
            completion_id = counter[task_id]
            while len(check_results[task_id]) <= completion_id:
                check_results[task_id].append(None)
            if check_results[task_id][completion_id] is None:
                if dataset in ['humaneval', 'humaneval-x']:
                    test_file_str += json.dumps({"task_id": task_id, "completion": item["generation"],
                                                 "completion_id": completion_id,
                                                 "test_code": data[task_id]["test"]}) + "\n"
                elif dataset in ['code_contests']:
                    testcase = data[task_id]["generated_tests"]
                    test_file_str += json.dumps({"task_id": f'{language}/{task_id}', "test_code": item["generation"],
                                                 "completion_id": completion_id,
                                                 "testcases": list(zip(testcase["input"], testcase["output"]))}) + "\n"
            else:
                remains -= 1
            counter[task_id] += 1
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
               f'{docker_base_dir}/scripts/evaluate_humaneval_x.sh {docker_base_dir}/data.jsonl {language} 1']
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
    timer = None
    while True:
        out = process.stdout.readline().decode('utf8').strip()
        # err = process.stderr.readline().decode('utf8').strip()
        # print(out)
        if out.startswith('[RESULT') or out.startswith('timeout =') or process.poll() is not None:
            if out.startswith('timeout ='):
                matches = re.match('timeout = (.+?)_(.+)', out)
                timer = Timer(int(float(matches.group(1))), matches.group(2))
            elif out.startswith('[RESULT'):
                matches = re.match('\\[RESULT_(.+)_(.+?)] (.*)', out)
                task_id = matches.group(1).strip()
                completion_id = int(matches.group(2).strip())
                output = ast.literal_eval(matches.group(3).strip())
                check_results[task_id][completion_id] = output[0]
                with open(result_path, 'w+') as f:
                    json.dump(check_results, f, indent=4)
                remains -= len(output)
                timer.close()
            else:
                break
    print(f'Write evaluation results to {result_path}.')
    with open(result_path, 'w+') as f:
        json.dump(check_results, f, indent=4)


if __name__ == '__main__':
    # Config
    dataset = 'code_contests'
    language = 'python'
    generation_path = 'result/code_contests_gpt-3.5-turbo_python.jsonl'
    print(f'Evaluate {generation_path} of {dataset} dataset using {language} language.')

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
    remains = len(generation)

    evaluate()
