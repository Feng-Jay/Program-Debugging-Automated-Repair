"""IntroClass 中位数作业。测试命令：python3 -m cases test median cases/median/median.cpp"""

from pathlib import Path

BUG = "IntroClass median / 较小数被写错"
TASK = (
    "题目：求三个整数的中位数。\n"
    "先在前两个数里分出较大的和较小的，再用第三个数比较，得到不大不小的那个。\n"
    "例如 2 8 6 的中位数是 6；三个数相同，中位数就是这个数。"
)
WHY = "第一个数不大于第二个数时，学生把较小数也写成了第二个数（small = num2）。"
ORIGIN = "IntroClass，匿名提交 000。修复只把 small = num2 改成 small = num1。"

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "median.cpp"
FIXED = HERE / "median.fixed.cpp"


def _case(title: str, numbers: str, median: str) -> dict:
    return {
        "title": title,
        "stdin": numbers + "\n",
        "expect": f"{median} is the median",
    }


# 黑盒测试来自 IntroClass。2 8 6 和 6 8 2 会暴露这个错误。
TESTS = [
    _case("2 6 8，中间是 6", "2 6 8", "6"),
    _case("2 8 6，中间是 6", "2 8 6", "6"),
    _case("6 2 8，中间是 6", "6 2 8", "6"),
    _case("6 8 2，中间是 6", "6 8 2", "6"),
    _case("8 2 6，中间是 6", "8 2 6", "6"),
    _case("8 6 2，中间是 6", "8 6 2", "6"),
    _case("三个都是 9", "9 9 9", "9"),
]
