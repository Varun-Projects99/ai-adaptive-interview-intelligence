import sys
import subprocess
import os
import tempfile
import json
import traceback

CHALLENGES = {
    "two_sum": {
        "title": "Two Sum",
        "difficulty": "Easy",
        "description": "Given an array of integers <code>nums</code> and an integer <code>target</code>, return indices of the two numbers such that they add up to <code>target</code>.<br><br>You may assume that each input would have exactly one solution, and you may not use the same element twice.",
        "constraints": [
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9",
            "Only one valid answer exists."
        ],
        "examples": [
            {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."},
            {"input": "nums = [3,2,4], target = 6", "output": "[1,2]"},
            {"input": "nums = [3,3], target = 6", "output": "[0,1]"}
        ],
        "templates": {
            "python": "def solve(nums, target):\n    # Write your Python code here\n    pass\n",
            "javascript": "function solve(nums, target) {\n    // Write your JavaScript code here\n    return [];\n}\n"
        },
        "test_cases": [
            {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
            {"args": [[3, 2, 4], 6], "expected": [1, 2]},
            {"args": [[3, 3], 6], "expected": [0, 1]},
            {"args": [[1, 5, 8, 3], 11], "expected": [2, 3]}
        ]
    },
    "valid_parentheses": {
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "description": "Given a string <code>s</code> containing just the characters <code>'('</code>, <code>')'</code>, <code>'{'</code>, <code>'}'</code>, <code>'['</code> and <code>']'</code>, determine if the input string is valid.<br><br>An input string is valid if:<br>1. Open brackets must be closed by the same type of brackets.<br>2. Open brackets must be closed in the correct order.",
        "constraints": [
            "1 <= s.length <= 10^4",
            "s consists of parentheses only '()[]{}'."
        ],
        "examples": [
            {"input": "s = \"()\"", "output": "true"},
            {"input": "s = \"()[]{}\"", "output": "true"},
            {"input": "s = \"(]\"", "output": "false"}
        ],
        "templates": {
            "python": "def solve(s):\n    # Write your Python code here\n    pass\n",
            "javascript": "function solve(s) {\n    // Write your JavaScript code here\n    return false;\n}\n"
        },
        "test_cases": [
            {"args": ["()"], "expected": True},
            {"args": ["()[]{}"], "expected": True},
            {"args": ["(]"], "expected": False},
            {"args": ["([)]"], "expected": False},
            {"args": ["{[]}"], "expected": True}
        ]
    },
    "fibonacci": {
        "title": "Fibonacci Number",
        "difficulty": "Easy",
        "description": "The Fibonacci numbers, commonly denoted <code>F(n)</code> form a sequence, called the Fibonacci sequence, such that each number is the sum of the two preceding ones, starting from <code>0</code> and <code>1</code>.<br><br>Given <code>n</code>, calculate <code>F(n)</code>.",
        "constraints": [
            "0 <= n <= 30"
        ],
        "examples": [
            {"input": "n = 2", "output": "1", "explanation": "F(2) = F(1) + F(0) = 1 + 0 = 1."},
            {"input": "n = 3", "output": "2"},
            {"input": "n = 4", "output": "3"}
        ],
        "templates": {
            "python": "def solve(n):\n    # Write your Python code here\n    pass\n",
            "javascript": "function solve(n) {\n    // Write your JavaScript code here\n    return 0;\n}\n"
        },
        "test_cases": [
            {"args": [0], "expected": 0},
            {"args": [1], "expected": 1},
            {"args": [2], "expected": 1},
            {"args": [3], "expected": 2},
            {"args": [4], "expected": 3},
            {"args": [10], "expected": 55},
            {"args": [20], "expected": 6765}
        ]
    },
    "reverse_string": {
        "title": "Reverse String",
        "difficulty": "Easy",
        "description": "Write a function that reverses a string. You must return the reversed string.",
        "constraints": [
            "1 <= s.length <= 10^5",
            "s consists of printable ASCII characters."
        ],
        "examples": [
            {"input": "s = \"hello\"", "output": "\"olleh\""},
            {"input": "s = \"Hannah\"", "output": "\"hannaH\""}
        ],
        "templates": {
            "python": "def solve(s):\n    # Write your Python code here\n    pass\n",
            "javascript": "function solve(s) {\n    // Write your JavaScript code here\n    return \"\";\n}\n"
        },
        "test_cases": [
            {"args": ["hello"], "expected": "olleh"},
            {"args": ["Hannah"], "expected": "hannaH"},
            {"args": ["a"], "expected": "a"},
            {"args": ["InterviewIQ"], "expected": "QIwieveetnI"}
        ]
    }
}

def run_python_code(user_code: str, problem_id: str) -> dict:
    if problem_id not in CHALLENGES:
        return {"error": "Invalid problem ID"}

    challenge = CHALLENGES[problem_id]
    test_cases = challenge["test_cases"]

    # Build the full execution script
    # We will serialize results using a special print separator
    runner_script = f"""
import json
import sys

# User code:
{user_code}

test_cases = {repr(test_cases)}
results = []

for i, tc in enumerate(test_cases):
    args = tc["args"]
    expected = tc["expected"]
    try:
        if isinstance(args, list) and len(args) > 1:
            result = solve(*args)
        else:
            arg = args[0] if isinstance(args, list) else args
            result = solve(arg)
        
        # Match order-independent list equality for Two Sum index output
        passed = False
        if isinstance(expected, list) and isinstance(result, list):
            passed = sorted(expected) == sorted(result)
        else:
            passed = expected == result

        results.append({{
            "index": i,
            "passed": passed,
            "actual": result,
            "expected": expected
        }})
    except Exception as e:
        results.append({{
            "index": i,
            "passed": False,
            "error": str(e),
            "expected": expected
        }})

print("---RESULTS_JSON_START---")
print(json.dumps(results))
print("---RESULTS_JSON_END---")
"""

    temp_file = None
    try:
        # Create temp file in workspace or sys temp
        fd, temp_file_path = tempfile.mkstemp(suffix=".py", prefix="code_test_")
        temp_file = os.fdopen(fd, "w")
        temp_file.write(runner_script)
        temp_file.close()

        # Execute using the running python executable
        process = subprocess.Popen(
            [sys.executable, temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return {
                "success": False,
                "error": "Time Limit Exceeded (execution exceeded 2.0s limit)",
                "console": "Execution timed out.",
                "test_results": []
            }

        # Parse standard output for JSON results block
        console_output = ""
        results_json_str = None
        
        lines = stdout.splitlines()
        capture = False
        for line in lines:
            if line == "---RESULTS_JSON_START---":
                capture = True
                continue
            if line == "---RESULTS_JSON_END---":
                capture = False
                continue
            if capture:
                if results_json_str is None:
                    results_json_str = line
                else:
                    results_json_str += line
            else:
                console_output += line + "\n"

        # If execution error
        if process.returncode != 0:
            err_msg = stderr if stderr else "Execution error occurred."
            return {
                "success": False,
                "error": "Runtime / Compilation Error",
                "console": console_output + "\n" + err_msg,
                "test_results": []
            }

        # Parse test results JSON
        test_results = []
        if results_json_str:
            try:
                test_results = json.loads(results_json_str)
            except Exception as e:
                console_output += f"\nFailed to parse results: {e}"

        all_passed = len(test_results) > 0 and all(r.get("passed", False) for r in test_results)

        return {
            "success": all_passed,
            "console": console_output,
            "error": None if all_passed else "Some test cases failed.",
            "test_results": test_results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "console": traceback.format_exc(),
            "test_results": []
        }
    finally:
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

def run_javascript_code(user_code: str, problem_id: str) -> dict:
    if problem_id not in CHALLENGES:
        return {"error": "Invalid problem ID"}

    challenge = CHALLENGES[problem_id]
    test_cases = challenge["test_cases"]

    # We will try to run JavaScript using node if it's available, otherwise return fallback
    # Check if node exists
    try:
        subprocess.run(["node", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        return {
            "success": False,
            "error": "NodeJS not found",
            "console": "NodeJS runtime is required to execute JavaScript code. Please install NodeJS or switch language to Python.",
            "test_results": []
        }

    # Node js runner builder
    runner_script = f"""
{user_code}

const testCases = {json.dumps(test_cases)};
const results = [];

testCases.forEach((tc, i) => {{
    const args = tc.args;
    const expected = tc.expected;
    try {{
        let result;
        if (Array.isArray(args) && args.length > 1) {{
            result = solve(...args);
        }} else {{
            result = solve(Array.isArray(args) ? args[0] : args);
        }}

        // Match order-independent list equality for Two Sum index output
        let passed = false;
        if (Array.isArray(expected) && Array.isArray(result)) {{
            passed = expected.length === result.length && 
                     expected.slice().sort().every((v, idx) => v === result.slice().sort()[idx]);
        }} else {{
            passed = expected === result;
        }}

        results.push({{
            index: i,
            passed: passed,
            actual: result,
            expected: expected
        }});
    }} catch(e) {{
        results.push({{
            index: i,
            passed: false,
            error: e.message,
            expected: expected
        }});
    }}
}});

console.log("---RESULTS_JSON_START---");
console.log(JSON.stringify(results));
console.log("---RESULTS_JSON_END---");
"""

    temp_file = None
    try:
        fd, temp_file_path = tempfile.mkstemp(suffix=".js", prefix="code_test_")
        temp_file = os.fdopen(fd, "w")
        temp_file.write(runner_script)
        temp_file.close()

        process = subprocess.Popen(
            ["node", temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return {
                "success": False,
                "error": "Time Limit Exceeded",
                "console": "Execution timed out.",
                "test_results": []
            }

        console_output = ""
        results_json_str = None
        
        lines = stdout.splitlines()
        capture = False
        for line in lines:
            if line == "---RESULTS_JSON_START---":
                capture = True
                continue
            if line == "---RESULTS_JSON_END---":
                capture = False
                continue
            if capture:
                if results_json_str is None:
                    results_json_str = line
                else:
                    results_json_str += line
            else:
                console_output += line + "\n"

        if process.returncode != 0:
            err_msg = stderr if stderr else "Execution error occurred."
            return {
                "success": False,
                "error": "Runtime / Compilation Error",
                "console": console_output + "\n" + err_msg,
                "test_results": []
            }

        test_results = []
        if results_json_str:
            try:
                test_results = json.loads(results_json_str)
            except Exception as e:
                console_output += f"\nFailed to parse results: {e}"

        all_passed = len(test_results) > 0 and all(r.get("passed", False) for r in test_results)

        return {
            "success": all_passed,
            "console": console_output,
            "error": None if all_passed else "Some test cases failed.",
            "test_results": test_results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "console": traceback.format_exc(),
            "test_results": []
        }
    finally:
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
