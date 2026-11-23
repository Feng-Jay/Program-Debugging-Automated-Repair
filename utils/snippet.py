"""拼出要插入 C++ 源码的一小段代码。

template 的空指针检查和补 else，以及 synth 填“缺 else”这个洞，都用同一段格式：

    {
        std::cout << "...\\n";
        return 0;
    }

打印的文字来自该案例的测试期望，不是写死在某一道题里的答案。
"""

from __future__ import annotations


def _escape_cpp_string(text: str) -> str:
    """让一段普通文本能放进 C++ 双引号字符串。"""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return escaped.replace("\n", "\\n")


def guard_block(indent: str, message: str | None, return_code: str) -> str:
    """生成一段带花括号的代码：可选地打印 message，然后 return。

    indent 是插入位置原来的缩进。message 为 None 时只写 return。
    """
    inner = indent + "    "
    lines = [indent + "{\n"]
    if message is not None:
        lines.append(f'{inner}std::cout << "{_escape_cpp_string(message)}\\n";\n')
    lines.append(f"{inner}return {return_code};\n")
    lines.append(indent + "}")
    return "".join(lines)
