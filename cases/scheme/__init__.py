"""ConDefects 里的 AtCoder ABC308 A。测试命令：

    python3 -m cases test scheme cases/scheme/abc308a.cpp
"""

from pathlib import Path

BUG = "ConDefects ABC308 A / 相等被当成下降"
TASK = (
    "题目：检查 8 个整数是不是一份合格方案。\n"
    "三条都满足才输出 Yes：从左到右可以相等但不能下降；"
    "每个数在 100 到 675 之间；每个数是 25 的倍数。"
)
WHY = "题面允许分数相等。这份提交写成了 >=，相等时会输出 No。"
ORIGIN = "ConDefects 提交 45931202，已译成 C++。官方三个样例都通过，相等的情况样例没覆盖。"

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "abc308a.cpp"
FIXED = HERE / "abc308a.fixed.cpp"


def _case(title: str, line: str, answer: str) -> dict:
    return {"title": title, "stdin": line + "\n", "expect": answer + "\n"}


# 前三条是比赛公开样例。第四条按题面补上：相邻可以相等。
TESTS = [
    _case("样例 1：严格递增，应当 Yes", "125 175 250 300 400 525 600 650", "Yes"),
    _case("样例 2：中间下降，应当 No", "100 250 300 400 325 575 625 675", "No"),
    _case("样例 3：超出范围，应当 No", "0 23 24 145 301 413 631 632", "No"),
    _case("125 出现两次，题面允许，应当 Yes", "125 125 250 300 400 525 600 650", "Yes"),
]

# 公开样例看不出这个错误。
FEW_TESTS = TESTS[:3]
