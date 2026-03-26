"""
Windows 本地 SOCKS5 代理 GUI：登录后监听 127.0.0.1:1080，流量经 TLS 隧道由 VPS 转发。
运行：在 vpn-proxy-client 目录执行  python -m windows_client.app_gui
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from windows_client.tunnel_client import TunnelSession, run_socks_with_tunnel

CONFIG_PATH = Path.home() / ".vpnproxy_client.json"
DEFAULT_CA = ROOT / "server" / "data" / "certs" / "server.crt"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vpnproxy-gui")


class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("VPN 代理隧道 — Windows 客户端")
        self.root.geometry("560x420")

        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._async_stop: asyncio.Event | None = None

        self._build()

    def _build(self) -> None:
        f = ttk.Frame(self.root, padding=8)
        f.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(f, text="服务端地址").grid(row=row, column=0, sticky=tk.W)
        self.host = tk.StringVar(value="127.0.0.1")
        ttk.Entry(f, textvariable=self.host, width=28).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(f, text="端口").grid(row=row, column=0, sticky=tk.W)
        self.port = tk.StringVar(value="18443")
        ttk.Entry(f, textvariable=self.port, width=8).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(f, text="用户名").grid(row=row, column=0, sticky=tk.W)
        self.user = tk.StringVar(value="demo")
        ttk.Entry(f, textvariable=self.user, width=20).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(f, text="密码").grid(row=row, column=0, sticky=tk.W)
        self.password = tk.StringVar()
        ttk.Entry(f, textvariable=self.password, show="*", width=20).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(f, text="CA 证书路径").grid(row=row, column=0, sticky=tk.W)
        self.ca = tk.StringVar(value=str(DEFAULT_CA))
        ttk.Entry(f, textvariable=self.ca, width=40).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(f, text="本地 SOCKS5").grid(row=row, column=0, sticky=tk.W)
        self.socks = tk.StringVar(value="127.0.0.1:1080")
        ttk.Entry(f, textvariable=self.socks, width=28).grid(row=row, column=1, sticky=tk.W)

        row += 1
        bf = ttk.Frame(f)
        bf.grid(row=row, column=0, columnspan=2, pady=8)
        self.btn_start = ttk.Button(bf, text="启动代理", command=self._on_start)
        self.btn_start.pack(side=tk.LEFT, padx=4)
        self.btn_stop = ttk.Button(bf, text="停止", command=self._on_stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=4)

        row += 1
        ttk.Label(f, text="日志").grid(row=row, column=0, sticky=tk.NW)
        self.log = scrolledtext.ScrolledText(f, height=12, state=tk.DISABLED)
        self.log.grid(row=row, column=1, sticky=tk.NSEW)
        f.columnconfigure(1, weight=1)
        f.rowconfigure(row, weight=1)

        self._load_config()

    def _append_log(self, s: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, s + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _log(self, s: str) -> None:
        self.root.after(0, lambda: self._append_log(s))

    def _load_config(self) -> None:
        if not CONFIG_PATH.exists():
            return
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            self.host.set(data.get("host", self.host.get()))
            self.port.set(str(data.get("port", self.port.get())))
            self.user.set(data.get("user", self.user.get()))
            if data.get("ca"):
                self.ca.set(data["ca"])
            if data.get("socks"):
                self.socks.set(data["socks"])
        except Exception:
            pass

    def _save_config(self) -> None:
        try:
            h, p = self.socks.get().rsplit(":", 1)
        except ValueError:
            h, p = "127.0.0.1", "1080"
        data = {
            "host": self.host.get().strip(),
            "port": int(self.port.get().strip() or "18443"),
            "user": self.user.get().strip(),
            "ca": self.ca.get().strip(),
            "socks": f"{h}:{p}",
        }
        CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _on_start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        ca = Path(self.ca.get().strip())
        if not ca.is_file():
            messagebox.showerror("错误", f"找不到 CA 证书：{ca}")
            return
        try:
            port = int(self.port.get().strip())
        except ValueError:
            messagebox.showerror("错误", "端口无效")
            return
        try:
            sh, sp = self.socks.get().strip().rsplit(":", 1)
            socks_port = int(sp)
        except ValueError:
            messagebox.showerror("错误", "本地 SOCKS 格式应为 127.0.0.1:1080")
            return

        self._save_config()

        def thread_main() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._async_stop = asyncio.Event()
            try:
                loop.run_until_complete(self._async_run(ca, port, sh, socks_port))
            finally:
                loop.close()
                self._loop = None
                self._async_stop = None

        self._thread = threading.Thread(target=thread_main, daemon=True)
        self._thread.start()
        self.btn_start.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self._log("正在连接…")

    async def _async_run(self, ca: Path, port: int, listen_host: str, socks_port: int) -> None:
        session = TunnelSession(
            self.host.get().strip(),
            port,
            ca,
            self.user.get().strip(),
            self.password.get(),
        )
        try:
            await session.connect()
        except Exception as e:
            self._log(f"连接失败: {e}")
            self._reset_ui()
            return
        self._log("隧道已建立，本地 SOCKS5 已启动。")

        assert self._async_stop is not None
        stop = self._async_stop

        async def runner() -> None:
            await run_socks_with_tunnel(
                listen_host,
                socks_port,
                session,
                on_log=lambda m: self._log(m),
            )

        task = asyncio.create_task(runner())
        await stop.wait()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await session.shutdown()
        self._log("已停止。")
        self._reset_ui()

    def _reset_ui(self) -> None:
        def _() -> None:
            self.btn_start.configure(state=tk.NORMAL)
            self.btn_stop.configure(state=tk.DISABLED)

        self.root.after(0, _)

    def _on_stop(self) -> None:
        if self._loop and self._async_stop and not self._async_stop.is_set():
            self._loop.call_soon_threadsafe(self._async_stop.set)
        self._log("正在停止…")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
