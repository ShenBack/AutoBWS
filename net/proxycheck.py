from __future__ import annotations

import asyncio
import time

from net.http import new_async_session
from net.proxy import parse_proxy, proxy_label

TEST_URL = "https://api.bilibili.com/x/frontend/finger/spi"


async def test_one(raw: str, impersonate: str, *, timeout: float = 8.0) -> dict:
    norm = parse_proxy(raw)
    if not norm:
        return {"raw": raw, "norm": None, "ok": False, "latency_ms": None, "error": "格式无效"}
    t0 = time.monotonic()
    try:
        async with new_async_session(impersonate, proxy=norm) as s:
            r = await s.get(TEST_URL, timeout=timeout)
        ms = int((time.monotonic() - t0) * 1000)
        ok = getattr(r, "status_code", 0) == 200
        return {"raw": raw, "norm": norm, "ok": ok, "latency_ms": ms if ok else None,
                "error": "" if ok else f"HTTP {getattr(r, 'status_code', '?')}"}
    except Exception as e:
        return {"raw": raw, "norm": norm, "ok": False, "latency_ms": None, "error": type(e).__name__}


async def evaluate(raws: list[str], impersonate: str, *, timeout: float = 8.0,
                   concurrency: int = 40, on_progress=None) -> dict:
    raws = [r for r in (raws or []) if r and str(r).strip()]
    if not raws:
        return {"results": [], "ranked": [], "best": None}
    sem = asyncio.Semaphore(max(1, concurrency))
    total = len(raws)
    done = 0

    async def _bounded(r: str) -> dict:
        nonlocal done
        async with sem:
            res = await test_one(r, impersonate, timeout=timeout)
        done += 1
        if on_progress:
            try:
                on_progress(done, total, res)
            except Exception:
                pass
        return res

    results = await asyncio.gather(*[_bounded(r) for r in raws])
    working = [x for x in results if x["ok"] and x["latency_ms"] is not None]
    working.sort(key=lambda x: x["latency_ms"])
    ranked = [x["norm"] for x in working]
    return {"results": list(results), "ranked": ranked, "best": (ranked[0] if ranked else None)}


def fmt_result(x: dict) -> str:
    if x["ok"]:
        return f"{proxy_label(x['norm'])}  {x['latency_ms']}ms"
    return f"{proxy_label(x['norm']) if x['norm'] else x['raw']}  ✗ {x['error']}"
