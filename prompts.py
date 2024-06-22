import copy
from config import config
from parse import to_terminal_io

dataset = config["dataset"]


def get_example_problem():
    if dataset in ['humaneval', 'humaneval-x']:
        return '''# Example problem:
def median(l):
    """
    Given a list l, return median of elements in the list. 
    >>> median([3, 1, 2, 4, 5])
    3
    >>> median([-7, 4, 6, 100, 10, 20])
    15.0
    """
'''
    elif dataset == 'code_contests':
        return '''# Example problem:
You are given q queries in the following form:
Given three integers l_i, r_i and d_i, find minimum positive integer x_i such that it is divisible by d_i and it does not belong to the segment [l_i, r_i].
Can you answer all the queries?
Recall that a number x belongs to segment [l, r] if l \u2264 x \u2264 r.
Input
The first line contains one integer q (1 \u2264 q \u2264 500) \u2014 the number of queries.
Then q lines follow, each containing a query given in the format l_i r_i d_i (1 \u2264 l_i \u2264 r_i \u2264 10^9, 1 \u2264 d_i \u2264 10^9). l_i, r_i and d_i are integers.
Output
For each query print one integer: the answer to this query.
Example
Input
5
2 4 2
5 10 4
3 10 1
1 2 3
4 6 5
Output
6
4
1
3
10
'''
    else:
        raise NotImplementedError()


def get_output_name():
    if dataset in ['humaneval', 'humaneval-x']:
        return "output"
    elif dataset == 'code_contests':
        return "case_out"
    else:
        raise NotImplementedError()


def testcase_prompt(problem, example_testcase):
    if example_testcase is not None:
        if dataset == 'code_contests':
            example_testcase = (example_testcase[0][0], example_testcase[1][0])
        example_testcase_prompt = f'For this problem, an example IO tuple can be represented as: {example_testcase}'
    else:
        example_testcase_prompt = ''
    if dataset in ['humaneval', 'humaneval-x']:
        example_generated_testcase = """# Example test case:
test_cases = [
    # basic function test cases
    ([[-10,4,6,1000,10,20]],[8.0]),
    ([1,2,3,4,5],[3.0]),
    ([[10, 2, 38, 23, 38, 23, 21]],[23.0]),
    ([[4, 1, 2, 3]],[2.5]),
    # special situation test cases
    ([[1,1,1,1]],[1.0]),
    ([[1]],[1.0]),
    ([[-10, -20, -30, -40, -50]],[-30.0]),
    # boundary and stress test cases
    ([[i for i in range(1, 10001)]],[5000.5]),
    ([[1] * 5000 + [2] * 5000],[1.5]),
    # random test cases
    ([[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]],[4.0]),
    ([[15, 20, 35, 40, 50]],[35.0])
    
]
    
Each tuple in `test_cases` contains two parts: case_in and case_out, both of which are lists. Each element in the lists corresponds to a parameter/return value of the function. For example, the first example IO in the problem description can be represented as: ([[3, 1, 2, 4, 5]], [3])
"""
    elif dataset == 'code_contests':
        example_generated_testcase = """# Example Test case:
test_cases = [
    # basic function test cases
    ([[1], [78, 79, 79]], [[158]]),
    ([[1], [6, 6, 6]], [[12]]),
    ([[1], [79, 80, 100]], [[100]]),
    # special situation test cases
    ([[1], [1, 1, 123456789]], [[123456789]]),
    ([[1], [80, 100, 1]], [[1]]),
    ([[5], [1000000000, 1000000000, 1], [1000000000, 1000000000, 1], [1000000000, 1000000000, 1], [1000000000, 1000000000, 1], [1000000000, 1000000000, 1]], [[1], [1], [1], [1], [1]]),
    # boundary and stress test cases
    ([[20], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2], [1, 1000000000, 2]], [[1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002], [1000000002]]),
    ([[25], [1, 1000000000, 1], [1, 1000000000, 1000000000], [2, 1000000000, 1], [1, 999999999, 1000000000], [5, 6, 5], [1, 1000000000, 1], [1, 1000000000, 1000000000], [2, 1000000000, 1], [1, 999999999, 1000000000], [5, 6, 5], [1, 1000000000, 1], [1, 1000000000, 1000000000], [2, 1000000000, 1], [1, 999999999, 1000000000], [5, 6, 5], [1, 1000000000, 1], [1, 1000000000, 1000000000], [2, 1000000000, 1], [1, 999999999, 1000000000], [5, 6, 5], [1, 1000000000, 1], [1, 1000000000, 1000000000], [2, 1000000000, 1], [1, 999999999, 1000000000], [5, 6, 5]], [[1000000001], [2000000000], [1], [1000000000], [10], [1000000001], [2000000000], [1], [1000000000], [10], [1000000001], [2000000000], [1], [1000000000], [10], [1000000001], [2000000000], [1], [1000000000], [10], [1000000001], [2000000000], [1], [1000000000], [10]]),
    # random test cases
    ([[5], [80, 100, 10], [5, 10, 4], [3, 10, 1], [1, 2, 3], [4, 6, 5]], [[10], [4], [1], [3], [10]]),
    ([[1], [1, 1000000000, 1017]], [[1000000845]])
]

Each tuple in `test_cases` contains two parts: case_in and case_out, both of which are 2D lists. Each element list in the 2D lists corresponds to an input/output line, and each element in the element lists corresponds to a string/number separated by a space in an input/output line. For example, the example IO in the problem description can be represented as: ([[5], [2, 4, 2], [10, 4], [10, 1], [2, 3], [6, 5]], [[6], [4], [1], [3], [10]])
"""
    else:
        raise NotImplementedError()

    return f"""Given a question, you need to write several CERTAINLY CORRECT testcases for checking the correctness of the code implementation about the functionality of the given question. Please do not duplicate the Example IO given in the question. You are required to generate 20 sets of absolutely correct test cases that comprehensively validate the implementation's functionality under various conditions, including 4 types for 5 pieces each: functional and logical correctness test cases ,special situation test cases, boundary and stress test cases and completely random data test cases. The elements in each test case can only consist of two parts named 'caseIn' and 'caseOut'. Please also annotate each test case with detailed comments. Again, all you need to do and you can do is to return me only an array called test_cases.
Here is an example: 
{get_example_problem()}
{example_generated_testcase}
Now, please provide the test cases for the following problem. Please do not duplicate the Example I0 given in the problem description.

# Problem:
{problem.strip()}

{example_testcase_prompt}

# Test case:
"""


