from __future__ import annotations

import sys
import time

_WEEK = ["一", "二", "三", "四", "五", "六", "日"]


def fmt_ts(sec) -> str:
    if not sec:
        return "—"
    t = time.localtime(int(sec))
    return time.strftime("%Y-%m-%d %H:%M:%S", t) + f" 周{_WEEK[t.tm_wday]}"


def fmt_duration(ms: int) -> str:
    s = max(0, ms) // 1000
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    parts = []
    if d: parts.append(f"{d}天")
    if h or d: parts.append(f"{h:02d}时")
    if m or h or d: parts.append(f"{m:02d}分")
    parts.append(f"{s:02d}秒")
    return "".join(parts)


def set_timer_resolution(enable: bool) -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        winmm = ctypes.WinDLL("winmm")
        (winmm.timeBeginPeriod if enable else winmm.timeEndPeriod)(1)
    except Exception:
        pass
