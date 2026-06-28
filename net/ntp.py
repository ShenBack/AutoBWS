from __future__ import annotations

import asyncio
import struct
import time

_NTP_DELTA = 2208988800

DEFAULT_NTP_HOSTS = ["ntp.aliyun.com", "ntp1.aliyun.com", "cn.pool.ntp.org"]


async def query_ntp(host: str = "ntp.aliyun.com", port: int = 123,
                    timeout: float = 3.0) -> tuple[int, float]:
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()

    class _Proto(asyncio.DatagramProtocol):
        def datagram_received(self, data, addr):
            if not fut.done():
                fut.set_result(data)

        def error_received(self, exc):
            if not fut.done():
                fut.set_exception(exc)

    t0 = time.monotonic()
    transport, _ = await loop.create_datagram_endpoint(_Proto, remote_addr=(host, port))
    try:
        transport.sendto(b"\x1b" + 47 * b"\x00")
        data = await asyncio.wait_for(fut, timeout)
        t1 = time.monotonic()
    finally:
        transport.close()

    if len(data) < 48:
        raise ValueError("NTP 响应过短")
    secs, frac = struct.unpack("!II", data[40:48])
    server_ms = int((secs - _NTP_DELTA) * 1000 + (frac / 2**32) * 1000)
    return server_ms, (t0 + t1) / 2.0


async def query_ntp_any(hosts: list[str] | None = None,
                        timeout: float = 3.0) -> tuple[int, float] | None:
    for host in (hosts or DEFAULT_NTP_HOSTS):
        try:
            return await query_ntp(host, timeout=timeout)
        except Exception:
            continue
    return None
