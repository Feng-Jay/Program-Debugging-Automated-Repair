"""搜索式修复（python3 lab.py search <案例>）。

先看 run()，再看三个生成补丁的函数：
  op_replacements    把一处比较符换成另一种
  var_replacements   把一处局部变量换成同函数里的另一个
  statement_edits    删除、替换，或插入程序里已经有的语句

每次只改一处，不按案例名写死补丁。材料必须已经出现在程序里，
所以需要新字符串或新 if 的缺陷，这里可能找不到。
日志：logs/search-<案例>.log
"""

from __future__ import annotations

from cases import ALL
from utils.astutil import COMPARE_OPS, ROLE_TEXT, SourceTree, function_name, line_number, one_line, unique_texts
from utils.runlog import start_log, try_candidates


def _functions(tree: SourceTree):
    functions = tree.functions()
    if not functions:
        raise RuntimeError("源文件里没有函数定义，无法搜索")
    return functions


def op_replacements(tree: SourceTree) -> list[tuple[str, str]]:
    """每处比较运算换成其余比较符，一次只换一个运算符。"""
    candidates: list[tuple[str, str]] = []
    for function in _functions(tree):
        for op in tree.compare_ops(function):
            for new_op in COMPARE_OPS:
                if new_op == op.operator:
                    continue
                code = tree.replace(op.operator_start, op.operator_end, new_op)
                label = f"比较运算: {op.text} 中的 {op.operator} → {new_op}"
                candidates.append((label, code))
    return candidates


def var_replacements(tree: SourceTree) -> list[tuple[str, str]]:
    """每个局部变量的使用处，换成同一函数里声明的另一个名字。"""
    candidates: list[tuple[str, str]] = []
    # 赋值右边和条件里的名字更常是写错的那一个，所以排在前面。
    role_rank = {"assignment_rhs": 0, "condition": 1, "other": 2}
    for function in _functions(tree):
        declared = tree.declared_names(function)
        uses = sorted(tree.identifier_uses(function), key=lambda use: (role_rank.get(use.role, 9), use.start))
        for use in uses:
            for other in declared:
                if other == use.name:
                    continue
                code = tree.replace(use.start, use.end, other)
                label = f"变量替换: {use.name} → {other}（{use.role}）"
                candidates.append((label, code))
    return candidates


def _simple_statements(tree: SourceTree, function):
    """只取表达式语句和 return。整段 if 删掉容易把结构拆坏。"""
    stmts = [s for s in tree.statements(function) if s.type != "compound_statement"]
    return [s for s in stmts if s.type in {"expression_statement", "return_statement"}]


def statement_edits(tree: SourceTree) -> list[tuple[str, str]]:
    """用函数里已有的语句做删除、替换和插入。

    单独的 return 0 不删除，避免把函数收尾删掉；它仍可以拿去替换或插入。
    """
    candidates: list[tuple[str, str]] = []
    for function in _functions(tree):
        simple = _simple_statements(tree, function)
        for stmt in simple:
            stripped = stmt.text.strip()
            if stripped in {"return 0;", "return;"}:
                continue
            code = _delete_statement(tree, stmt.start, stmt.end)
            if code != tree.text:
                candidates.append((f"删除语句: { one_line(stmt.text, 40) }", code))
        for target in simple:
            for donor in simple:
                if donor.span == target.span or donor.text == target.text:
                    continue
                code = tree.replace(target.start, target.end, donor.text)
                candidates.append(
                    (f"替换语句: { one_line(target.text, 40) } ← { one_line(donor.text, 40) }", code)
                )
        for target in simple:
            indent = tree.line_indent(target.start)
            for donor in simple:
                if donor.span == target.span:
                    continue
                insertion = donor.text
                if not insertion.endswith("\n"):
                    insertion = insertion + "\n" + indent
                else:
                    insertion = insertion + indent
                code = tree.replace(target.start, target.start, insertion)
                candidates.append(
                    (f"插入语句: 在 { one_line(target.text, 40) } 前插入 { one_line(donor.text, 40) }", code)
                )
    return candidates


def _delete_statement(tree: SourceTree, start: int, end: int) -> str:
    """删掉语句，并带上紧跟的换行，避免留下空行。"""
    raw_end = end
    if raw_end < len(tree.raw) and tree.raw[raw_end:raw_end + 1] == b"\n":
        raw_end += 1
    return tree.replace(start, raw_end, "")


def candidates_for(source_text: str, *, include_statements: bool = True) -> list[tuple[str, str]]:
    """按比较符、变量、语句的顺序生成补丁，并去掉重复源码。"""
    tree = SourceTree(source_text)
    items: list[tuple[str, str]] = []
    items.extend(op_replacements(tree))
    items.extend(var_replacements(tree))
    if include_statements:
        items.extend(statement_edits(tree))
    return unique_texts(items)


def describe_sites(tree: SourceTree) -> list[str]:
    """列出会改的位置。每个位置一行，先不展开成全部补丁。"""
    rows: list[str] = []
    for function in _functions(tree):
        name = function_name(tree, function)
        for op in tree.compare_ops(function):
            line = line_number(tree, op.operator_start)
            rows.append(f"比较运算  {name} 第{line}行  {one_line(op.text, 48)}  里的 {op.operator}")
        for use in tree.identifier_uses(function):
            line = line_number(tree, use.start)
            role = ROLE_TEXT.get(use.role, "其他位置")
            rows.append(f"局部变量  {name} 第{line}行  {use.name}（{role}）")
        for stmt in _simple_statements(tree, function):
            line = line_number(tree, stmt.start)
            text = one_line(stmt.text, 48)
            if stmt.text.strip() in {"return 0;", "return;"}:
                rows.append(f"已有语句  {name} 第{line}行  {text}  （不删除，只拿来替换或插入）")
            else:
                rows.append(f"已有语句  {name} 第{line}行  {text}")
    return rows


def run(case_name: str = "median", *, limit: int | None = 120, stop_on_fix: bool = False) -> bool:
    """说明要改的位置，再逐个测试补丁。有补丁通过完整测试就返回 True。"""
    if case_name not in ALL:
        raise ValueError(f"未知案例：{case_name}")
    case = ALL[case_name]
    original = case.SOURCE.read_text(encoding="utf-8")
    log = start_log("search", case_name, case.SOURCE)
    try:
        tree = SourceTree(original)
        all_items = candidates_for(original)
        items = all_items[:limit] if limit is not None else all_items
        log.emit("每次只改一处：比较符、局部变量，或已有语句的删除、替换、插入。")
        log.emit("位置：")
        sites = describe_sites(tree)
        if sites:
            for row in sites:
                log.emit(f"  {row}")
        else:
            log.emit("  （没有比较运算、局部变量或简单语句）")
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
            log.emit("要写的语句如果原来没有，搜索也变不出来。")
        return found
    finally:
        log.save()
