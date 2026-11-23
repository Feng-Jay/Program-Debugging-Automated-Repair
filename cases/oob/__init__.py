"""按下标查分数。测试命令：python3 -m cases test oob cases/oob/oob.cpp"""

from pathlib import Path

BUG = "数组越界 / 下标正好等于长度"
TASK = (
    "题目：输入一个下标，查出那一格的分数。\n"
    "表里有 4 格，下标从 0 开始：70、80、90、100。\n"
    "合法下标是 0 到 3。超出范围要输出“下标超出范围”。"
)
WHY = "表外面的判断写成了 index > 4。下标等于 4 时条件不成立，程序去读了 scores[4]。"
ORIGIN = "课堂例子。0、3、-1、5 都能通过，只有下标 4 会越界。"

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "oob.cpp"
FIXED = HERE / "oob.fixed.cpp"


def _case(title: str, index: str, expect: str) -> dict:
    return {"title": title, "stdin": index + "\n", "expect": expect}


TESTS = [
    _case("下标 0，第一格", "0", "70"),
    _case("下标 3，最后一格", "3", "100"),
    _case("下标 -1，小于 0", "-1", "下标超出范围"),
    _case("下标 5，大于 4", "5", "下标超出范围"),
    _case("下标 4，正好在表外面", "4", "下标超出范围"),
]

# 下标 4 才是漏掉的那一格。
FEW_TESTS = TESTS[:-1]
