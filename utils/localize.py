"""读入故障定位的结果。修复方法只用它决定改哪些行。

文件里一行一个位置，越靠前越优先。行号后面可以写可疑度：

    12
    15 0.4

空行和以 # 开头的行会跳过。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from utils.astutil import line_number


@dataclass(frozen=True)
class Localization:
    """按可疑程度排好的行号。score 越大越优先；没写可疑度时，文件里越靠前越大。"""

    ranked: tuple[tuple[int, float], ...]

    @property
    def lines(self) -> set[int]:
        return {line for line, _ in self.ranked}

    def score(self, line: int) -> float:
        for number, value in self.ranked:
            if number == line:
                return value
        return 0.0

    def summary(self) -> str:
        parts = [f"第{line}行" for line, _ in self.ranked]
        return "、".join(parts)


def parse_localization(text: str) -> Localization:
    """把定位文件的文本解析成行号列表。没有行号时抛出 ValueError。"""
    found: list[int] = []
    explicit: dict[int, float] = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.replace(",", " ").split()
        if not parts[0].isdigit():
            raise ValueError(f"定位结果里有无法识别的行：{raw.strip()}")
        number = int(parts[0])
        if number < 1:
            raise ValueError(f"行号要从 1 开始：{raw.strip()}")
        score = None
        if len(parts) > 1:
            try:
                score = float(parts[1])
            except ValueError as exc:
                raise ValueError(f"可疑度不是数字：{raw.strip()}") from exc
        if len(parts) > 2:
            raise ValueError(f"定位结果一行只写行号和可选的可疑度：{raw.strip()}")
        if number not in found:
            found.append(number)
        if score is not None:
            explicit[number] = score
    if not found:
        raise ValueError("定位结果是空的")
    if explicit:
        ranked = tuple(sorted(((n, explicit.get(n, 0.0)) for n in found), key=lambda item: item[1], reverse=True))
    else:
        total = len(found)
        ranked = tuple((number, float(total - index)) for index, number in enumerate(found))
    return Localization(ranked)


def load_localization(path: Path) -> Localization:
    """从文件读取定位结果。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"读不到定位结果：{path}") from exc
    return parse_localization(text)


def _span(tree, start: int, end: int) -> range:
    first = line_number(tree, start)
    if end <= start:
        return range(first, first + 1)
    last = line_number(tree, end - 1)
    return range(first, last + 1)


def selected(loc: Localization | None, tree, start: int, end: int) -> bool:
    """没给定位结果时每一处都改；给了就只改落在这些行上的位置。"""
    if loc is None:
        return True
    return any(number in loc.lines for number in _span(tree, start, end))


def priority(loc: Localization | None, tree, start: int, end: int) -> float:
    """这个位置对应的最高可疑度。没给定位结果时都是 0，保持原来的生成顺序。"""
    if loc is None:
        return 0.0
    scores = [loc.score(number) for number in _span(tree, start, end) if number in loc.lines]
    return max(scores) if scores else 0.0
