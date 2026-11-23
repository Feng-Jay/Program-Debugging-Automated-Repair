"""把一次演示的说明、补丁和测试结果同时打印并保存。

终端上看得到当前在做什么。完整内容写到 logs/<方法>-<案例>.log。
search、template、synth 生成好候选之后，都调用 try_candidates 逐个测试。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import difflib
import tempfile

from utils.evaluate import has_few, score

ROOT = Path(__file__).resolve().parents[1]


class RunLog:
    """一次命令的日志。emit 既打印，也记下来，最后 save 写成文件。"""

    def __init__(self, kind: str, case_name: str, directory: Path | None = None):
        self.kind = kind
        self.case_name = case_name
        self.directory = directory or (ROOT / "logs")
        self.path = self.directory / f"{kind}-{case_name}.log"
        self._chunks: list[str] = []

    def emit(self, text: str = "") -> None:
        print(text)
        if not text.endswith("\n"):
            text += "\n"
        self._chunks.append(text)

    def save(self) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path.write_text("".join(self._chunks), encoding="utf-8")
        print(f"日志：{self.path}")
        return self.path


def start_log(kind: str, case_name: str, source: Path, directory: Path | None = None) -> RunLog:
    """写上方法名、案例、源文件和时间，供后面的说明接着用。"""
    log = RunLog(kind, case_name, directory)
    log.emit(f"方法：{kind}")
    log.emit(f"案例：{case_name}")
    log.emit(f"程序：{source}")
    log.emit(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.emit("")
    return log


def patch_diff(before: str, after: str, filename: str) -> str:
    """原程序和补丁的 unified diff，只保留改动附近的两行上下文。"""
    diff = "".join(difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=filename,
        tofile=filename + "（补丁）",
        n=2,
    ))
    return diff.rstrip("\n") if diff else "（没有文本变化）"


def result_line(few_ok: bool, full_ok: bool, *, with_few: bool) -> str:
    """把两次测试的通过与否写成一行。没有少量测试时只写完整测试。"""
    full_text = "通过" if full_ok else "失败"
    if not with_few:
        return f"结果：完整测试 {full_text}"
    few_text = "通过" if few_ok else "失败"
    return f"结果：少量测试 {few_text}，完整测试 {full_text}"


def try_candidates(
    log: RunLog,
    *,
    case_name: str,
    original: str,
    filename: str,
    items: list[tuple[str, str]],
    stop_on_fix: bool,
) -> list[str]:
    """逐个打印补丁 diff 并调用测试。

    返回通过完整测试的补丁说明。stop_on_fix 为真时，遇到第一个就停。
    """
    passed: list[str] = []
    with_few = has_few(case_name)
    with tempfile.TemporaryDirectory(prefix="apr-") as tmp:
        for index, (label, code) in enumerate(items, start=1):
            log.emit(f"[{index}/{len(items)}] {label}")
            log.emit(patch_diff(original, code, filename))
            log.emit("编译并测试")
            path = Path(tmp) / f"candidate_{index}.cpp"
            path.write_text(code, encoding="utf-8")
            few_ok, full_ok = score(case_name, path)
            log.emit(result_line(few_ok, full_ok, with_few=with_few))
            log.emit("")
            if full_ok:
                passed.append(label)
                if stop_on_fix:
                    log.emit("通过了，后面的先不跑。")
                    break
    return passed
