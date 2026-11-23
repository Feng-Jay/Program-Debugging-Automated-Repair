"""分数线例子，用来检查修复方法能否泛化。测试命令：

    python3 -m cases test cutoff cases/cutoff/cutoff.cpp
"""

from pathlib import Path

BUG = "分数线 / 正好等于 60 被判不及格"
TASK = (
    "题目：输入一个整数分数。\n"
    "60 分及以上输出 pass，否则输出 fail。"
)
WHY = "判断写成了 score > 60。正好 60 分时会输出 fail。"
ORIGIN = "课堂泛化例子。方法实现不得按案例名特判。"

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "cutoff.cpp"
FIXED = HERE / "cutoff.fixed.cpp"


def _case(title: str, score: str, expect: str) -> dict:
    return {"title": title, "stdin": score + "\n", "expect": expect}


TESTS = [
    _case("80 分，应当 pass", "80", "pass"),
    _case("0 分，应当 fail", "0", "fail"),
    _case("59 分，应当 fail", "59", "fail"),
    _case("61 分，应当 pass", "61", "pass"),
    _case("60 分，应当 pass", "60", "pass"),
]

FEW_TESTS = TESTS[:-1]
