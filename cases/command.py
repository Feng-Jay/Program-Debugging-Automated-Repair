"""给课堂脚本用的唯一调用方式，等价于在终端里输入案例命令。

    from cases.command import run
    run(["test", "cutoff", "--quiet", "patch.c"])

就是：

    python3 -m cases test cutoff --quiet patch.c

退出码 0 表示通过。修复演示据此判断补丁，不再调用编译或比对函数。
"""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# 这些词是命令或案例名，不是待测的 C 文件。
WORDS = {"list", "help", "info", "test", "median", "scheme", "npd", "oob", "cutoff"}


def run(argv: list[str]) -> int:
    prepared = []
    for arg in argv:
        if arg.startswith("-") or arg in WORDS:
            prepared.append(arg)
        else:
            # 命令在课程目录下执行，所以文件路径先写成绝对路径。
            prepared.append(str(Path(arg).resolve()))
    # 先刷出调用方已经打印的内容，避免子进程的输出插到前面。
    sys.stdout.flush()
    sys.stderr.flush()
    completed = subprocess.run([sys.executable, "-m", "cases", *prepared], cwd=ROOT)
    return completed.returncode
