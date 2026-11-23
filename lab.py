#!/usr/bin/env python3
"""课堂入口。

list / verify 转去执行案例命令。verify 会把要测的文件传给 test。
ast 画出语法树。template / search / synth / prompt / llm 对指定案例生成或验证补丁。
每次运行把过程写到 logs/。
"""

import argparse
from pathlib import Path
import subprocess
import sys
import unittest

from cases import ALL
from cases.command import run as case_command
from methods import astview, model, search, synth, template
from utils.localize import load_localization


def _assert_methods_are_general() -> None:
    """方法源码里不应出现某个案例的现成正确答案。"""
    root = Path(__file__).resolve().parent
    banned = [
        "insert_else",
        'cout << "找不到',
        "small = num1",
        "index >= 4",
        "s[i] > s[i + 1]",
        "score >= 60",
    ]
    sources = list((root / "methods").glob("*.py")) + list((root / "utils").glob("*.py"))
    for path in sorted(sources):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                raise RuntimeError(f"{path.name} 含有针对样例的硬编码片段：{token!r}")


def selftest() -> bool:
    passed = True
    for name, case in ALL.items():
        print("\n" + "=" * 60)
        print(f"{name}：有缺陷的程序 {case.SOURCE.name}")
        buggy_failed = case_command(["test", name, str(case.SOURCE)]) != 0
        print(f"{name}：参考修复 {case.FIXED.name}")
        fixed_passed = case_command(["test", name, str(case.FIXED)]) == 0
        passed = buggy_failed and fixed_passed and passed
        if not (buggy_failed and fixed_passed):
            print(f"SELFTEST 失败：{name} 的缺陷程序或参考修复未达到预期")

    print("\n" + "=" * 60)
    print("检查修复方法没有把现成补丁写进源码")
    try:
        _assert_methods_are_general()
        print("  通过：methods 中未见案例特判字符串")
    except RuntimeError as exc:
        print(f"  失败：{exc}")
        passed = False

    print("\n" + "=" * 60)
    print("语法树与修复泛化单元测试")
    suite = unittest.defaultTestLoader.discover(
        str(Path(__file__).resolve().parent / "tests"),
        pattern="test_*.py",
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.wasSuccessful() and passed

    # 课堂方法在真实案例上的回归：找到通过完整测试的补丁即成功。
    # search 依赖程序内部已有材料，对 npd 可能找不到补丁，不作为失败条件。
    method_jobs = [
        ("template", template.run, "cutoff", True),
        ("template", template.run, "oob", True),
        ("template", template.run, "npd", True),
        ("synth", synth.run, "cutoff", True),
        ("search", search.run, "cutoff", True),
        ("search", search.run, "oob", True),
        ("search", search.run, "scheme", True),
        ("search", search.run, "median", True),
    ]
    for title, func, case_name, required in method_jobs:
        print("\n" + "=" * 60)
        print(f"{title} {case_name}")
        try:
            ok = func(case_name, stop_on_fix=True)
        except (RuntimeError, subprocess.TimeoutExpired, OSError, ValueError) as exc:
            print(f"错误：{exc}")
            ok = False
        if required and not ok:
            print(f"SELFTEST 失败：{title} 未能修复 {case_name}")
            passed = False
        elif ok:
            print(f"SELFTEST：{title} 已得到能通过 {case_name} 完整测试的补丁")
        else:
            print(f"SELFTEST：{title} 未修复 {case_name}（本次不作为失败）")

    print("\n" + "=" * 60)
    print("模型接口：没有密钥时不应返回成功")
    if model.credentials() is None:
        ok = model.run("cutoff")
        if ok:
            print("SELFTEST 失败：没有密钥时 llm 不应返回成功")
            passed = False
        else:
            print("  通过：没有密钥，未发请求")
    else:
        print("  检测到 API 密钥，跳过“无密钥”断言（本次不自动发起联网请求）")

    print("\nSELFTEST:", "PASS" if passed else "FAIL")
    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description="APR 课程实验：测试指定的 C 文件、观察修复方法")
    parser.add_argument("action", choices=[
        "list", "verify", "ast", "template", "search", "synth", "prompt", "llm", "selftest",
    ])
    parser.add_argument("case", nargs="?", choices=list(ALL), default="cutoff")
    parser.add_argument("--source", type=Path, help="verify 时指定自己的 C 补丁（不覆盖原始文件）")
    parser.add_argument("--loc", type=Path, help="定位结果。每行一个行号，可选可疑度；靠前的行优先")
    args = parser.parse_args()
    try:
        loc = load_localization(args.loc) if args.loc else None
        if loc is not None and args.action not in {"template", "search", "synth", "prompt", "llm"}:
            raise ValueError("--loc 只用于 search、template、synth、prompt、llm")
        if args.action == "list":
            return case_command(["list"])
        if args.action == "selftest":
            return 0 if selftest() else 1
        if args.action == "verify":
            source = args.source or ALL[args.case].FIXED
            return case_command(["test", args.case, str(source)])
        if args.action == "ast":
            return 0 if astview.run(args.case) else 1
        if args.action == "template":
            return 0 if template.run(args.case, loc=loc) else 1
        if args.action == "search":
            return 0 if search.run(args.case, loc=loc) else 1
        if args.action == "synth":
            return 0 if synth.run(args.case, loc=loc) else 1
        if args.action == "prompt":
            return 0 if model.show(args.case, loc=loc) else 1
        if args.action == "llm":
            return 0 if model.run(args.case, loc=loc) else 1
    except (RuntimeError, subprocess.TimeoutExpired, OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
