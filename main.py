import argparse
import asyncio
import os
import sys
import threading
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    parser = argparse.ArgumentParser(description="AUTOBWS · bw乐园抢票助手")
    parser.add_argument("--port", type=int, default=8765, help="Web 端口(默认 8765)")
    parser.add_argument("--host", default="127.0.0.1", help="绑定地址(默认仅本机)")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--allow-lan", action="store_true", help="允许局域网访问(有账号泄露风险,默认仅本机)")
    parser.add_argument("--plain", action="store_true", help="纯文本无 GUI 模式")
    parser.add_argument("--profile", action="append", dest="profiles", metavar="NAME",
                        help="(无头)直接用指定配置抢,可多次")
    parser.add_argument("--list-profiles", action="store_true", help="列出配置后退出")
    parser.add_argument("--impersonate", default=None)
    parser.add_argument("--rebind", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.list_profiles:
        from core import profiles
        for n in profiles.list_profiles():
            p = profiles.load(n)
            print(f"{n}\t{p.uname}\t{len(p.sessions)}场次\t{'直连' if not p.proxies else f'{len(p.proxies)}代理'}")
        return

    if args.plain or args.profiles:
        from net.http import DEFAULT_IMPERSONATE
        if not args.impersonate:
            args.impersonate = DEFAULT_IMPERSONATE
        import cli
        try:
            asyncio.run(cli.run_headless(args))
        except KeyboardInterrupt:
            print("\n已中止。")
        return

    loopback = args.host in ("127.0.0.1", "localhost", "::1") or args.host.startswith("127.")
    if args.allow_lan:
        os.environ["AUTOBWS_ALLOW_LAN"] = "1"
    elif not loopback:
        print("[!] 绑定了非本机地址但未加 --allow-lan,非回环客户端会被拒绝(默认仅本机访问以保护账号)")
    import uvicorn
    url = f"http://{'127.0.0.1' if loopback else args.host}:{args.port}/"
    if not args.no_browser:
        def _open_when_ready():
            import time
            import urllib.request
            probe = f"http://127.0.0.1:{args.port}/"
            for _ in range(60):
                try:
                    urllib.request.urlopen(probe, timeout=0.4)
                    break
                except Exception:
                    time.sleep(0.2)
            webbrowser.open(url)
        threading.Thread(target=_open_when_ready, daemon=True).start()
    print(f"AUTOBWS Web GUI 已启动:{url}   (Ctrl+C 退出)")
    uvicorn.run("web.app:app", host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
