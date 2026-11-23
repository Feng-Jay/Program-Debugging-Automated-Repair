"""把语法树画成图（python3 lab.py ast <案例>）。

终端里打印一棵缩进树，同时写出 Graphviz 的 .dot，并尽量生成 .svg 图片。
每个节点只写行号和对应代码。不修改程序，也不运行测试。
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from cases import ALL
from utils.astutil import COMPARE_OPS, SourceTree, line_number, one_line
from utils.runlog import ROOT, start_log

class _View:
    def __init__(self, title: str):
        self.title = title
        self.children: list[_View] = []


def run(case_name: str = "cutoff") -> bool:
    """解析案例的缺陷程序，打印语法树，并写出 dot 和 svg。"""
    if case_name not in ALL:
        raise ValueError(f"未知案例：{case_name}")
    case = ALL[case_name]
    original = case.SOURCE.read_text(encoding="utf-8")
    log = start_log("ast", case_name, case.SOURCE)
    try:
        log.emit(diagram(original))
        log.emit("")
        dot_path, image_path = write_picture(original, case_name)
        log.emit(f"dot  {dot_path}")
        if image_path is not None:
            log.emit(f"svg  {image_path}")
        else:
            log.emit("本机没有 dot，只写了 .dot。装好 Graphviz 后可以：")
            log.emit(f"  dot -Tsvg {dot_path} -o {dot_path.with_suffix('.svg')}")
        return True
    finally:
        log.save()


def diagram(source_text: str) -> str:
    """返回终端里那棵缩进树。测试和 run() 都用它。"""
    lines = ["语法树（括号、分号、花括号不单列）", ""]
    _write_views(_forest(source_text), "", lines)
    return "\n".join(lines)


def dot_source(source_text: str) -> str:
    """返回 Graphviz 的 DOT 文本。节点文字与终端里的树相同。"""
    root = _View("程序")
    root.children = _forest(source_text)
    return _to_dot(root)


def write_picture(source_text: str, case_name: str, directory: Path | None = None) -> tuple[Path, Path | None]:
    """把 DOT 写到 logs/ast-<案例>.dot，能调用 dot 时再写出同名 .svg。"""
    folder = directory or (ROOT / "logs")
    folder.mkdir(parents=True, exist_ok=True)
    dot_path = folder / f"ast-{case_name}.dot"
    dot_path.write_text(dot_source(source_text), encoding="utf-8")
    image_path = _render_svg(dot_path)
    return dot_path, image_path


def _forest(source_text: str) -> list[_View]:
    tree = SourceTree(source_text)
    children = [child for child in tree.tree.root_node.children if child.is_named]
    views = []
    for child in children:
        view = _view(tree, child, None, set())
        if view is not None:
            views.append(view)
    return views


def _write_views(views: list[_View], prefix: str, lines: list[str]) -> None:
    for index, view in enumerate(views):
        last = index == len(views) - 1
        branch = "└─ " if last else "├─ "
        title_lines = view.title.splitlines() or [""]
        lines.append(f"{prefix}{branch}{title_lines[0]}")
        # 同一节点的后续行沿着树干对齐，不另起分支。
        spine = prefix + ("   " if last else "│  ")
        for extra in title_lines[1:]:
            lines.append(f"{spine}{extra}")
        _write_views(view.children, spine, lines)


def _view(tree, node, function, declared) -> _View | None:
    if not node.is_named:
        return None

    if node.type == "comment":
        return _View(_label(tree, node))

    if node.type == "preproc_include":
        return _View(_label(tree, node))

    if node.type == "function_definition":
        view = _View(_label(tree, node))
        body = node.child_by_field_name("body")
        names = set(tree.declared_names(node))
        if body is not None and body.type == "compound_statement":
            _add_children(view, tree, body.children, node, names)
        return view

    if node.type in {"declaration", "struct_specifier"}:
        return _View(_label(tree, node))

    if node.type == "if_statement":
        return _view_if(tree, node, function, declared)

    if node.type in {"for_statement", "while_statement", "do_statement"}:
        view = _View(_label(tree, node))
        body = node.child_by_field_name("body")
        if body is None:
            for child in node.children:
                if child.type == "compound_statement":
                    body = child
                    break
        if body is not None and body.type == "compound_statement":
            _add_children(view, tree, body.children, function, declared)
        elif body is not None:
            child = _view(tree, body, function, declared)
            if child is not None:
                view.children.append(child)
        return view

    if node.type == "expression_statement":
        return _view_statement(tree, node, function, declared)

    if node.type == "return_statement":
        return _view_statement(tree, node, function, declared)

    if node.type == "compound_statement":
        # 调用方会展开花括号里的语句，这里不单独占一个节点。
        return None

    return _View(_label(tree, node))


def _add_children(parent: _View, tree, nodes, function, declared) -> None:
    for node in nodes:
        if not node.is_named:
            continue
        child = _view(tree, node, function, declared)
        if child is not None:
            parent.children.append(child)


def _view_if(tree, node, function, declared) -> _View:
    condition = node.child_by_field_name("condition")
    consequence = node.child_by_field_name("consequence")
    alternative = node.child_by_field_name("alternative")
    view = _View(_label(tree, node))
    if condition is not None:
        view.children.extend(_compare_views(tree, condition))
    if consequence is not None:
        _add_children(view, tree, _branch_nodes(consequence), function, declared)
    if alternative is not None:
        alt_node = _unwrap_else(alternative)
        if alt_node.type == "if_statement":
            view.children.append(_view_if(tree, alt_node, function, declared))
        else:
            _add_children(view, tree, _branch_nodes(alt_node), function, declared)
    return view


def _unwrap_else(node):
    if node.type != "else_clause":
        return node
    named = [child for child in node.children if child.is_named]
    return named[0] if named else node


def _branch_nodes(node):
    if node is None:
        return []
    if node.type == "compound_statement":
        return [child for child in node.children if child.is_named]
    if node.type == "else_clause":
        named = [child for child in node.children if child.is_named]
        return named or [node]
    return [node]


def _compare_views(tree, node) -> list[_View]:
    views = []
    for current in tree.walk(node):
        if current.type != "binary_expression":
            continue
        op_node = next((child for child in current.children if not child.is_named), None)
        if op_node is None:
            continue
        op = tree.node_text(op_node)
        if op not in COMPARE_OPS:
            continue
        views.append(_View(_label(tree, current)))
    return views


def _view_statement(tree, node, function, declared) -> _View:
    view = _View(_label(tree, node))
    view.children.extend(_statement_extras(tree, node, function, declared))
    return view


def _statement_extras(tree, node, function, declared) -> list[_View]:
    if function is None:
        return []
    extras: list[_View] = []
    covered: list[tuple[int, int]] = []
    for current in tree.walk(node):
        if current.type == "field_expression":
            op = next((tree.node_text(child) for child in current.children if not child.is_named), "")
            if op != "->":
                continue
            extras.append(_View(_label(tree, current)))
            covered.append((current.start_byte, current.end_byte))
        elif current.type == "pointer_expression":
            op = next((tree.node_text(child) for child in current.children if not child.is_named), "")
            if op != "*":
                continue
            extras.append(_View(_label(tree, current)))
            covered.append((current.start_byte, current.end_byte))
        elif current.type == "subscript_expression":
            extras.append(_View(_label(tree, current)))
            covered.append((current.start_byte, current.end_byte))
    seen: set[str] = set()
    for use in tree.identifier_uses(function):
        if not (node.start_byte <= use.start < node.end_byte):
            continue
        if use.name not in declared:
            continue
        if any(start <= use.start < end for start, end in covered):
            continue
        title = _label_at(tree, use.start, use.name)
        if title in seen:
            continue
        seen.add(title)
        extras.append(_View(title))
    return extras


def _label(tree, node) -> str:
    """行号加上这段节点自己的代码。语句跨行时只保留第一行，注释保留每一行。"""
    code = tree.node_text(node)
    if node.type == "comment":
        return _comment_label(tree, node.start_byte, code)
    return _label_at(tree, node.start_byte, code)


def _comment_label(tree, byte_pos: int, code: str) -> str:
    """块注释是一个节点，但正文跨多行。每一行都标上它自己的行号。"""
    start = line_number(tree, byte_pos)
    rows = code.splitlines() or [""]
    return "\n".join(f"{start + index}  {row.rstrip()}" for index, row in enumerate(rows))


def _label_at(tree, byte_pos: int, code: str) -> str:
    line = line_number(tree, byte_pos)
    first = code.strip().splitlines()[0] if code.strip() else ""
    return f"{line}  {one_line(first, 64)}"


def _to_dot(root: _View) -> str:
    lines = [
        "digraph ast {",
        "  rankdir=TB;",
        '  graph [pad="0.4", nodesep="0.35", ranksep="0.45", bgcolor="white"];',
        '  node [shape=box, style="rounded", fontname="PingFang SC", fontsize=13, margin="0.15,0.08"];',
        '  edge [color="#8A8A8A"];',
    ]
    counter = 0

    def emit(view: _View, parent: str | None) -> None:
        nonlocal counter
        ident = f"n{counter}"
        counter += 1
        lines.append(f'  {ident} [label="{_dot_label(view.title)}"];')
        if parent is not None:
            lines.append(f"  {parent} -> {ident};")
        for child in view.children:
            emit(child, ident)

    emit(root, None)
    lines.append("}")
    return "\n".join(lines) + "\n"


def _dot_label(text: str) -> str:
    """把换行写成 DOT 的 \\n，并转义引号和反斜杠。"""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return escaped.replace("\n", "\\n")


def _render_svg(dot_path: Path) -> Path | None:
    dot = shutil.which("dot")
    if not dot:
        return None
    svg_path = dot_path.with_suffix(".svg")
    result = subprocess.run(
        [dot, "-Tsvg", str(dot_path), "-o", str(svg_path)],
        capture_output=True, text=True, timeout=20,
    )
    if result.returncode != 0 or not svg_path.is_file():
        detail = (result.stderr or result.stdout or "dot 失败").strip()
        raise RuntimeError(f"生成语法树图片失败：{detail}")
    return svg_path
