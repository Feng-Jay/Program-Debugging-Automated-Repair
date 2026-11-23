"""案例命令，用法类似 Defects4J：一条命令做一件事，用退出码表示成败。

    python3 -m cases list
    python3 -m cases info cutoff
    python3 -m cases test cutoff cases/cutoff/cutoff.cpp
    python3 -m cases test cutoff cases/cutoff/cutoff.fixed.cpp
    python3 -m cases test cutoff --few my_cutoff.cpp
"""

from pathlib import Path
import subprocess
import sys
import tempfile

from cases import ALL
from cases import harness

HELP = """\
用法：python3 -m cases <命令> <案例> [参数]

命令：
  list                              列出全部案例
  info <案例>                       查看缺陷说明、缺陷程序和参考修复的路径
  test <案例> [--quiet] [--few] <文件>
                                    编译并测试指定的 C++ 文件。
                                    --few   只跑少量测试（scheme、npd、oob、cutoff 有）
                                    --quiet 不打印每一条，调用方只看退出码

例子：
  python3 -m cases test cutoff cases/cutoff/cutoff.cpp
  python3 -m cases test cutoff cases/cutoff/cutoff.fixed.cpp
  python3 -m cases test median cases/median/median.cpp
  python3 -m cases test scheme cases/scheme/abc308a.cpp
  python3 -m cases test npd cases/npd/npd.cpp
  python3 -m cases test oob cases/oob/oob.cpp
  python3 -m cases test cutoff cases/cutoff/cutoff.cpp

退出码：0 测试通过，1 失败，2 命令写错。
"""


def do_list() -> int:
    for name, case in ALL.items():
        print(f"{name:8s} {case.BUG}")
    return 0


def do_info(name: str, case) -> int:
    print(f"案例：{name}")
    print(getattr(case, "TASK", ""))
    print(f"缺陷：{case.WHY}")
    origin = getattr(case, "ORIGIN", "")
    if origin:
        print(f"来源：{origin}")
    print(f"缺陷程序：{case.SOURCE}")
    print(f"参考修复：{case.FIXED}")
    print(f"完整测试：{len(case.TESTS)} 条")
    few = getattr(case, "FEW_TESTS", None)
    if few:
        print(f"少量测试：{len(few)} 条（见 {name}.py 里的 FEW_TESTS）")
    return 0


def actual_line(result: subprocess.CompletedProcess[str], expect: str) -> str:
    chosen = ""
    for raw in result.stdout.splitlines():
        if expect and expect.strip() in raw:
            chosen = raw
            break
    if not chosen:
        lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
        chosen = lines[-1] if lines else ""
    text = chosen.replace("\x00", "\\0").strip()
    if ">" in text:
        text = text.rsplit(">", 1)[-1].strip()
    if text:
        return text
    if result.returncode != 0:
        err = [ln.strip() for ln in result.stderr.splitlines() if ln.strip()]
        if err:
            return err[0][:160]
    return "(没有输出)"


def do_test(source: Path, tests: list, quiet: bool, task: str = "") -> int:
    if not source.is_file():
        print(f"错误：找不到源文件 {source}", file=sys.stderr)
        return 1
    if not quiet:
        if task:
            print(task)
            print()
        print(f"测试 {source.name}（{len(tests)} 条）")
    passed = True
    with tempfile.TemporaryDirectory(prefix="apr-") as tmp:
        for test in tests:
            result = harness.run_source(
                source, Path(tmp), test.get("args", []), test.get("stdin", ""),
            )
            ok = harness.matches(result, test)
            passed = ok and passed
            if quiet:
                continue
            mark = "通过" if ok else "失败"
            print(f"  {mark}  {test.get('title', '测试')}")
            if test.get("stdin"):
                print(f"       输入：{' / '.join(test['stdin'].split())}")
            if "expect" in test:
                print(f"       期望：{test['expect'].strip()}")
                print(f"       实际：{actual_line(result, test['expect'])}")
    return 0 if passed else 1


def parse_test_args(args: list[str]):
    few = False
    quiet = False
    source = None
    for arg in args:
        if arg == "--few":
            few = True
        elif arg == "--quiet":
            quiet = True
        elif arg.startswith("-"):
            raise ValueError(f"未知参数：{arg}")
        elif source is None:
            source = Path(arg)
        else:
            raise ValueError("test 只能指定一个 C++ 文件")
    return few, quiet, source


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(HELP)
        return 0
    command, *rest = argv
    if command == "list":
        if rest:
            raise ValueError("list 不接受参数")
        return do_list()
    if command not in ("info", "test"):
        raise ValueError(f"未知命令：{command}")
    if not rest:
        raise ValueError(f"{command} 需要案例名，例如 cutoff")
    name, *rest = rest
    case = ALL.get(name)
    if case is None:
        known = " ".join(ALL)
        raise ValueError(f"未知案例：{name}。可用：{known}")
    if command == "info":
        if rest:
            raise ValueError("info 不接受额外参数")
        return do_info(name, case)
    few, quiet, source = parse_test_args(rest)
    if source is None:
        raise ValueError(
            f"请指定要测试的 C++ 文件，例如 {case.SOURCE.relative_to(Path(__file__).resolve().parents[1])}"
        )
    if few and not getattr(case, "FEW_TESTS", None):
        raise ValueError(f"{name} 没有少量测试")
    tests = case.FEW_TESTS if few else case.TESTS
    return do_test(source, tests, quiet, getattr(case, "TASK", ""))


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (RuntimeError, subprocess.TimeoutExpired, OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1 if isinstance(exc, (RuntimeError, subprocess.TimeoutExpired, OSError)) else 2)
