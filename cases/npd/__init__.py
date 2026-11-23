"""按名字查分数。测试命令：python3 -m cases test npd cases/npd/npd.cpp"""

from pathlib import Path

BUG = "空指针 / 名单里没有的名字"
TASK = (
    "题目：输入一个名字，查出名单里的分数。\n"
    "名单只有 alice 90、bob 80、cara 70。\n"
    "找到了输出“名字 分数”；没有这个人要输出“找不到”，不能去读空指针。"
)
WHY = "没找到时 found 仍是空指针。程序没有判断，直接读了 found->name。"
ORIGIN = "课堂例子。三个已知名字都能通过，名单里没有的名字会崩溃。"

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "npd.cpp"
FIXED = HERE / "npd.fixed.cpp"


def _case(title: str, name: str, expect: str) -> dict:
    return {"title": title, "stdin": name + "\n", "expect": expect}


TESTS = [
    _case("alice 在名单里", "alice", "alice 90"),
    _case("bob 在名单里", "bob", "bob 80"),
    _case("cara 在名单里", "cara", "cara 70"),
    _case("dave 不在名单里", "dave", "找不到"),
]

# 三个已知名字看不出空指针。
FEW_TESTS = TESTS[:-1]
