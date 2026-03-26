"""本地联调：启动服务端子进程 + SOCKS5 访问公网 IP 检测页。"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    ca = ROOT / "server" / "data" / "certs" / "server.crt"
    if not ca.is_file():
        print("首次运行请先生成证书：python server/run.py 一次后 Ctrl+C")
        sys.exit(1)

    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "server" / "run.py")],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    if proc.poll() is not None:
        print("服务端进程已退出，代码:", proc.returncode)
        sys.exit(1)
    try:
        import asyncio

        from windows_client.tunnel_client import TunnelSession

        async def run() -> None:
            s = TunnelSession("127.0.0.1", 18443, ca, "demo", "demo123")
            await s.connect()
            from windows_client.tunnel_client import run_socks_with_tunnel

            task = asyncio.create_task(
                run_socks_with_tunnel("127.0.0.1", 11080, s, on_log=None)
            )
            await asyncio.sleep(0.8)
            proxies = {"http": "socks5h://127.0.0.1:11080", "https": "socks5h://127.0.0.1:11080"}
            # 禁止在 asyncio 线程里同步 requests，否则会卡住 SOCKS 协程
            r = await asyncio.to_thread(
                lambda: requests.get(
                    "http://httpbin.org/ip",
                    proxies=proxies,
                    timeout=20,
                )
            )
            print("httpbin:", r.text[:200])
            r.raise_for_status()
            print("VERIFY_OK")
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            await s.shutdown()
        asyncio.run(run())
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