def natural_language_specification_prompt(problem, refined_description=""):
    if len(refined_description) > 0:
        problem = f"""{problem.strip()}

The following is a refined description of the problem:

{refined_description.strip()}
"""
    if dataset in ['humaneval', 'humaneval-x']:
        example_nl_specification = """# Example constraints:
1. Input 'l' should be a list.
2. Each element in input 'l' should be of type int or float.
3. 'Output' should be of type int or float.
4. Counts of elements greater than or equal to 'output' and less than or equal to 'output' should be equal in list 'l'.
"""
    elif dataset == 'code_contests':
        # TODO
        example_nl_specification = """# Example constraints:
1. Input should be a string.
2. Input should contains at least a line stands for the number of queries.
3. The first line should only contains one integer q which stands for the number of queries.
4. q should be within the given data range.
5. The total number of queries should be equal to q.
6. The length of each query should be 3.
7. Each query should only contains integer elements.
8. l of each query should be less than or equal to r.
9. l of each query should be within the given data range.
10. r of each query should be within the given data range.
11. d of each query should be within the given data range.
12. Output should be a string.
13. The total number of output lines should be q.
14. The result x of each query should be a single integer.
15. Result x of each query should be a positive integer.
16. Result x of each query should be a multiple of d.
17. Result x of each query should not be within the range [l, r].
18. Result x of each query should be the minimum positive integer that meets the requirements.
"""
    else:
        raise NotImplementedError()
    return f"""Given a problem, you need to provide some constraints that **the problem input, output, and their interrelationships** should satisfy. Please list various constraints as comprehensively as possible, including those related to data type and functionality.
Here is an example:
{get_example_problem()}
{example_nl_specification}
Now, please provide the specifications for the following problem.

# Problem:
{problem.strip()}

# Constraints:
"""


