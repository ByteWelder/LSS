"""
Runs the integration tests in tests/cases.

Each test is a <name>.lss file with the expected output in <name>.h and <name>.c.
All tests are run, and all failures are reported at the end.

Usage: python tests/run_tests.py [--update]

    --update    overwrite the expected .h and .c files with the current output
"""
import contextlib
import glob
import io
import os
import sys

LSS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(LSS_DIR, "tests", "cases")
sys.path.insert(0, LSS_DIR)

from source.codegenerator import CodeGenerator
from source.files import read_file, write_file
from source.main import parse
from source.templates import render_templates


def generate(lss_path: str) -> dict:
    """Returns a dict that maps the file extension (".h" or ".c") onto the generated content"""
    generator = CodeGenerator(parse(read_file(lss_path)))
    files = render_templates(generator)
    return {os.path.splitext(file_name)[1]: content for file_name, content in files.items()}


def context_lines(lines: list, index: int, marker_index: int) -> list:
    result = []
    for i in range(index - 1, index + 2):
        if i < 0:
            continue
        marker = ">" if i == marker_index else " "
        text = lines[i] if i < len(lines) else "<end of file>"
        result.append(f"    {marker} {i + 1:5} | {text}")
        if i >= len(lines):
            break
    return result


def find_mismatch(expected: str, actual: str):
    """Returns a description of the first mismatching line, or None when the content matches"""
    expected_lines = expected.splitlines()
    actual_lines = actual.splitlines()
    for index in range(max(len(expected_lines), len(actual_lines))):
        expected_line = expected_lines[index] if index < len(expected_lines) else None
        actual_line = actual_lines[index] if index < len(actual_lines) else None
        if expected_line != actual_line:
            lines = [f"  mismatch at line {index + 1}", "  expected:"]
            lines += context_lines(expected_lines, index, index)
            lines.append("  actual:")
            lines += context_lines(actual_lines, index, index)
            return "\n".join(lines)
    return None


def run_case(lss_path: str, update: bool) -> list:
    """Runs a single test and returns a list of failure descriptions"""
    name = os.path.splitext(os.path.basename(lss_path))[0]
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            generated = generate(lss_path)
    except SystemExit:
        return [f"  compilation failed:\n    {output.getvalue().strip()}"]

    failures = []
    for extension in (".h", ".c"):
        expected_path = os.path.join(CASES_DIR, name + extension)
        if update:
            write_file(expected_path, generated[extension])
            continue
        if not os.path.exists(expected_path):
            failures.append(f"  {name}{extension}: expected file is missing (run with --update to create it)")
            continue
        mismatch = find_mismatch(read_file(expected_path), generated[extension])
        if mismatch is not None:
            failures.append(f"  {name}{extension}:\n{mismatch}")
    return failures


def main():
    update = "--update" in sys.argv
    lss_paths = sorted(glob.glob(os.path.join(CASES_DIR, "*.lss")))
    failed = []
    for lss_path in lss_paths:
        name = os.path.basename(lss_path)
        failures = run_case(lss_path, update)
        if failures:
            failed.append(name)
            print(f"FAIL {name}")
            for failure in failures:
                print(failure)
        else:
            print(f"{'UPDATED' if update else 'PASS'} {name}")

    print()
    print(f"{len(lss_paths) - len(failed)} passed, {len(failed)} failed")
    for name in failed:
        print(f"  failed: {name}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
