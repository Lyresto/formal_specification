cpp_atom_types = ['int', 'float', 'double', 'string', 'bool']
go_atom_types = ['int', 'float32', 'float64', 'string', 'bool']
java_atom_types = ['int', 'float', 'double', 'String', 'boolean',
                   'Integer', 'Float', 'Double', 'Boolean']
python_atom_types = [int, float, str, bool]
rust_atom_types = ['i32', 'f32', 'f64', 'String', 'bool']


def spaces(length):
    return ''.join([' '] * length)


def get_item_type_for_cpp(ori_type):
    return ori_type[ori_type.find('<') + 1:-1].strip()


def print_output_for_cpp(ret_type: str, top=False):
    function = f'void print_output({ret_type} output, int index) {{\n'
    if top:
        function += spaces(4) + 'cout << "\\n[SOLUTION OUTPUT " << index << "] ";\n'
    if ret_type in cpp_atom_types:
        if ret_type == 'string':
            function += spaces(4) + 'cout << "\\\"" << output << "\\\"";\n'
        else:
            function += spaces(4) + 'cout << output;\n'
        item_type = None
    elif ret_type.startswith('vector'):
        item_type = get_item_type_for_cpp(ret_type)
        function += spaces(4) + 'cout << "[";\n'
        function += spaces(4) + f'for (int i = 0; i < output.size(); i++) {{\n'
        function += spaces(8) + 'print_output(output[i], -1);\n'
        function += spaces(8) + 'if (i != output.size() - 1) {\n'
        function += spaces(12) + 'cout << ", ";\n'
        function += spaces(8) + '}\n'
        function += spaces(4) + '}\n'
        function += spaces(4) + 'cout << "]";\n'
    else:
        raise NotImplementedError()
    if top:
        function += spaces(4) + 'cout << "\\n";\n'
    function += '}\n\n\n'
    if item_type is not None:
        function = print_output_for_cpp(item_type) + function
    return function


def convert_param_for_cpp(param_type: str, param_value):
    if param_type in cpp_atom_types:
        if param_type == 'string':
            return f'"{param_value}"'
        if param_type == 'bool':
            return str(param_value).lower()
        return str(param_value)
    if param_type.startswith('vector'):
        param = "{"
        for i, item in enumerate(param_value):
            item_type = get_item_type_for_cpp(param_type)
            param += convert_param_for_cpp(item_type, item)
            if i != len(param_value) - 1:
                param += ", "
        param += "}"
        return param
    raise NotImplementedError()


def package_test_code_for_cpp(testcases, entrypoint, param_types: list[str], ret_type: str):
    test_code = print_output_for_cpp(ret_type, True) + '#undef NDEBUG\nint main() {\n'
    for i, tc in enumerate(testcases):
        test_code += spaces(4) + 'try {\n'
        params = []
        for param_value, param_type in zip(tc[0], param_types):
            params.append(convert_param_for_cpp(param_type, param_value))
        test_code += spaces(8) + f'print_output({entrypoint}({", ".join(params)}), {i});\n'
        test_code += spaces(4) + '} catch (const exception& e) { }\n'
    test_code += '}\n'
    return test_code


def get_item_type_for_go(ori_type):
    return ori_type[ori_type.find(']') + 1:].strip()


def print_output_for_go(ret_type: str, depth=0):
    function = f'func PrintOutput{depth}(output {ret_type}, index int) {{\n'
    if depth == 0:
        function += spaces(4) + 'fmt.Printf("\\n[SOLUTION OUTPUT %v] ", index)\n'
    if ret_type in go_atom_types:
        if ret_type == 'string':
            function += spaces(4) + 'fmt.Printf("\\\"%v\\\"", output)\n'
        else:
            function += spaces(4) + 'fmt.Printf("%v", output)\n'
        item_type = None
    elif ret_type.startswith('['):
        item_type = get_item_type_for_go(ret_type)
        function += spaces(4) + 'fmt.Printf("[")\n'
        function += spaces(4) + f'for i, item := range output {{\n'
        function += spaces(8) + f'PrintOutput{depth + 1}(item, -1)\n'
        function += spaces(8) + 'if i != len(output) - 1 {\n'
        function += spaces(12) + 'fmt.Printf(", ")\n'
        function += spaces(8) + '}\n'
        function += spaces(4) + '}\n'
        function += spaces(4) + 'fmt.Printf("]")\n'
    else:
        raise NotImplementedError()
    if depth == 0:
        function += spaces(4) + 'fmt.Printf("\\n")\n'
    function += '}\n\n\n'
    if item_type is not None:
        function = print_output_for_go(item_type, depth + 1) + function
    return function


def convert_param_for_go(param_type: str, param_value, top=False):
    if param_type in go_atom_types:
        if param_type == 'string':
            return f'"{param_value}"'
        if param_type == 'bool':
            return str(param_value).lower()
        return str(param_value)
    if param_type.startswith('['):
        if top:
            param = f'{param_type}{{'
        else:
            param = "{"
        for i, item in enumerate(param_value):
            item_type = get_item_type_for_go(param_type)
            param += convert_param_for_go(item_type, item)
            if i != len(param_value) - 1:
                param += ", "
        param += "}"
        return param
    raise NotImplementedError()