def specification_prompt(problem, param_names, refined_description="", example_testcase=None, has_nl_specification=False):
    if example_testcase is not None and dataset == 'code_contests':
        example_testcase_prompt = (
            f'# An example case_in: "{to_terminal_io(example_testcase[0][0], True)}"',
            f'# An example case_in: "{to_terminal_io(example_testcase[0][0], True)}" and case_out: "{to_terminal_io(example_testcase[1][0], True)}"'
        )
    else:
        example_testcase_prompt = ('', '')

    # No need to provide testcase format for humaneval
    if len(refined_description) > 0:
        problem = f"""{problem.strip()}

The following is a refined description of the problem:

{refined_description.strip()}
"""


    if dataset in ['humaneval', 'humaneval-x']:

        example_specification = """# Example specification:

def preconditions(l):
    assert isinstance(l, list), "Input 'l' is not a list."
    assert all([isinstance(i, (int, float)) for i in l]), "There are elements in input 'l' that are not of type int or float."
def postconditions(l, output):
    assert isinstance(output, (int, float)), "'Output' is not of type int or float."
    num_greater = sum([1 for i in l if i >= output])
    num_less = sum([1 for i in l if i <= output])
    assert num_greater == num_less, "Counts of elements greater than or equal to 'output' and less than or equal to 'output' are not equal."
"""
    elif dataset == 'code_contests':
        example_specification = """# Example specification:
def preconditions(case_in):
    assert isinstance(case_in, str), "Input is not a string."
    lines = case_in.split('\\n')
    assert len(lines) >= 1, "Input should contains at least a line stands for the number of queries."
    assert lines[0].isdigit(), "The first line should only contains one integer q which stands for the number of queries."
    q = int(lines[0])
    assert 1 <= q <= 500, "q is not within the given data range."
    queries = lines[1:]
    assert len(queries) == q, "The total number of queries is not equal to q."
    for idx, query in enumerate(queries):
        query_elems = query.split(' ')
        assert len(query_elems) == 3, f"The length of the {idx + 1}th query is not 3."
        for element in query_elems:
            assert element.isdigit(), f"The {idx + 1}th query contains non-integer elements: {element}."
        l, r, d = tuple(map(int, query_elems))
        assert l <= r, f"l of the {idx + 1}th query is not less than or equal to r."
        assert l >= 1, f"l of the {idx + 1}th query is not within the given data range."
        assert r <= 1e9, f"r of the {idx + 1}th query is not within the given data range."
        assert 1e9 >= d >= 1, f"d of the {idx + 1}th query is not within the given data range."


def postconditions(case_in, case_out):
    assert isinstance(case_out, str), "Output is not a string."
    case_in_lines = case_in.split('\\n')
    q = int(case_in_lines[0])
    case_out_lines = case_out.split('\\n')
    assert len(case_out_lines) == q, "The total number of output lines is not q."
    for idx, query_result in enumerate(case_out_lines):
        assert query_result.isdigit(), f"The result x of the {idx + 1}th query is not a single integer."
        x = int(query_result)
        l, r, d = tuple(map(int, case_in_lines[idx + 1].split(' ')))
        assert x > 0, f"Result x of the {idx + 1}th query is not a positive integer."
        assert x % d == 0, f"Result x of the {idx + 1}th query is not a multiple of d."
        assert not (l <= x <= r), f"Result x of the {idx + 1}th query is within the range [l, r]."
        if x != d:
            assert l <= d <= r and l <= (x - d) <= r, f"Result x of the {idx + 1}th query is not the minimum positive integer that meets the requirements."
"""
    else:
        raise NotImplementedError()


    if not has_nl_specification:
        start_prompt = f"""I want you to act as a python programmer. Given a problem, you need to generate two specification functions: `preconditions`, which checks whether the input satisfies certain constraints about the requirement, and `postconditions` checks the functional relationships between the test inputs and outputs to ensure compliance with the requirements. Please thoroughly assess the correctness of the test cases (Inputs and Outputs) from various perspectives, including but not limited to formal correctness, functional correctness, logical correctness, etc. In the event that an error is encountered during the evaluation, please print the corresponding test case along with a specific error message. Please also generate as many detailed comments as possible.
Here is an example:
{get_example_problem()}
{example_specification}
Now, please provide the specifications for the following problem. Your output should only include two functions: "preconditions" and "postconditions". You do not need to generate test cases. Only provide the code.

# Problem:
{problem.strip()}
"""
    else:
        start_prompt = f"""Now please translate the constraints you provided earlier into Python specification, and print detailed error information when encountering assertion errors.
Here is an example:
{example_specification.strip()}
"""

    return f"""{start_prompt}
# Specification:
{example_testcase_prompt[0]}
def preconditions({', '.join(param_names)}):
    #----------------you should ALWAYS begin with----------
    assert isinstance(case_in, str), "Input is not a string."
    case_in_lines = case_in.split('\\n')
    #----------------end-----------------------------------
    # TODO: Continue to fill in preconditions

{example_testcase_prompt[1]}
def postconditions({', '.join(param_names)}, {get_output_name()}):
    #----------------you should ALWAYS begin with-------------
    assert isinstance(case_out, str), "Output is not a string."
    case_in_lines = case_in.split('\\n')
    case_out_lines = case_out.split('\\n')
    #----------------end-------------------------------------
    # TODO: Continue to fill in postconditions
"""


