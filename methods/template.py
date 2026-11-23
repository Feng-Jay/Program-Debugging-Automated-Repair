"""模板式修复（python3 lab.py template <案例>）。

先看 run()，再看三条模板：
  relop_template         把一处关系运算符换成另一种
  null_check_template    在 p-> 或 *p 前面插入空指针检查
  missing_else_template  给没有 else 的 if 补一个分支

插入的打印文字来自测试期望，见 utils/snippet.py。不按案例名写死补丁。
日志：logs/template-<案例>.log
"""

from __future__ import annotations

from cases import ALL
from utils.astutil import COMPARE_OPS, SourceTree, function_name, line_number, one_line, unique_texts
from utils.evaluate import expected_strings
from utils.runlog import start_log, try_candidates
from utils.snippet import guard_block


def relop_template(tree: SourceTree) -> list[tuple[str, str]]:
    """每处比较运算换成其余比较符。和 search 的比较符替换是同一种编辑。"""
    candidates: list[tuple[str, str]] = []
    for function in tree.functions():
        for op in tree.compare_ops(function):
            for new_op in COMPARE_OPS:
                if new_op == op.operator:
                    continue
                code = tree.replace(op.operator_start, op.operator_end, new_op)
                candidates.append((f"模板[关系运算] {op.operator} → {new_op}（在 {op.text}）", code))
    return candidates


def null_check_template(tree: SourceTree, messages: list[str]) -> list[tuple[str, str]]:
    """在使用指针的语句前插入 if (p == nullptr) 或 if (!p)。"""
    candidates: list[tuple[str, str]] = []
    returns = ("0", "1", "2")
    bodies: list[tuple[str, str | None, str]] = []
    for message in messages:
        for ret in returns:
            bodies.append((f"输出 {message!r} 并 return {ret}", message, ret))
    for ret in returns:
        bodies.append((f"仅 return {ret}", None, ret))
    for function in tree.functions():
        for use in tree.pointer_uses(function):
            indent = tree.line_indent(use.statement_start)
            # 语句前如果已经有检查，仍然生成。过不过交给测试。
            for condition in (f"{use.pointer} == nullptr", f"!{use.pointer}"):
                for title, message, ret in bodies:
                    block = (
                        f"if ({condition}) "
                        + guard_block(indent, message, ret).lstrip()
                        + "\n"
                        + indent
                    )
                    code = tree.replace(use.statement_start, use.statement_start, block)
                    candidates.append(
                        (f"模板[空指针检查] 在使用 {use.pointer}{use.kind} 前：if ({condition}) / {title}", code)
                    )
    return candidates


def missing_else_template(tree: SourceTree, messages: list[str]) -> list[tuple[str, str]]:
    """给没有 else 的 if 接上一个 else 分支。"""
    candidates: list[tuple[str, str]] = []
    payloads: list[tuple[str, str | None, str]] = []
    for message in messages:
        payloads.append((f"输出 {message!r} 并返回", message, "0"))
    payloads.append(("直接 return 0", None, "0"))
    payloads.append(("直接 return 1", None, "1"))
    for function in tree.functions():
        for if_node in tree.if_statements(function):
            if if_node.has_else:
                continue
            indent = tree.line_indent(if_node.start)
            for title, message, ret in payloads:
                else_block = " else " + guard_block(indent, message, ret).lstrip()
                code = tree.replace(if_node.end, if_node.end, else_block)
                cond = " ".join(if_node.condition.split())
                if len(cond) > 40:
                    cond = cond[:39] + "…"
                candidates.append((f"模板[补 else] 接在 if ({cond}) 后：{title}", code))
    return candidates


def candidates_for(source_text: str, messages: list[str]) -> list[tuple[str, str]]:
    """先生成会插入新语句的模板，再换比较符，方便先看到结构上的修改。"""
    tree = SourceTree(source_text)
    items: list[tuple[str, str]] = []
    items.extend(null_check_template(tree, messages))
    items.extend(missing_else_template(tree, messages))
    items.extend(relop_template(tree))
    return unique_texts(items)


def describe_matches(tree: SourceTree) -> list[str]:
    """列出每条模板匹配到第几行，先不展开成全部补丁。"""
    rows: list[str] = []
    for function in tree.functions():
        name = function_name(tree, function)
        for op in tree.compare_ops(function):
            line = line_number(tree, op.operator_start)
            rows.append(f"关系运算  {name} 第{line}行  {one_line(op.text, 48)}  里的 {op.operator}")
        for use in tree.pointer_uses(function):
            line = line_number(tree, use.statement_start)
            stmt = one_line(tree.raw[use.statement_start:use.statement_end].decode("utf-8"), 48)
            rows.append(f"空指针检查  {name} 第{line}行  使用 {use.pointer}{use.kind}  的语句：{stmt}")
        for if_node in tree.if_statements(function):
            if if_node.has_else:
                continue
            line = line_number(tree, if_node.start)
            rows.append(f"补 else  {name} 第{line}行  if ({one_line(if_node.condition, 48)}) 没有 else")
    return rows


def run(case_name: str = "median", *, limit: int | None = 160, stop_on_fix: bool = False) -> bool:
    """先说明匹配到哪里，再逐个套用模板并测试。"""
    if case_name not in ALL:
        raise ValueError(f"未知案例：{case_name}")
    case = ALL[case_name]
    original = case.SOURCE.read_text(encoding="utf-8")
    log = start_log("template", case_name, case.SOURCE)
    try:
        tree = SourceTree(original)
        messages = expected_strings(case_name)
        matches = describe_matches(tree)
        all_items = candidates_for(original, messages)
        items = all_items[:limit] if limit is not None else all_items
        log.emit("模板：换关系符、指针前加空检查、给没有 else 的 if 补分支。")
        log.emit("打印的文字用这个案例测试里的期望输出。")
        if messages:
            log.emit("期望：" + "、".join(repr(item) for item in messages))
        else:
            log.emit("期望：（没有字符串）")
        log.emit("匹配：")
        if matches:
            for row in matches:
                log.emit(f"  {row}")
        else:
            log.emit("  （没有关系运算、指针使用或缺 else 的 if）")
        log.emit("")
        if len(items) != len(all_items):
            log.emit(f"补丁 {len(all_items)} 个，这次测前 {len(items)} 个。")
        else:
            log.emit(f"补丁 {len(all_items)} 个。")
        log.emit("")
        interesting = try_candidates(
            log,
            case_name=case_name,
            original=original,
            filename=case.SOURCE.name,
            items=items,
            stop_on_fix=stop_on_fix,
        )
        found = bool(interesting)
        if interesting:
            log.emit(f"通过 {len(interesting)} 个，例如：{interesting[0]}")
        else:
            log.emit("没有通过完整测试的补丁。")
        return found
    finally:
        log.save()
