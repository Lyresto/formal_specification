# 形式化规约优化生成代码

> 目前仅可用于HumanEval风格的数据

- case：一些实例（均针对pluck问题生成）
- conversation：chatgpt的对话记录文件
    - code：生成和优化代码时的对话
    - refine：生成细化需求时的对话
    - specification：生成规约时的对话
    - testcase：生成测试用例时的对话
- template：一些需要在运行时组装执行的模板
- chatgpt.py：用于调用chatgpt的相关函数
- **generate.py**：主文件
- one_data.jsonl：数据文件（目前由于可行性测试）
- parse.py：一些用于解析的函数
- prompt.py：用于prompt组装

**运行时需要创建一个config.json文件**
```json
{
    "chat_gpt_key": "your_api_key",
    "python3_interpreter_path": "path_to_python.exe"
}
```