def specification_modify_prompt_for_proper_testcase(param_names, testcase_info):
    testcase_info = copy.copy(testcase_info)
    prompt = "I tested your specification using some correct testcases to ensure its completeness. If your specification is complete, there should be no errors reported. Please modify your specification according to the following messages:"
    for case_in, case_out, msg in testcase_info[:1]:
        msg_item = "\nWhen "
        for params_name, param_value in zip(param_names, case_in):
            if isinstance(param_value, str):
                param_value = f'"{params_name}"'
            msg_item += f"{params_name} = {param_value}, "
        if isinstance(case_out[0], str):
            case_out[0] = f'"{case_out[0]}"'
        msg_item += f"{get_output_name()} = {case_out[0]}, the specification erroneously reports: {msg}."
        prompt += msg_item
    prompt += "\nPlease provide the revised specification directly."
    return prompt


def constraints_modify_prompt_for_proper_testcase(param_names, testcase_info):
    testcase_info = copy.copy(testcase_info)
    prompt = "I checked the constraints you provided using some correct testcases and found some errors, such as:"
    for case_in, case_out, _ in testcase_info[:1]:
        msg_item = "\nWhen "
        for params_name, param_value in zip(param_names, case_in):
            if isinstance(param_value, str):
                param_value = f'"{params_name}"'
            msg_item += f"{params_name} = {param_value}, "
        if isinstance(case_out[0], str):
            case_out[0] = f'"{case_out[0]}"'
        msg_item += f"{get_output_name()} = {case_out[0]}, this correct testcase does not meet the constraints you provided."
        prompt += msg_item
    prompt += "\nPlease modify the constraints to ensure that these correct testcases comply with the constraints. Provide all constraints obtained after modification."
    return prompt


def specification_modify_prompt_for_improper_testcase(param_names, testcase_info):
    testcase_info = copy.copy(testcase_info)
    prompt = "I tested your specification using some possibly wrong cases to ensure its soundness. If your specification is sound, there should be some errors reported. Please modify your specification according to the following messages:"
    for case_in, case_out in testcase_info[:1]:
        msg_item = "\nWhen "
        for params_name, param_value in zip(param_names, case_in):
            if isinstance(param_value, str):
                param_value = f'"{params_name}"'
            msg_item += f"{params_name} = {param_value}, "
        if isinstance(case_out[0], str):
            case_out[0] = f'"{case_out[0]}"'
        msg_item += f"{get_output_name()} = {case_out[0]}, this case possibly erroneously passed the specification."
        prompt += msg_item
    prompt += "\nPlease provide the revised specification directly."
    return prompt


def constraints_modify_prompt_for_improper_testcase(param_names, testcase_info):
    testcase_info = copy.copy(testcase_info)
    prompt = "I checked the constraints you provided using some **possibly incorrect** testcases and found that some of them fully comply with the constraints, such as:"
    for case_in, case_out in testcase_info[:1]:
        msg_item = "\nWhen "
        for params_name, param_value in zip(param_names, case_in):
            if isinstance(param_value, str):
                param_value = f'"{params_name}"'
            msg_item += f"{params_name} = {param_value}, "
        if isinstance(case_out[0], str):
            case_out[0] = f'"{case_out[0]}"'
        msg_item += f"{get_output_name()} = {case_out[0]}, this possibly incorrect testcase fully comply with the constraints."
        prompt += msg_item
    prompt += "\nPlease modify or add constraints so that these possibly incorrect test cases do not comply with the constraints. Provide all constraints obtained after modification."
    return prompt


