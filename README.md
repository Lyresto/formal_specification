# 形式化规约优化生成代码

> 目前仅可用于HumanEval(-X)

- case：一些调试用实例（均针对pluck问题生成）
- conversation：chatgpt的对话记录文件（运行时生成）
    - code：生成和优化代码时的对话
    - intermediate：中间结果（包括规约和筛选之后的测试用例）
    - refine：生成细化需求时的对话
    - specification：生成规约时的对话
    - testcase：生成测试用例时的对话
- data：数据文件夹（目前用于可行性测试）
- humaneval-x：一些docker挂载文件
- result：结果保存文件夹
- template：一些在主进程运行时组装执行的模板
- chatgpt.py：用于调用chatgpt的相关函数
- config.py：用于配置加载
- **generate.py**：主文件
- parse.py：一些用于解析的函数
- prompts.py：用于prompt组装

**运行时需要创建一个config.json文件**
```json
{
    "chat_gpt_key": "your_api_key",
    "python3_interpreter_path": "path_to_python.exe",
    "model": "gpt-3.5-turbo-0613",
    "dataset": "humaneval",
    "language_for_code_contests": "java",
    "data_path": "data/humaneval.jsonl"
}
```

以及docker相关配置
1. 安装docker
2.  ```shell
    docker pull rishubi/codegeex:latest
    ```