def safe_test_single_case_for_go(entrypoint, param_names, param_types: list[str]):
    function = f'func SafeTest({", ".join([" ".join(it) for it in zip(param_names, param_types)])}, __index int) {{\n'
    function += spaces(4) + 'defer func() {\n'
    function += spaces(8) + 'if r := recover(); r != nil { }\n'
    function += spaces(4) + '}()\n\n'
    function += spaces(4) + f'PrintOutput0({entrypoint}({", ".join(param_names)}), __index)\n'
    function += '}\n\n\n'
    return function


def package_test_code_for_go(testcases, entrypoint, param_types: list[str], ret_type: str, param_names):
    test_code = print_output_for_go(ret_type, 0) + \
                safe_test_single_case_for_go(entrypoint, param_names, param_types) + \
                'func main() {\n'
    for p_name, p_type in zip(param_names, param_types):
        test_code += spaces(4) + f'var {p_name} {p_type}\n'
    for i, tc in enumerate(testcases):
        for param_value, param_name, param_type in zip(tc[0], param_names, param_types):
            test_code += spaces(4) + f'{param_name} = {convert_param_for_go(param_type, param_value, True)}\n'
        test_code += spaces(4) + f'SafeTest({", ".join(param_names)}, {i})\n'
    test_code += '}\n'
    return test_code


def get_item_type_for_java(ori_type):
    return ori_type[ori_type.find('<') + 1:-1].strip()


def print_output_for_java(ret_type: str, top=False):
    function = spaces(4) + f'public static void printOutput({ret_type} output, int index) {{\n'
    if top:
        function += spaces(8) + 'System.out.printf("\\n[SOLUTION OUTPUT %d] ", index);\n'
    if ret_type in java_atom_types:
        if ret_type == 'String':
            function += spaces(8) + 'System.out.printf("\\\"%s\\\"", output);\n'
        else:
            function += spaces(8) + 'System.out.print(output);\n'
        item_type = None
    elif ret_type.startswith('List'):
        item_type = get_item_type_for_java(ret_type)
        function += spaces(8) + 'System.out.print("[");\n'
        function += spaces(8) + f'for (int i = 0; i < output.size(); i++) {{\n'
        function += spaces(12) + 'printOutput(output.get(i), -1);\n'
        function += spaces(12) + 'if (i != output.size() - 1) {\n'
        function += spaces(16) + 'System.out.print(", ");\n'
        function += spaces(12) + '}\n'
        function += spaces(8) + '}\n'
        function += spaces(8) + 'System.out.print("]");\n'
    else:
        raise NotImplementedError()
    if top:
        function += spaces(8) + 'System.out.print("\\n");\n'
        function += spaces(4) + '}\n'
    else:
        function += spaces(4) + '}\n\n'
    if item_type is not None:
        function = print_output_for_java(item_type) + function
    return function


def convert_param_for_java(param_type: str, param_value):
    if param_type in java_atom_types:
        if param_type == 'String':
            return f'"{param_value}"'
        if param_type in ['bool', 'Boolean']:
            return str(param_value).lower()
        return str(param_value)
    if param_type.startswith('List'):
        param = "Arrays.asList("
        for i, item in enumerate(param_value):
            item_type = get_item_type_for_java(param_type)
            param += convert_param_for_java(item_type, item)
            if i != len(param_value) - 1:
                param += ", "
        param += ")"
        return param
    raise NotImplementedError()


def package_test_code_for_java(testcases, entrypoint, param_types: list[str], ret_type: str, param_names):
    test_code = f'class PrintTool {{\n{print_output_for_java(ret_type, True)}}}\n\n'
    test_code += 'public class Main {\n'
    test_code += spaces(4) + 'public static void main(String[] args) {\n'
    test_code += spaces(8) + 'Solution __s = new Solution();\n'
    for p_name, p_type in zip(param_names, param_types):
        test_code += spaces(8) + f'{p_type} {p_name};\n'
    for i, tc in enumerate(testcases):
        test_code += spaces(8) + 'try {\n'
        for param_value, param_name, param_type in zip(tc[0], param_names, param_types):
            test_code += spaces(12) + f'{param_name} = {convert_param_for_java(param_type, param_value)};\n'
        test_code += spaces(12) + f'PrintTool.printOutput(__s.{entrypoint}({", ".join(param_names)}), {i});\n'
        test_code += spaces(8) + '} catch (Exception ignored) { }\n'
    test_code += spaces(4) + '}\n'
    test_code += '}\n'
    return test_code


print_output_for_js = """const printOutput = (output, index) => {
    if (typeof output == "string") {
        output = "\\\"" + output + "\\\""
    }
    console.log("\\n[SOLUTION OUTPUT " + index + "]", output)
}

"""


