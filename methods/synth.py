"""约束式修复（python3 lab.py synth <案例>）。

先看 run()，再看这三个函数：
  describe_holes   洞在第几行：缺 else、比较运算、局部变量
  components       能填进去的材料：比较符、变量名、测试期望、返回值
  fill_holes       每次只填一个洞

缺 else 时插入的代码来自 utils/snippet.py，和 template 用的是同一段。
日志：logs/synth-<案例>.log
"""

from __future__ import annotations

from cases import ALL
from utils.astutil import COMPARE_OPS, ROLE_TEXT, SourceTree, function_name, line_number, one_line, unique_texts
from utils.evaluate import expected_strings
from utils.localize import Localization, priority, selected
from utils.runlog import start_log, try_candidates
from utils.snippet import guard_block


def components(tree: SourceTree, messages: list[str]) -> dict:
    """收集填洞用的材料。比较符是固定的一组，变量名和字符串来自这份程序和测试。"""
    names: list[str] = []
    for function in tree.functions():
        for name in tree.declared_names(function):
            if name not in names:
                names.append(name)
    return {
        "compare_ops": list(COMPARE_OPS),
        "variables": names,
        "messages": list(messages),
        "returns": ["0", "1", "2"],
    }


def fill_holes(tree: SourceTree, parts: dict, loc: Localization | None = None) -> list[tuple[str, str]]:
    """每个洞只用一种材料填一次，其他代码不动。"""
    ranked: list[tuple[float, str, str]] = []
    role_rank = {"assignment_rhs": 0, "condition": 1, "other": 2}
    for function in tree.functions():
        indent_of = tree.line_indent
        for if_node in tree.if_statements(function):
            if if_node.has_else:
                continue
            if not selected(loc, tree, if_node.start, if_node.end):
                continue
            rank = priority(loc, tree, if_node.start, if_node.end)
            indent = indent_of(if_node.start)
            payloads: list[tuple[str, str]] = []
            for message in parts["messages"]:
                for ret in parts["returns"]:
                    block = " else " + guard_block(indent, message, ret).lstrip()
                    payloads.append((f"else 输出 {message!r} 并 return {ret}", block))
            for ret in parts["returns"]:
                block = " else " + guard_block(indent, None, ret).lstrip()
                payloads.append((f"else return {ret}", block))
            for title, block in payloads:
                code = tree.replace(if_node.end, if_node.end, block)
                ranked.append((rank, f"洞[缺 else] {title}", code))
        for op in tree.compare_ops(function):
            if not selected(loc, tree, op.operator_start, op.operator_end):
                continue
            rank = priority(loc, tree, op.operator_start, op.operator_end)
            for new_op in parts["compare_ops"]:
                if new_op == op.operator:
                    continue
                code = tree.replace(op.operator_start, op.operator_end, new_op)
                ranked.append((rank, f"洞[比较运算] {op.text}：{op.operator} ↦ {new_op}", code))
        declared = set(parts["variables"])
        uses = sorted(tree.identifier_uses(function), key=lambda use: (role_rank.get(use.role, 9), use.start))
        for use in uses:
            if use.name not in declared:
                continue
            if not selected(loc, tree, use.start, use.end):
                continue
            rank = priority(loc, tree, use.start, use.end)
            for other in parts["variables"]:
                if other == use.name:
                    continue
                code = tree.replace(use.start, use.end, other)
                ranked.append((rank, f"洞[变量] {use.name} ↦ {other}", code))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return unique_texts([(label, code) for _, label, code in ranked])


def candidates_for(source_text: str, messages: list[str], loc: Localization | None = None) -> list[tuple[str, str]]:
    """先收集组件，再单洞填充。测试可以直接调用它，不必跑完整日志。"""
    tree = SourceTree(source_text)
    return fill_holes(tree, components(tree, messages), loc)


def describe_holes(tree: SourceTree, loc: Localization | None = None) -> list[str]:
    """列出每个洞在第几行。具体填什么由 fill_holes 展开。"""
    rows: list[str] = []
    for function in tree.functions():
        name = function_name(tree, function)
        for if_node in tree.if_statements(function):
            if if_node.has_else:
                continue
            if not selected(loc, tree, if_node.start, if_node.end):
                continue
            line = line_number(tree, if_node.start)
            cond = one_line(if_node.condition, 48)
            rows.append(f"洞·缺 else  {name} 第{line}行  if ({cond}) 没有 else")
        for op in tree.compare_ops(function):
            if not selected(loc, tree, op.operator_start, op.operator_end):
                continue
            line = line_number(tree, op.operator_start)
            rows.append(f"洞·比较运算  {name} 第{line}行  {one_line(op.text, 48)}  里的 {op.operator}")
        for use in tree.identifier_uses(function):
            if not selected(loc, tree, use.start, use.end):
                continue
            line = line_number(tree, use.start)
            role = ROLE_TEXT.get(use.role, "其他位置")
            rows.append(f"洞·变量  {name} 第{line}行  {use.name}（{role}）")
    return rows


def run(
    case_name: str = "median",
    *,
    limit: int | None = 160,
    stop_on_fix: bool = False,
    loc: Localization | None = None,
) -> bool:
    """先说明洞和组件，再逐个填充并测试。"""
    if case_name not in ALL:
        raise ValueError(f"未知案例：{case_name}")
    case = ALL[case_name]
    original = case.SOURCE.read_text(encoding="utf-8")
    log = start_log("synth", case_name, case.SOURCE)
    try:
        tree = SourceTree(original)
        parts = components(tree, expected_strings(case_name))
        holes = describe_holes(tree, loc)
        all_items = fill_holes(tree, parts, loc)
        items = all_items[:limit] if limit is not None else all_items
        log.emit("每次只填一个洞，其它代码不动。")
        if loc is None:
            log.emit("没有定位结果，找到的洞都会填。")
        else:
            log.emit(f"定位：{loc.summary()}")
        log.emit("组件：")
        log.emit("  比较符 " + " ".join(parts["compare_ops"]))
        log.emit("  变量 " + (" ".join(parts["variables"]) if parts["variables"] else "（没有）"))
        if parts["messages"]:
            shown = "、".join(repr(item) for item in parts["messages"])
            log.emit(f"  字符串 {shown}")
        else:
            log.emit("  字符串 （没有）")
        log.emit("  返回值 " + " ".join(parts["returns"]))
        log.emit("洞：")
        if holes:
            for row in holes:
                log.emit(f"  {row}")
        else:
            log.emit("  （没有缺 else、比较运算或局部变量）")
        log.emit("")
        if len(items) != len(all_items):
            log.emit(f"填法 {len(all_items)} 个，这次测前 {len(items)} 个。")
        else:
            log.emit(f"填法 {len(all_items)} 个。")
        log.emit("")
        matches = try_candidates(
            log,
            case_name=case_name,
            original=original,
            filename=case.SOURCE.name,
            items=items,
            stop_on_fix=stop_on_fix,
        )
        log.emit(f"通过 {len(matches)} 个")
        for label in matches[:5]:
            log.emit(f"  {label}")
        if not matches:
            log.emit("这些洞和组件里，没有通过完整测试的。")
        return bool(matches)
    finally:
        log.save()
