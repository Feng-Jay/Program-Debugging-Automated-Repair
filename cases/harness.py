"""编译并运行一个 C++ 文件。只给 `python3 -m cases` 用。

测试使用示例:

    python3 -m cases test cutoff 补丁.cpp
"""

import os
from pathlib import Path
import shutil
import subprocess

CXX = os.environ.get("APR_CXX") or shutil.which("clang++") or shutil.which("g++") or shutil.which("clang")
FLAGS = ["-std=c++17", "-O0", "-g", "-Wall", "-Wextra", "-fsanitize=undefined", "-fno-sanitize-recover=all"]


def compile_cpp(source: Path, binary: Path) -> None:
    if not CXX:
        raise RuntimeError("未找到 C++ 编译器；请安装 clang++/g++（macOS: xcode-select --install）")
    result = subprocess.run(
        [CXX, *FLAGS, str(source), "-o", str(binary)],
        capture_output=True, text=True, timeout=25,
    )
    if result.returncode:
        raise RuntimeError(f"编译失败 ({source.name}):\n{result.stderr}")


def execute(binary: Path, args: list[str], stdin: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(binary), *args], input=stdin, capture_output=True, text=True, timeout=4,
    )


def run_source(source: Path, work: Path, args: list[str], stdin: str) -> subprocess.CompletedProcess[str]:
    """先把 C++ 源文件编译成程序，再喂给它这道题的输入。"""
    binary = work / "program"
    compile_cpp(source, binary)
    return execute(binary, args, stdin)


def matches(result: subprocess.CompletedProcess[str], test: dict) -> bool:
    """对照一条期望。有 expect 时，只要求这句话出现在输出里。"""
    if result.returncode != test.get("exit", 0):
        return False
    if "stdout" in test and result.stdout != test["stdout"]:
        return False
    if "stderr" in test and test.get("check_stderr", True) and result.stderr != test["stderr"]:
        return False
    if "expect" in test and test["expect"] not in result.stdout:
        return False
    return True
