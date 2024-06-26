import copy
from config import config
from parse import to_terminal_io

dataset = config["dataset"]


def get_another_example_problem_for_code_contests():
    if dataset in ['humaneval', 'humaneval-x']:
        return ''''''
    else:
        return '''Here is another example which help you generate specification in complex situation:
# Example2 problem:
Polycarp starts his own business. Tomorrow will be the first working day of his car repair shop. For now the car repair shop is very small and only one car can be repaired at a given time.\n\nPolycarp is good at marketing, so he has already collected n requests from clients. The requests are numbered from 1 to n in order they came.\n\nThe i-th request is characterized by two values: si \u2014 the day when a client wants to start the repair of his car, di \u2014 duration (in days) to repair the car. The days are enumerated from 1, the first day is tomorrow, the second day is the day after tomorrow and so on.\n\nPolycarp is making schedule by processing requests in the order from the first to the n-th request. He schedules the i-th request as follows:\n\n  * If the car repair shop is idle for di days starting from si (si, si + 1, ..., si + di - 1), then these days are used to repair a car of the i-th client. \n  * Otherwise, Polycarp finds the first day x (from 1 and further) that there are di subsequent days when no repair is scheduled starting from x. In other words he chooses the smallest positive x that all days x, x + 1, ..., x + di - 1 are not scheduled for repair of any car. So, the car of the i-th client will be repaired in the range [x, x + di - 1]. It is possible that the day x when repair is scheduled to start will be less than si. \n\n\n\nGiven n requests, you are asked to help Polycarp schedule all of them according to the rules above.\n\nInput\n\nThe first line contains integer n (1 \u2264 n \u2264 200) \u2014 the number of requests from clients.\n\nThe following n lines contain requests, one request per line. The i-th request is given as the pair of integers si, di (1 \u2264 si \u2264 109, 1 \u2264 di \u2264 5\u00b7106), where si is the preferred time to start repairing the i-th car, di is the number of days to repair the i-th car.\n\nThe requests should be processed in the order they are given in the input.\n\nOutput\n\nPrint n lines. The i-th line should contain two integers \u2014 the start day to repair the i-th car and the finish day to repair the i-th car.\n\nExamples\n\nInput\n\n3\n9 2\n7 3\n2 4\n\n\nOutput\n\n9 10\n1 3\n4 7\n\n\nInput\n\n4\n1000000000 1000000\n1000000000 1000000\n100000000 1000000\n1000000000 1000000\n\n\nOutput\n\n1000000000 1000999999\n1 1000000\n100000000 100999999\n1000001 2000000

'''


def get_another_example_nl_specification_for_code_contests():
    if dataset in ['humaneval', 'humaneval-x']:
        return ''''''
    else:
        return '''# Example2 constraints:
1. Input should be a string.
2. The first line of input should only contain one element.
3. n in input should be integer.
4. n in input is not within the given range [1,200].
5. The input lines should be n+1.
6. Each line of input request should only contain two elements.
7. The two elements in each input line should be integer.
8. The s of each input request should be within the given range [1,1e9].
9. The d of each input request should be within the given range [1,5e6].
10. Output should be a string.
11. The number of output lines should be n.
12. The output start day and finish dat to repair each car should be integer.
13. Each output request's start day should be earlier than finish day.
14. In output,if there is a car which expected start repair time is not equal to the actual start repair time, then there must be a car which actual start repair time is 1.
15. In output,a car's actual finish repair time and the other car's actual start repair time overlap.
'''


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
        return '''# Example problem :
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
        example_nl_specification = """# Example constraints:
1. Input should be a string.
2. Input should contains at least a line stands for the number of queries.
3. The first line of input should only contains one element q.
4. The only element q in the first line should be integer.
5. q should be within the given data range.
6. The total number of queries of input should be equal to q.
7. The the {idx + 1}th query does not contain 3 space-separated elements.
8. Each query of input should only contains integer elements.
9. l of each query of input should be less than or equal to r.
10. l of each query of input should be within the given data range.
11. r of each query of input should be within the given data range.
12. d of each query of input should be within the given data range.
13. Output should be a string.
14. The total number of output lines should be q.
15. The result x of each query of output should be a single integer.
16. Result x of each output query should be a positive integer.
17. Result x of each output query should be a multiple of d.
18. Result x of each output query should not be within the range [l, r].
19. Result x of each output query should be the minimum positive integer that meets the requirements.
"""
    else:
        raise NotImplementedError()
    return f"""Given a problem, you need to provide some constraints that the problem input, output, and their interrelationships should satisfy. Please list various constraints as comprehensively as possible, including those related to data type and functionality.
Here is an example:
{get_example_problem()}
{example_nl_specification}
{get_another_example_problem_for_code_contests()}
{get_another_example_nl_specification_for_code_contests()}
Now, please provide the constraints for the following problem.

# Problem:
{problem.strip()}

# Constraints:
"""


def specification_prompt(problem, param_names, refined_description="", example_testcase=None,
                         has_nl_specification=False):
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
    assert len(lines[0]) == 1, "The first line of input should only contains one element q."
    assert lines[0][0].isdigit(), "The only element q in the first line should be integer."
    q = int(lines[0])
    assert 1 <= q <= 500, "q is not within the given data range."
    queries = lines[1:]
    assert len(queries) == q, "The total number of queries is not equal to q."
    for idx, query in enumerate(queries):
        query_elems = query.split(' ')
        assert len(query_elems) == 3, f"The the {idx + 1}th query does not contain 3 space-separated elements."
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
        start_prompt = f"""I want you to act as a python programmer. Given a problem, you need to generate two specification functions: `preconditions`, which checks whether the input satisfies certain constraints about the requirement, and `postconditions` checks the functional relationships between the test inputs and outputs to ensure compliance with the requirements. Please thoroughly assess the correctness of the test cases (Inputs and Outputs) from various perspectives, preconditions should check the correctness of the input form, including whether the data type and number are consistent with the requirements of the problem, etc. postconditions should check the data type and number of the output, and check whether the output meets all the conditions required(more focused). Note that this kind of check by specification here is not the realization of the problem requirements, but the use of relatively simple logic to check whether the output meets the expectation and whether it is inconsistent with the input or the problem requirements. In the event that an error is encountered during the evaluation, please print the corresponding test case along with a specific error message. Please also generate as many detailed comments as possible.
Here is an example:
{get_example_problem()}
{example_specification}

Now, please provide the specifications for the following problem.Try to give a CORRECT and RESTRICTIVE specification. Please ensure that the syntax of the specification is CORRECT and can be COMPILED and RUN.Your output should only include two functions: "preconditions" and "postconditions". You do not need to generate test cases. Only provide the code.
Unresolved reference variables and unresolved property references to a class CANNOT appear in the specification! For example,do not use the 'isdigit()' function on variables of type 'int'.
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
    
You only need to return the Specification.Please ensure that the syntax of the specification is CORRECT and can be COMPILED and RUN.Unresolved reference variables and unresolved property references to a class CANNOT appear in the specification! For example,do not use the 'isdigit()' function on variables of type 'int'.
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
    prompt += "\nPlease provide the revised specification directly.Please do not bend the rules to meet pass rate requirements."
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
    prompt += "\nPlease provide the revised specification directly.Please do not bend the rules to meet fail rate requirements."
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
    prompt += "\nPlease modify or add constraints so that these possibly incorrect test cases do not comply with the constraints. Provide ALL constraints obtained after modification!"
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
        example_refined_requirement = """# Refined requirements:
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
