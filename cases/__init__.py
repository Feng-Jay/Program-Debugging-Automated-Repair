"""案例包。测试请走命令，不要在这里找函数接口。

    python3 -m cases help
"""

from . import median, scheme, npd, oob, cutoff

ALL = {
    "median": median,
    "scheme": scheme,
    "npd": npd,
    "oob": oob,
    "cutoff": cutoff,
}
