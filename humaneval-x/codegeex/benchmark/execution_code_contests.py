import contextlib
import faulthandler
import io
import multiprocessing
import os
import platform
import signal
import random
import subprocess
import tempfile
import gzip
import json
from typing import *


def dicts_to_jsonl(data_list: list, filename: str, compress: bool = True) -> None:
    """
    Method saves list of dicts into jsonl file.
    :param data: (list) list of dicts to be stored,
    :param filename: (str) path to the output file. If suffix .jsonl is not given then methods appends
        .jsonl suffix into the file.
    :param compress: (bool) should file be compressed into a gzip archive?
    """
    sjsonl = '.jsonl'
    sgz = '.gz'
    # Check filename
    if not filename.endswith(sjsonl):
        filename = filename + sjsonl
    # Save data

    if compress:
        filename = filename + sgz
        with gzip.open(filename, 'w') as compressed:
            for ddict in data_list:
                jout = json.dumps(ddict) + '\n'
                jout = jout.encode('utf-8')
                compressed.write(jout)
    else:
        with open(filename, 'w') as out:
            for ddict in data_list:
                jout = json.dumps(ddict) + '\n'
                out.write(jout)


def check_correctness(
        task_id: str,
        sample: dict,
        language_type: str,
        timeout: float = 3.0,
        tmp_dir: str = None,
        completion_id: Optional[int] = None,
) -> Dict:
    """
    Evaluates the functional correctness of a completion by running the test
    suite provided in the problem.
    """
    timeout = 3.0 * len(sample["testcases"])
    print(f'timeout = {timeout}_{"/".join(task_id.split("/")[1:])}/{completion_id}')

    def unsafe_execute(tmp_dir):
        random_id = random.uniform(1, 1000)
        code = sample["test_code"]
        testcases = sample["testcases"]
        import os
        import shutil

        if "tmp" not in tmp_dir:
            tmp_dir = os.path.join(tmp_dir, "tmp")
        tmp_dir = os.path.join(tmp_dir, f"{task_id.replace('/', '-')}-{random_id}")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        os.chdir(tmp_dir)
        if "python" in language_type.lower():
            # Disable functionalities that can make destructive changes to the test.
            open('test.py', 'w').write(code)
            try:
                with time_limit(timeout):
                    # WARNING
                    # This program exists to execute untrusted model-generated code. Although
                    # it is highly unlikely that model-generated code will do something overtly
                    # malicious in response to this test suite, model-generated code may act
                    # destructively due to a lack of model capability or alignment.
                    # Users are strongly encouraged to sandbox this evaluation suite so that it
                    # does not perform destructive actions on their host or network.
                    # Once you have read this disclaimer and taken appropriate precautions,
                    # uncomment the following line and proceed at your own risk:
                    failed = False
                    for i, tc in enumerate(testcases):
                        tc_input, tc_output = tc
                        process = subprocess.Popen(['python', 'test.py'], stdin=subprocess.PIPE,
                                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        out, err = process.communicate(input=tc_input)
                        if len(err) == 0:
                            print(f'\n<TESTCASE OUTPUT {i}>\n{out.strip()}\n</TESTCASE OUTPUT {i}>\n')
                        elif not failed:
                            result.append(f"failed: {err}")
                            failed = True
                        if len(err) > 0:
                            print(f'\n<TESTCASE ERROR {i}>\n{err.strip()}\n</TESTCASE ERROR {i}>\n')
                        if not failed and out.strip() != tc_output.strip():
                            result.append("failed: wrong answer")
                            failed = True
                    if not failed:
                        result.append("passed")

            except TimeoutException:
                print("time out")
                if not failed:
                    result.append("timed out")

            shutil.rmtree(tmp_dir)

        elif "go" in language_type.lower():
            assert tmp_dir is not None, "Go should be evaluated in a dir where necessary module files installed."

            import os
            import shutil

            if "tmp" not in tmp_dir:
                tmp_dir = os.path.join(tmp_dir, "tmp")
            tmp_dir = os.path.join(tmp_dir, f"{task_id.replace('/', '-')}-{random_id}")
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)

            os.chdir(tmp_dir)
            open(f"main.go", 'w').write(sample["test_code"])
            try:
                exec_result = None
                with time_limit(timeout):
                    # WARNING
                    # This program exists to execute untrusted model-generated code. Although
                    # it is highly unlikely that model-generated code will do something overtly
                    # malicious in response to this test suite, model-generated code may act
                    # destructively due to a lack of model capability or alignment.
                    # Users are strongly encouraged to sandbox this evaluation suite so that it
                    # does not perform destructive actions on their host or network.
                    # Once you have read this disclaimer and taken appropriate precautions,
                    # uncomment the following line and proceed at your own risk:
                    exec_result = subprocess.run(["go", "run", "main.go"], timeout=timeout, capture_output=True)

                if exec_result.returncode == 0:
                    result.append("passed")
                else:
                    if exec_result.stderr:
                        try:
                            err = exec_result.stderr.decode()
                        except:
                            err = exec_result.stderr
                    else:
                        try:
                            err = exec_result.stdout.decode()
                        except:
                            err = exec_result.stdout
                    result.append(f"failed: {err}")
                try:
                    print(exec_result.stdout.decode())
                except:
                    print("decode error")

            except TimeoutException:
                print("time out")
                result.append("timed out")

            shutil.rmtree(tmp_dir)
        elif "js" in language_type.lower():
            import os
            import shutil

            if "tmp" not in tmp_dir:
                tmp_dir = os.path.join(tmp_dir, "tmp")
            tmp_dir = os.path.join(tmp_dir, f"{task_id.replace('/', '-')}-{random_id}")
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)

            os.chdir(tmp_dir)
            open(f"test.js", 'w').write(sample["test_code"])
            try:
                with time_limit(timeout):
                    # WARNING
                    # This program exists to execute untrusted model-generated code. Although
                    # it is highly unlikely that model-generated code will do something overtly
                    # malicious in response to this test suite, model-generated code may act
                    # destructively due to a lack of model capability or alignment.
                    # Users are strongly encouraged to sandbox this evaluation suite so that it
                    # does not perform destructive actions on their host or network.
                    # Once you have read this disclaimer and taken appropriate precautions,
                    # uncomment the following line and proceed at your own risk:
                    exec_result = subprocess.run(["node", "test.js"], timeout=timeout, capture_output=True)

                if exec_result.stderr.decode():
                    err = exec_result.stderr.decode()
                    result.append(f"failed: {err}")
                elif exec_result.stdout.decode():
                    err = exec_result.stdout.decode()
                    result.append(f"failed: {err}")
                else:
                    result.append("passed")
                try:
                    print(exec_result.stdout.decode())
                except:
                    print("decode error")

            except TimeoutException:
                print("time out")
                result.append("timed out")

            shutil.rmtree(tmp_dir)
        elif "cpp" in language_type.lower():

            open(f"test.cpp", 'w').write(code)
            compilation_result = subprocess.run(["/usr/bin/g++", "-std=c++11", "test.cpp"], timeout=timeout,
                                                capture_output=True)
            if compilation_result.returncode != 0:
                if compilation_result.stderr:
                    err = compilation_result.stderr.decode()
                else:
                    err = compilation_result.stdout.decode()
                result.append(f"failed: compilation error: {err}")
                print("failed: compilation error")
            else:
                try:
                    with time_limit(timeout):
                        # WARNING
                        # This program exists to execute untrusted model-generated code. Although
                        # it is highly unlikely that model-generated code will do something overtly
                        # malicious in response to this test suite, model-generated code may act
                        # destructively due to a lack of model capability or alignment.
                        # Users are strongly encouraged to sandbox this evaluation suite so that it
                        # does not perform destructive actions on their host or network.
                        # Once you have read this disclaimer and taken appropriate precautions,
                        # uncomment the following line and proceed at your own risk:
                        failed = False
                        for i, tc in enumerate(testcases):
                            tc_input, tc_output = tc
                            process = subprocess.Popen(['./a.out'], stdin=subprocess.PIPE,
                                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            out, err = process.communicate(input=tc_input)
                            if len(err) == 0:
                                print(f'\n<TESTCASE OUTPUT {i}>\n{out.strip()}\n</TESTCASE OUTPUT {i}>\n')
                            elif not failed:
                                result.append(f"failed: {err}")
                                failed = True
                            if len(err) > 0:
                                print(f'\n<TESTCASE ERROR {i}>\n{err.strip()}\n</TESTCASE ERROR {i}>\n')
                            if not failed and out.strip() != tc_output.strip():
                                result.append("failed: wrong answer")
                                failed = True
                        if not failed:
                            result.append("passed")
                except TimeoutException:
                    print("time out")
                    if not failed:
                        result.append("timed out")

            shutil.rmtree(tmp_dir)
        elif "rust" in language_type.lower():
            import os

            WD: str = os.path.dirname(os.path.abspath(__file__))
            RUST_DIR: str = os.path.join(WD, "rust")
            RUST_SRC: str = os.path.join(RUST_DIR, "src")
            RUST_BIN: str = os.path.join(RUST_SRC, "bin")
            RUST_TMP_DIR: str = os.path.join(RUST_DIR, "tmp")
            RUST_LOGS: str = os.path.join(RUST_TMP_DIR, "logs")
            RUST_EXT: str = ".rs"

            # Create mandatory tmp directories
            os.makedirs(RUST_TMP_DIR, exist_ok=True)
            os.makedirs(RUST_LOGS, exist_ok=True)
            os.makedirs(RUST_SRC, exist_ok=True)
            os.makedirs(RUST_BIN, exist_ok=True)

            with tempfile.NamedTemporaryFile(dir=RUST_BIN, delete=False) as f:
                # temporal file name
                file_prefix = sample["task_id"].lower().replace("/", "_")
                file_name: str = file_prefix + RUST_EXT

                os.rename(f.name, os.path.join(RUST_BIN, file_name))

                # Sample to pure Rust function
                rust_code: str = sample["test_code"]

                # dump the rust source code in the target temporal file
                f.write(rust_code.encode('utf-8'))

            # Proceed towards Rust binaries compilation. Therefore move to Rust module root dir.
            os.chdir(RUST_DIR)

            # Two possible outcomes
            # Pass OR Fail compilation
            log_filename: str = file_prefix + ".jsonl"
            log_path: str = os.path.join(RUST_LOGS, log_filename)
            cargo_check: str = "cargo check --bin " + file_prefix + " --message-format json >> " + log_path
            # Compilation build status
            returned_val_compilation: int

            # Overwrite file content
            if os.path.exists(log_path):
                if (file_size := os.path.getsize(log_path)) >= 0:
                    os.remove(log_path)
                    returned_val_compilation = os.system(cargo_check)

            else:
                returned_val_compilation = os.system(cargo_check)

            # 0 means success   
            if returned_val_compilation == 0:

                # Execution pipeline
                cargo_test: str = "cargo test --bin " + file_prefix  # + " --message-format json >> " + log_path
                returned_val_execution = os.system(cargo_test)

                if returned_val_execution == 0:
                    result.append("passed")
                else:
                    result.append(f"failed: execution error")

            else:
                print("failed: compilation error")
                result.append(f"failed: compilation error")


        elif "java" in language_type.lower():
            assert tmp_dir is not None, "Java should be evaluated in a temporary dir."

            open(os.path.join(tmp_dir, "Main.java"), 'w').write(code)
            res = "failed: unknown error"
            compile_returncode = -1
            for _ in range(5):
                try:
                    compilation_result = subprocess.run(['javac', os.path.join(tmp_dir, "Main.java")], timeout=5,
                                                        capture_output=True)
                    compile_returncode = compilation_result.returncode
                    break
                except subprocess.TimeoutExpired as e:
                    continue
            if compile_returncode != 0:
                res = "failed: compilation error"
            else:
                try:
                    with time_limit(timeout):
                        # WARNING
                        # This program exists to execute untrusted model-generated code. Although
                        # it is highly unlikely that model-generated code will do something overtly
                        # malicious in response to this test suite, model-generated code may act
                        # destructively due to a lack of model capability or alignment.
                        # Users are strongly encouraged to sandbox this evaluation suite so that it
                        # does not perform destructive actions on their host or network.
                        # Once you have read this disclaimer and taken appropriate precautions,
                        # uncomment the following line and proceed at your own risk:
                        failed = False
                        for i, tc in enumerate(testcases):
                            tc_input, tc_output = tc
                            process = subprocess.Popen([f'java', '-cp', tmp_dir, 'Main'], stdin=subprocess.PIPE,
                                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            out, err = process.communicate(input=tc_input)
                            if len(err) == 0:
                                print(f'\n<TESTCASE OUTPUT {i}>\n{out.strip()}\n</TESTCASE OUTPUT {i}>\n')
                            elif not failed:
                                result.append(f"failed: {err}")
                                failed = True
                            if len(err) > 0:
                                print(f'\n<TESTCASE ERROR {i}>\n{err.strip()}\n</TESTCASE ERROR {i}>\n')
                            if not failed and out.strip() != tc_output.strip():
                                result.append("failed: wrong answer")
                                failed = True
                        if not failed:
                            result.append("passed")
                except TimeoutException:
                    print("time out")
                    if not failed:
                        result.append("time out")
                except BaseException as e:
                    if not failed:
                        result.append(f"failed: {e}")

            shutil.rmtree(tmp_dir)

    manager = multiprocessing.Manager()
    result = manager.list()

    p = multiprocessing.Process(target=unsafe_execute, args=(tmp_dir,))
    p.start()
    p.join(timeout=timeout + 1)
    if p.is_alive():
        p.kill()

    if not result:
        result.append("timed out")

    print(f'\n[RESULT_{"/".join(task_id.split("/")[1:])}_{completion_id}] {result}')

    return {
        "task_id": task_id,
        "completion_id": completion_id,
        "test_code": sample["test_code"],
        "completion": sample["test_code"],
        "result": result[0],
        "passed": result[0] == "passed",
        "finish": -1 if "finish" not in sample else sample["finish"],
        "file": "" if "file" not in sample else sample["file"],
        "output": [] if "output" not in sample else sample["output"],
    }


# Copyright (c) OpenAI (https://openai.com)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ============================================================================
@contextlib.contextmanager
def time_limit(seconds: float):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@contextlib.contextmanager
def swallow_io():
    stream = WriteOnlyStringIO()
    with contextlib.redirect_stdout(stream):
        with contextlib.redirect_stderr(stream):
            with redirect_stdin(stream):
                yield


@contextlib.contextmanager
def create_tempdir():
    with tempfile.TemporaryDirectory() as dirname:
        with chdir(dirname):
            yield dirname


class TimeoutException(Exception):
    pass


class WriteOnlyStringIO(io.StringIO):
    """ StringIO that throws an exception when it's read from """

    def read(self, *args, **kwargs):
        raise IOError

    def readline(self, *args, **kwargs):
        raise IOError

    def readlines(self, *args, **kwargs):
        raise IOError

    def readable(self, *args, **kwargs):
        """ Returns True if the IO object can be read. """
        return False


class redirect_stdin(contextlib._RedirectStream):  # type: ignore
    _stream = 'stdin'


@contextlib.contextmanager
def chdir(root):
    if root == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(root)
    try:
        yield
    except BaseException as exc:
        raise exc
    finally:
        os.chdir(cwd)


def reliability_guard(maximum_memory_bytes: Optional[int] = None):
    """
    This disables various destructive functions and prevents the generated code
    from interfering with the test (e.g. fork bomb, killing other processes,
    removing filesystem files, etc.)

    WARNING
    This function is NOT a security sandbox. Untrusted code, including, model-
    generated code, should not be blindly executed outside of one. See the 
    Codex paper for more information about OpenAI's code sandbox, and proceed
    with caution.
    """

    if maximum_memory_bytes is not None:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (maximum_memory_bytes, maximum_memory_bytes))
        resource.setrlimit(resource.RLIMIT_DATA, (maximum_memory_bytes, maximum_memory_bytes))
        if not platform.uname().system == 'Darwin':
            resource.setrlimit(resource.RLIMIT_STACK, (maximum_memory_bytes, maximum_memory_bytes))

    faulthandler.disable()

    import builtins
    builtins.exit = None
    builtins.quit = None

    import os
    os.environ['OMP_NUM_THREADS'] = '1'

    os.kill = None
    os.system = None
    os.putenv = None
    os.remove = None
    os.removedirs = None
    os.rmdir = None
    os.fchdir = None
    os.setuid = None
    os.fork = None
    os.forkpty = None
    os.killpg = None
    os.rename = None
    os.renames = None
    os.truncate = None
    os.replace = None
    os.unlink = None
    os.fchmod = None
    os.fchown = None
    os.chmod = None
    os.chown = None
    os.chroot = None
    os.fchdir = None
    os.lchflags = None
    os.lchmod = None
    os.lchown = None
    os.getcwd = None
    os.chdir = None

    import shutil
    shutil.rmtree = None
    shutil.move = None
    shutil.chown = None

    import subprocess
    subprocess.Popen = None  # type: ignore

    __builtins__['help'] = None

    import sys
    sys.modules['ipdb'] = None
    sys.modules['joblib'] = None
    sys.modules['resource'] = None
    sys.modules['psutil'] = None
    sys.modules['tkinter'] = None