def convert_param_for_js(param_value):
    param_type = type(param_value)
    if param_type in python_atom_types:
        if param_type == str:
            return f'"{param_value}"'
        if param_type == bool:
            return str(param_value).lower()
        return str(param_value)
    if param_type == list:
        param = "["
        for i, item in enumerate(param_value):
            param += convert_param_for_js(item)
            if i != len(param_value) - 1:
                param += ", "
        param += "]"
        return param
    raise NotImplementedError()


def package_test_code_for_js(testcases, entrypoint):
    test_entrypoint = f'test{entrypoint[0].upper()}{entrypoint[1:]}'
    test_code = print_output_for_js + f'const {test_entrypoint} = () => {{\n'
    for i, tc in enumerate(testcases):
        test_code += spaces(4) + 'try {\n'
        params = []
        for param_value in tc[0]:
            params.append(convert_param_for_js(param_value))
        test_code += spaces(8) + f'printOutput({entrypoint}({", ".join(params)}), {i});\n'
        test_code += spaces(4) + '} catch (err) { }\n'
    test_code += '}\n\n'
    test_code += f'{test_entrypoint}()\n'
    return test_code


print_output_for_python = """def print_output(output, index):
    if type(output) == str:
        output = f'"{output}"'
    print(f'\\n[SOLUTION OUTPUT {index}] {output}')


"""


def package_test_code_for_python(testcases, entrypoint):
    test_entrypoint = f'test_{entrypoint}'
    test_code = print_output_for_python + f'def {test_entrypoint}():\n'
    for i, tc in enumerate(testcases):
        test_code += spaces(4) + 'try:\n'
        test_code += spaces(8) + f'print_output({entrypoint}(*{str(tc[0])}), {i})\n'
        test_code += spaces(4) + 'except Exception as e:\n'
        test_code += spaces(8) + 'pass\n'
    test_code += f'\n\n{test_entrypoint}()\n'
    return test_code


def get_item_type_for_rust(ori_type):
    return ori_type[ori_type.find('<') + 1: -1].strip()


def convert_param_for_rust(param_type: str, param_value):
    if param_type in rust_atom_types:
        if param_type == 'String':
            return f'String::from("{param_value}")'
        if param_type == 'bool':
            return str(param_value).lower()
        return str(param_value)
    if param_type.startswith('Vec'):
        param = "vec!["
        for i, item in enumerate(param_value):
            item_type = get_item_type_for_rust(param_type)
            param += convert_param_for_rust(item_type, item)
            if i != len(param_value) - 1:
                param += ", "
        param += "]"
        return param
    raise NotImplementedError()


def package_test_code_for_rust(testcases, entrypoint, param_types: list[str], ret_type: str):
    test_code = '\n#[cfg(test)]\nmod tests {\n'
    test_code += spaces(4) + 'use super::*;\n\n'
    test_code += spaces(4) + '#[test]\n'
    test_code += spaces(4) + f'fn test_{entrypoint}() {{\n'
    for i, tc in enumerate(testcases):
        params = []
        for param_type, param_value in zip(param_types, tc[0]):
            params.append(convert_param_for_rust(param_type, param_value))
        test_code += spaces(8) + f'match {entrypoint}({", ".join(params)}) {{\n'
        test_code += spaces(12) + f'Ok(r) => println!("\\n[SOLUTION OUTPUT {{}}] {{:?}}", {i}, r),\n'
        test_code += spaces(12) + 'Err(e) => { }\n'
        test_code += spaces(8) + '}\n'
    test_code += spaces(4) + '}\n'
    test_code += '}\n'
    return test_code


def package_test_code(testcases, info):
    language = info["language"]
    extra_args = [info["entrypoint"], info["param_types"], info["ret_type"]]
    param_names = info["param_names"]
    if language == 'cpp':
        return package_test_code_for_cpp(testcases, *extra_args)
    elif language == 'go':
        return package_test_code_for_go(testcases, *extra_args, param_names)
    elif language == 'java':
        return package_test_code_for_java(testcases, *extra_args, param_names)
    elif language == 'javascript':
        return package_test_code_for_js(testcases, extra_args[0])
    elif language == 'python':
        return package_test_code_for_python(testcases, extra_args[0])
    # elif language == 'rust':
    #     return package_test_code_for_rust(testcases, *extra_args)
    else:
        raise ValueError(f'{language} is not supported')


if __name__ == '__main__':
    # print(print_output_for_cpp('vector<vector<string>>', True))
    # print(convert_param_for_cpp("vector<vector<string>>", [["1", "www"], ["f20]]"]]))
    print(package_test_code_for_rust(
        [([[[1, 2, 3, 4], [3]], "1"], [["best"]]), ([[[1, 3, 5, 7], [3, 5]], "hello"], [["no"]])], "MyFunc",
        ["Vec<Vec<i32>>", "String"], "Vec<String>"))
