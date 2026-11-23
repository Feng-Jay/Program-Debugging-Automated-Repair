"""基于模型的修复（python3 lab.py prompt / llm <案例>）。

先看 prompt()：把题目、失败现象、测试和源码写成一段文字。
show() 把这段文字打印并保存。run() 才可能发起真实请求。

默认使用 DeepSeek。没有密钥时不发请求。
返回的代码不写入文件，也不执行。日志：logs/prompt-<案例>.log、logs/llm-<案例>.log
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from cases import ALL
from utils.localize import Localization
from utils.runlog import start_log

DEEPSEEK_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"


def credentials() -> dict | None:
    """只从环境变量读取本课程用的密钥，不打印密钥本身。"""
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if deepseek_key:
        base = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or DEEPSEEK_BASE
        model = os.environ.get("DEEPSEEK_MODEL") or os.environ.get("OPENAI_MODEL") or DEEPSEEK_MODEL
        return {
            "provider": "deepseek",
            "model": model,
            "url": base.rstrip("/") + "/chat/completions",
            "key": deepseek_key,
        }
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        base = os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        model = os.environ.get("OPENAI_MODEL") or DEEPSEEK_MODEL
        return {
            "provider": "openai-compatible",
            "model": model,
            "url": base.rstrip("/") + "/chat/completions",
            "key": openai_key,
        }
    return None


def prompt(case_name: str = "median", loc: Localization | None = None) -> str:
    if case_name not in ALL:
        raise ValueError(f"未知案例：{case_name}")
    case = ALL[case_name]
    code = case.SOURCE.read_text(encoding="utf-8")
    task = getattr(case, "TASK", "").strip()
    why = getattr(case, "WHY", "").strip()
    lines = [
        "修下面这份 C++。改动尽量小，给出 unified diff，并说明原因。",
        "",
    ]
    if task:
        lines.append(task)
        lines.append("")
    if why:
        lines.append(f"已知失败现象：{why}")
        lines.append("")
    lines.append("测试期望（输入与输出中应出现的内容）：")
    for test in getattr(case, "TESTS", []):
        title = test.get("title", "测试")
        stdin = " ".join((test.get("stdin") or "").split())
        expect = (test.get("expect") or test.get("stdout") or "").rstrip("\n")
        lines.append(f"- {title}：输入 {stdin!r} -> {expect}")
    lines.append("")
    lines.append("已经能过的测试别改坏。")
    lines.append("")
    if loc is not None:
        lines.append("可疑位置，优先改这些行：")
        lines.extend(f"- 第{number}行" for number, _ in loc.ranked)
        lines.append("")
    lines.append("代码：")
    lines.append("```cpp")
    lines.append(code.rstrip())
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def show(case_name: str = "median", loc: Localization | None = None) -> bool:
    """打印并保存离线提示。不改程序，也不调用模型。"""
    if case_name not in ALL:
        raise ValueError(f"未知案例：{case_name}")
    case = ALL[case_name]
    log = start_log("prompt", case_name, case.SOURCE)
    try:
        if loc is None:
            log.emit("没有定位结果。")
        else:
            log.emit(f"定位：{loc.summary()}")
        log.emit("")
        log.emit(prompt(case_name, loc))
        return True
    finally:
        log.save()


def run(case_name: str = "median", loc: Localization | None = None) -> bool:
    """发起真实 API 调用。没有密钥时返回 False，并说明未验证。"""
    if case_name not in ALL:
        raise ValueError(f"未知案例：{case_name}")
    case = ALL[case_name]
    log = start_log("llm", case_name, case.SOURCE)
    try:
        cfg = credentials()
        if cfg is None:
            if loc is None:
                log.emit("没有定位结果。")
            else:
                log.emit(f"定位：{loc.summary()}")
            log.emit("没有 DEEPSEEK_API_KEY 或 OPENAI_API_KEY，没有发请求。")
            log.emit(f"提示在：python3 lab.py prompt {case_name}")
            log.emit(
                "export DEEPSEEK_API_KEY='你的密钥'\n"
                f"python3 lab.py llm {case_name}"
            )
            return False
        if loc is None:
            log.emit("没有定位结果。")
        else:
            log.emit(f"定位：{loc.summary()}")
        log.emit(f"请求 {cfg['provider']} / {cfg['model']}")
        payload = json.dumps({
            "model": cfg["model"],
            "messages": [{"role": "user", "content": prompt(case_name, loc)}],
            "temperature": 0,
            "stream": False,
        }).encode("utf-8")
        request = urllib.request.Request(cfg["url"], data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg["key"],
        }, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=50) as response:
                body = json.load(response)
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise RuntimeError("模型返回内容不是文本")
            log.emit("回复：")
            log.emit(content)
            log.emit("")
            log.emit("上面的代码没有自动跑，也没有写入文件。")
            return True
        except (urllib.error.URLError, ValueError, KeyError, IndexError, TimeoutError) as exc:
            log.emit(f"请求失败：{type(exc).__name__}: {exc}")
            return False
    finally:
        log.save()