def requirement_refine_prompt(problem):
    # No need to describe format for humaneval
    if dataset in ['humaneval', 'humaneval-x']:
        example_refined_requirement = """# Refined requirements:
def median(l):
## Problem description:
This problem requires writing a function to determine the median of a given list of numbers. The median is the middle number in a sorted, ascending or descending, list of numbers and can be more descriptive of that data set than the average. If the list has an odd number of elements, the median is the middle element. If the list has an even number of elements, the median is the average of the two middle elements.

## Data restrictions:
The list l can contain any number of integers or floats.
The list will contain at least one element.
The elements of the list can be negative or positive.

## Explanation of examples:
For median([3, 1, 2, 4, 5]), the sorted list is [1, 2, 3, 4, 5]. The middle element is 3, so the output should be 3.
For median([-7, 4, 6, 100, 10, 20]), the sorted list is [-7, 4, 6, 10, 20, 100]. The two middle elements are 6 and 10, and their average is (6 + 10) / 2 = 8.0, so the output should be 8.0.
"""
    elif dataset == 'code_contests':
        example_refined_requirement ="""# Refined requirements:
## Problem description
You are given \( q \) queries, and each query consists of three integers: \( l_i \), \( r_i \), and \( d_i \). For each query, you need to find the smallest positive integer \( x_i \) such that \( x_i \) is divisible by \( d_i \) and does not lie within the segment \([l_i, r_i]\).
Recall that a number x belongs to segment [l, r] if l \u2264 x \u2264 r.

So you need to meet these significant requirements:
1. x_i is not in the range \([l_i, r_i]\);
2. x_i is divisible by d_i
3. x_i is the smallest of all the numbers that satisfy this condition

## Data restrictions:
1 \u2264 q \u2264 500
1 \u2264 l_i \u2264 r_i \u2264 10^9
 1 \u2264 d_i \u2264 10^9
 l_i, r_i and d_i are integers
 
## Explanation of examples:
 For the first query, the smallest \( x_i \) is 6 because 6 is divisible by 2 and is not in the range [2, 4].
- For the second query, the smallest \( x_i \) is 4 because 4 is divisible by 4 and is not in the range [5, 10].
- For the third query, the smallest \( x_i \) is 1 because 1 is divisible by 1 and is not in the range [3, 10].
- For the fourth query, the smallest \( x_i \) is 3 because 3 is divisible by 3 and is not in the range [1, 2].
- For the fifth query, the smallest \( x_i \) is 10 because 10 is divisible by 5 and is not in the range [4, 6].
"""
    else:
        raise NotImplementedError()
    return f"""Given a problem description, you need to itemize its requirements to make it easier to understand. 
Here is an example:
{get_example_problem()}
{example_refined_requirement}
Now please refine the requirements as required without changing the meaning of the problem to make it clearer and more understandable. Note that you can't add or delete any conditions and contents in the problem description.

# Problem:
{problem}

# Refined requirements:
"""


def code_prompt_for_iteration(param_names, info):
    info = copy.copy(info)
    prompt = "I evaluated the code you provided using testcases and found that some of them failed. Please modify the original code based on the following detailed information:"
    for case_in, case_out, code_out, msg in info[:1]:
        if dataset in ['humaneval', 'humaneval-x']:
            msg_item = "\nWhen "
            for params_name, param_value in zip(param_names, case_in):
                if isinstance(param_value, str):
                    param_value = f'"{params_name}"'
                msg_item += f"{params_name} = {param_value}, "
            if isinstance(case_out[0], str):
                case_out[0] = f'"{case_out[0]}"'
            if isinstance(code_out[0], str):
                code_out[0] = f'"{code_out[0]}"'
            if code_out[0] is None:
                msg_item += "the code encountered errors during compilation or runtime, resulting in the inability to obtain any return values."
            else:
                msg_item += f"the expected return value is: {case_out[0]}, but the return value obtained by running the code is: {code_out[0]}, and the error in this output is: {msg}"
        elif dataset == 'code_contests':
            msg_item = f"\nWhen the input is\n{case_in[0]}\n"
            if code_out[0] is None:
                msg_item += "The code encountered errors during compilation or runtime, resulting in the inability to obtain any return values."
            else:
                msg_item += f"The expected output is\n{case_out[0]}\nBut the output obtained by running the code is\n{code_out[0]}\nAnd the error in this output is: {msg}"
        else:
            raise NotImplementedError()

        prompt += msg_item
    prompt += "\nPlease provide the revised solution directly."
    return prompt
