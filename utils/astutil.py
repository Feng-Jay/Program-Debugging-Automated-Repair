"""语法树。search、template、synth 都从这里找节点，再用 replace 改源码。

学生会用到的方法：
  functions         文件里的函数
  compare_ops       比较运算，例如 a > b
  identifier_uses   局部变量出现的位置
  if_statements     if，以及它有没有 else
  pointer_uses      p-> 和 *p
  statements        函数里的语句
  replace           按字节位置换成新文本，返回整份新源码

解析用 tree-sitter。这里不看案例名，也不运行测试。
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    import tree_sitter_cpp
    from tree_sitter import Language, Parser
except ImportError as exc:  # pragma: no cover - 环境缺依赖时给出明确说明
    raise ImportError(
        "缺少 tree-sitter。请先运行：python3 -m pip install -r requirements.txt"
    ) from exc

# 比较符会被 search / template / synth 换成同组里的另一个。
COMPARE_OPS = ("<", "<=", ">", ">=", "==", "!=")
# &&、|| 以及输入输出的 <<、>> 能在树上看到。当前的修复方法不替换它们。
LOGICAL_OPS = ("&&", "||")
STREAM_OPS = ("<<", ">>")

_LANGUAGE = Language(tree_sitter_cpp.language())
_PARSER = Parser(_LANGUAGE)

STMT_TYPES = frozenset({
    "expression_statement",
    "return_statement",
    "if_statement",
    "for_statement",
    "while_statement",
    "do_statement",
    "switch_statement",
    "break_statement",
    "continue_statement",
    "compound_statement",
})


@dataclass(frozen=True)
class NodeView:
    type: str
    start: int
    end: int
    text: str

    @property
    def span(self) -> tuple[int, int]:
        return self.start, self.end


@dataclass(frozen=True)
class BinaryOp(NodeView):
    operator: str
    operator_start: int
    operator_end: int


@dataclass(frozen=True)
class IdentifierUse(NodeView):
    name: str
    role: str  # assignment_rhs / condition / other


@dataclass(frozen=True)
class IfView(NodeView):
    has_else: bool
    condition: str
    consequence_start: int
    consequence_end: int


@dataclass(frozen=True)
class PointerUse(NodeView):
    pointer: str
    statement_start: int
    statement_end: int
    kind: str


class SourceTree:
    """一份 C++ 源码和它的语法树。replace 不改原文件，只返回新文本。"""

    def __init__(self, text: str):
        if isinstance(text, bytes):
            self.raw = text
            self.text = text.decode("utf-8")
        else:
            self.text = text
            self.raw = text.encode("utf-8")
        self.tree = _PARSER.parse(self.raw)
        # 解析出了错误也先留着。补丁对不对，后面交给编译和测试判断。

    def node_text(self, node) -> str:
        """节点对应的源码片段。"""
        return self.raw[node.start_byte:node.end_byte].decode("utf-8")

    def walk(self, node=None):
        node = self.tree.root_node if node is None else node
        yield node
        for child in node.children:
            yield from self.walk(child)

    def functions(self):
        """所有函数定义，包含 main。"""
        return [n for n in self.walk() if n.type == "function_definition"]

    def line_indent(self, byte_pos: int) -> str:
        """该字节所在行开头的空格或制表符，插入新代码时用来对齐。"""
        start = self.raw.rfind(b"\n", 0, byte_pos) + 1
        end = start
        while end < byte_pos and self.raw[end:end + 1] in (b" ", b"\t"):
            end += 1
        return self.raw[start:end].decode("utf-8")

    def replace(self, start: int, end: int, new: str) -> str:
        """把 [start, end) 这一段字节换成 new，返回整份新源码。"""
        return self.raw[:start].decode("utf-8") + new + self.raw[end:].decode("utf-8")

    def declared_names(self, function) -> list[str]:
        """函数里声明过的局部变量名，按出现顺序，不重复。"""
        names: list[str] = []
        seen: set[str] = set()
        for node in self.walk(function):
            if node.type != "declaration":
                continue
            for child in self.walk(node):
                if child.type == "identifier":
                    name = self.node_text(child)
                    if name not in seen:
                        seen.add(name)
                        names.append(name)
        return names

    def statements(self, function=None) -> list[NodeView]:
        """函数体里的语句。if / 循环里面的语句也会列出来。"""
        roots = [function] if function is not None else self.functions()
        result: list[NodeView] = []
        for root in roots:
            body = None
            for child in root.children:
                if child.type == "compound_statement":
                    body = child
                    break
            if body is None:
                continue
            result.extend(self._compound_statements(body))
        return result

    def _compound_statements(self, compound) -> list[NodeView]:
        result: list[NodeView] = []
        for child in compound.children:
            if child.type in {"{", "}", "comment"}:
                continue
            if child.type == "declaration":
                continue
            if child.type in STMT_TYPES or child.type.endswith("_statement"):
                result.append(NodeView(child.type, child.start_byte, child.end_byte, self.node_text(child)))
                if child.type == "if_statement":
                    for field in ("consequence", "alternative"):
                        part = _statement_body(child.child_by_field_name(field))
                        if part is None:
                            continue
                        if part.type == "compound_statement":
                            result.extend(self._compound_statements(part))
                        elif part.type == "if_statement":
                            # else if：外层已收录整个 if；内层语句在递归 if 时处理
                            result.extend(self._compound_statements_from_if(part))
                        elif part.type in STMT_TYPES or part.type.endswith("_statement"):
                            result.append(NodeView(part.type, part.start_byte, part.end_byte, self.node_text(part)))
                elif child.type in {"for_statement", "while_statement", "do_statement"}:
                    for part in child.children:
                        if part.type == "compound_statement":
                            result.extend(self._compound_statements(part))
        return result

    def _compound_statements_from_if(self, node) -> list[NodeView]:
        result = [NodeView(node.type, node.start_byte, node.end_byte, self.node_text(node))]
        for field in ("consequence", "alternative"):
            part = _statement_body(node.child_by_field_name(field))
            if part is None:
                continue
            if part.type == "compound_statement":
                result.extend(self._compound_statements(part))
            elif part.type == "if_statement":
                result.extend(self._compound_statements_from_if(part))
            elif part.type in STMT_TYPES or part.type.endswith("_statement"):
                result.append(NodeView(part.type, part.start_byte, part.end_byte, self.node_text(part)))
        return result

    def compare_ops(self, function=None) -> list[BinaryOp]:
        """< <= > >= == !=。operator_start / operator_end 标出运算符本身。"""
        return self._binary_ops(COMPARE_OPS, function)

    def logical_ops(self, function=None) -> list[BinaryOp]:
        """&& 和 ||。当前修复方法不用它们生成补丁。"""
        return self._binary_ops(LOGICAL_OPS, function)

    def _binary_ops(self, allowed: tuple[str, ...], function=None) -> list[BinaryOp]:
        roots = [function] if function is not None else [self.tree.root_node]
        found: list[BinaryOp] = []
        for root in roots:
            for node in self.walk(root):
                if node.type != "binary_expression":
                    continue
                op_node = next((c for c in node.children if not c.is_named), None)
                if op_node is None:
                    continue
                op = self.node_text(op_node)
                if op not in allowed:
                    continue
                found.append(BinaryOp(
                    type=node.type,
                    start=node.start_byte,
                    end=node.end_byte,
                    text=self.node_text(node),
                    operator=op,
                    operator_start=op_node.start_byte,
                    operator_end=op_node.end_byte,
                ))
        return found

    def identifier_uses(self, function) -> list[IdentifierUse]:
        """局部变量的使用处。role 是 assignment_rhs、condition 或 other。"""
        declared = set(self.declared_names(function))
        uses: list[IdentifierUse] = []
        for node in self.walk(function):
            if node.type != "identifier":
                continue
            if node.parent is not None and node.parent.type == "declaration":
                continue
            if node.parent is not None and node.parent.type in {"function_declarator", "qualified_identifier"}:
                continue
            name = self.node_text(node)
            if name not in declared:
                continue
            uses.append(IdentifierUse(
                type="identifier",
                start=node.start_byte,
                end=node.end_byte,
                text=name,
                name=name,
                role=_identifier_role(node),
            ))
        return uses

    def if_statements(self, function=None) -> list[IfView]:
        """每个 if。has_else 为假时，template 和 synth 可以补 else。"""
        roots = [function] if function is not None else [self.tree.root_node]
        found: list[IfView] = []
        for root in roots:
            for node in self.walk(root):
                if node.type != "if_statement":
                    continue
                alternative = node.child_by_field_name("alternative")
                consequence = node.child_by_field_name("consequence")
                condition = node.child_by_field_name("condition")
                found.append(IfView(
                    type="if_statement",
                    start=node.start_byte,
                    end=node.end_byte,
                    text=self.node_text(node),
                    has_else=alternative is not None,
                    condition=self.node_text(condition) if condition is not None else "",
                    consequence_start=consequence.start_byte if consequence is not None else node.start_byte,
                    consequence_end=consequence.end_byte if consequence is not None else node.end_byte,
                ))
        return found

    def pointer_uses(self, function=None) -> list[PointerUse]:
        """p->成员 和 *p。同一条语句里的同一个指针只记一次。"""
        roots = [function] if function is not None else [self.tree.root_node]
        found: list[PointerUse] = []
        seen_stmt: set[tuple[int, int, str]] = set()
        for root in roots:
            for node in self.walk(root):
                kind = None
                pointer = None
                if node.type == "field_expression":
                    op = next((self.node_text(c) for c in node.children if not c.is_named), "")
                    if op != "->":
                        continue
                    argument = node.child_by_field_name("argument")
                    if argument is None and node.named_children:
                        argument = node.named_children[0]
                    if argument is None:
                        continue
                    pointer = self.node_text(argument)
                    kind = "->"
                elif node.type == "pointer_expression":
                    op = next((self.node_text(c) for c in node.children if not c.is_named), "")
                    if op != "*":
                        continue
                    argument = node.named_children[0] if node.named_children else None
                    if argument is None:
                        continue
                    pointer = self.node_text(argument)
                    kind = "*"
                else:
                    continue
                stmt = _enclosing_statement(node)
                if stmt is None:
                    continue
                key = (stmt.start_byte, stmt.end_byte, pointer)
                if key in seen_stmt:
                    continue
                seen_stmt.add(key)
                found.append(PointerUse(
                    type=node.type,
                    start=node.start_byte,
                    end=node.end_byte,
                    text=self.node_text(node),
                    pointer=pointer,
                    statement_start=stmt.start_byte,
                    statement_end=stmt.end_byte,
                    kind=kind,
                ))
        return found



def _statement_body(node):
    """else 在语法树上常常多包一层 else_clause，语句本身在里面。"""
    if node is None:
        return None
    if node.type != "else_clause":
        return node
    named = [child for child in node.children if child.is_named]
    return named[0] if named else None


def _is_descendant(root, node) -> bool:
    current = node
    while current is not None:
        if current == root:
            return True
        current = current.parent
    return False


def _identifier_role(node) -> str:
    """判断变量名是在赋值右边、if 条件里，还是别的地方。"""
    current = node
    while current is not None and current.parent is not None:
        parent = current.parent
        if parent.type == "assignment_expression":
            named = parent.named_children
            if len(named) >= 2 and _is_descendant(named[1], node):
                return "assignment_rhs"
            return "other"
        if parent.type == "if_statement":
            condition = parent.child_by_field_name("condition")
            if condition is not None and _is_descendant(condition, node):
                return "condition"
        current = parent
    return "other"


def _enclosing_statement(node):
    current = node
    while current is not None:
        if current.type in STMT_TYPES and current.type != "compound_statement":
            return current
        current = current.parent
    return None


def parse(text: str) -> SourceTree:
    """读入一份源码并解析。等价于 SourceTree(text)。"""
    return SourceTree(text)


def line_number(tree: SourceTree, byte_pos: int) -> int:
    """字节位置对应的行号，从 1 开始。"""
    return tree.raw.count(b"\n", 0, byte_pos) + 1


def one_line(text: str, limit: int = 72) -> str:
    """把一段源码收成一行，太长就截断。日志和语法树图都用它。"""
    one = " ".join(text.split())
    if len(one) <= limit:
        return one
    return one[: limit - 1] + "…"


def function_name(tree: SourceTree, function) -> str:
    """函数定义节点上的名字，例如 main。"""
    declarator = function.child_by_field_name("declarator")
    target = declarator if declarator is not None else function
    for child in target.children:
        if child.type == "identifier":
            return tree.node_text(child)
    return "函数"


# identifier_uses 的 role 显示给学生时用中文。
ROLE_TEXT = {
    "assignment_rhs": "赋值右边",
    "condition": "条件里",
    "other": "这句里",
}


def unique_texts(candidates: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """同一份源码只留第一次出现的说明。"""
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for label, code in candidates:
        if code in seen:
            continue
        seen.add(code)
        result.append((label, code))
    return result
