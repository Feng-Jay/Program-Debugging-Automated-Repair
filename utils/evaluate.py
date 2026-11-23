"""用课堂测试命令给补丁打分。

修复方法不要自己编译。这里只执行：

    python3 -m cases test <案例> [--few] --quiet <文件.cpp>

退出码 0 算通过。少量测试和完整测试的差别由案例自己的 FEW_TESTS 决定。
"""

from __future__ import annotations

from pathlib import Path

from cases import ALL
from cases.command import run as case_command


def expected_strings(case_name: str) -> list[str]:
    """收集测试里要求出现的输出。template 和 synth 把它们当作可填入的字符串。"""
    case = ALL[case_name]
    values: list[str] = []
    seen: set[str] = set()
    for test in getattr(case, "TESTS", []):
        for key in ("expect", "stdout"):
            raw = test.get(key)
            if not raw:
                continue
            text = raw.strip("\n")
            if text and text not in seen:
                seen.add(text)
                values.append(text)
    return values


def has_few(case_name: str) -> bool:
    """这个案例有没有单独的少量测试。没有的话，弱测试和完整测试是同一套。"""
    return bool(getattr(ALL[case_name], "FEW_TESTS", None))


def evaluate(case_name: str, source: Path, *, few: bool = False, quiet: bool = True) -> bool:
    """跑一轮测试。few 为真时只跑少量测试。"""
    args = ["test", case_name]
    if few:
        if not has_few(case_name):
            return evaluate(case_name, source, few=False, quiet=quiet)
        args.append("--few")
    if quiet:
        args.append("--quiet")
    args.append(str(source))
    return case_command(args) == 0


def score(case_name: str, source: Path) -> tuple[bool, bool]:
    """返回 (少量测试是否通过, 完整测试是否通过)。

    先跑完整测试。已经全部通过时，少量测试不必再跑。
    """
    full_ok = evaluate(case_name, source, few=False, quiet=True)
    if not has_few(case_name):
        return full_ok, full_ok
    # 已通过完整测试时，少量测试必然通过，不必再跑一遍。
    if full_ok:
        return True, True
    few_ok = evaluate(case_name, source, few=True, quiet=True)
    return few_ok, full_ok
