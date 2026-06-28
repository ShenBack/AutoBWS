from __future__ import annotations

import asyncio

from net.http import new_async_session
from net.proxy import parse_proxy


async def send_telegram(token: str, chat_id: str, text: str, proxy: str | None = None) -> tuple[bool, str]:
    if not (token and chat_id):
        return False, "缺少 bot token 或 chat id"
    norm = parse_proxy(proxy) if proxy else None
    try:
        async with new_async_session("chrome131_android", proxy=norm) as s:
            r = await s.post(f"https://api.telegram.org/bot{token}/sendMessage",
                             data={"chat_id": chat_id, "text": text}, timeout=12)
        ok = bool(r.json().get("ok"))
        return ok, "" if ok else str(r.text)[:200]
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


async def send_webhook(url: str, payload: dict) -> tuple[bool, str]:
    if not url:
        return False, "缺少 webhook url"
    try:
        async with new_async_session("chrome131_android") as s:
            r = await s.post(url, json=payload, timeout=12)
        code = getattr(r, "status_code", 0)
        return 200 <= code < 300, f"HTTP {code}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _smtp_send(host, port, user, pwd, to, subject, body) -> None:
    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    port = int(port or 465)
    srv = smtplib.SMTP_SSL(host, port, timeout=12) if port == 465 else smtplib.SMTP(host, port, timeout=12)
    try:
        if port != 465:
            srv.starttls()
        srv.login(user, pwd)
        srv.sendmail(user, [to], msg.as_string())
    finally:
        try:
            srv.quit()
        except Exception:
            pass


async def send_smtp(host, port, user, pwd, to, subject, body) -> tuple[bool, str]:
    if not (host and user and to):
        return False, "SMTP 配置不全"
    try:
        await asyncio.to_thread(_smtp_send, host, port, user, pwd, to, subject, body)
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


async def notify_all(st: dict, title: str, body: str, kind: str = "win") -> None:
    tasks = []
    if st.get("tg_enabled"):
        tasks.append(send_telegram(st.get("tg_token", ""), st.get("tg_chat", ""), f"{title}\n{body}", st.get("tg_proxy") or None))
    if st.get("webhook_enabled"):
        tasks.append(send_webhook(st.get("webhook_url", ""), {"title": title, "body": body, "kind": kind}))
    if st.get("smtp_enabled"):
        tasks.append(send_smtp(st.get("smtp_host", ""), st.get("smtp_port", 465), st.get("smtp_user", ""),
                               st.get("smtp_pass", ""), st.get("smtp_to", ""), title, body))
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def test_channel(st: dict, kind: str) -> tuple[bool, str]:
    title, body = "AUTOBWS 测试通知", "收到这条说明通知配置正常"
    if kind == "telegram":
        return await send_telegram(st.get("tg_token", ""), st.get("tg_chat", ""), f"{title}\n{body}", st.get("tg_proxy") or None)
    if kind == "webhook":
        return await send_webhook(st.get("webhook_url", ""), {"title": title, "body": body, "kind": "test"})
    if kind == "smtp":
        return await send_smtp(st.get("smtp_host", ""), st.get("smtp_port", 465), st.get("smtp_user", ""),
                               st.get("smtp_pass", ""), st.get("smtp_to", ""), title, body)
    return False, "未知渠道"
