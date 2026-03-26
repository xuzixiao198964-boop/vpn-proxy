"""TLS 隧道客户端：登录 + 多路复用。"""
from __future__ import annotations

import asyncio
import json
import logging
import ssl
import struct
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vpnproxy.framing import (
    HEADER_STRUCT,
    MSG_CONTROL,
    MSG_DATA,
    pack_control,
    pack_data,
    parse_control_payload,
    unpack_header,
)

log = logging.getLogger("tunnel-client")


class TunnelSession:
    def __init__(
        self,
        host: str,
        port: int,
        ca_file: Path,
        user: str,
        password: str,
    ) -> None:
        self.host = host
        self.port = port
        self.ca_file = ca_file
        self.user = user
        self.password = password
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._streams: dict[int, asyncio.Queue[bytes | None]] = {}
        self._open_wait: dict[int, asyncio.Future[bool]] = {}
        self._read_task: asyncio.Task[None] | None = None
        self._closed = False

    async def connect(self) -> None:
        ctx = ssl.create_default_context(cafile=str(self.ca_file))
        self._reader, self._writer = await asyncio.open_connection(
            self.host,
            self.port,
            ssl=ctx,
            ssl_handshake_timeout=20.0,
        )
        line = json.dumps(
            {"cmd": "login", "user": self.user, "pass": self.password},
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        assert self._writer is not None
        self._writer.write(line)
        await self._writer.drain()
        resp_raw = await self._reader.readuntil(b"\n")
        resp = json.loads(resp_raw.decode("utf-8"))
        if not resp.get("ok"):
            raise RuntimeError("登录失败：用户名或密码错误")
        self._read_task = asyncio.create_task(self._read_loop())
        log.info("tunnel connected")

    async def _read_loop(self) -> None:
        assert self._reader is not None
        try:
            while True:
                header = await self._reader.readexactly(HEADER_STRUCT.size)
                msg_type, stream_id, length = unpack_header(header)
                payload = await self._reader.readexactly(length) if length else b""
                if msg_type == MSG_CONTROL:
                    ctl = parse_control_payload(payload)
                    op = int(ctl.get("op", 0))
                    sid = int(ctl.get("id", 0))
                    if op == 2:  # OPEN_OK
                        fut = self._open_wait.pop(sid, None)
                        if fut and not fut.done():
                            fut.set_result(True)
                    elif op == 3:  # OPEN_ERR
                        fut = self._open_wait.pop(sid, None)
                        if fut and not fut.done():
                            fut.set_exception(RuntimeError(ctl.get("msg", "open failed")))
                    elif op == 5:  # CLOSE_REMOTE
                        q = self._streams.get(sid)
                        if q:
                            await q.put(None)
                elif msg_type == MSG_DATA:
                    q = self._streams.get(stream_id)
                    if q:
                        await q.put(payload)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning("read loop end: %s", e)
        finally:
            self._closed = True
            for q in self._streams.values():
                await q.put(None)
            for f in self._open_wait.values():
                if not f.done():
                    f.set_exception(ConnectionError("tunnel closed"))
            self._open_wait.clear()

    async def open_stream(self, host: str, port: int) -> tuple[int, asyncio.Queue[bytes | None]]:
        sid = self._next_id()
        q: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._streams[sid] = q
        fut: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
        self._open_wait[sid] = fut
        assert self._writer is not None
        self._writer.write(
            pack_control(
                0,
                {"op": 1, "id": sid, "host": host, "port": port},
            )
        )
        await self._writer.drain()
        try:
            await asyncio.wait_for(fut, timeout=30.0)
        except Exception:
            self._streams.pop(sid, None)
            self._open_wait.pop(sid, None)
            raise
        return sid, q

    def _next_id(self) -> int:
        import random

        import secrets

        while True:
            x = secrets.randbelow(2**31 - 2) + 1
            if x not in self._streams:
                return x

    async def send_data(self, stream_id: int, data: bytes) -> None:
        if self._closed or not self._writer:
            return
        self._writer.write(pack_data(stream_id, data))
        await self._writer.drain()

    async def close_stream(self, stream_id: int) -> None:
        self._streams.pop(stream_id, None)
        if not self._writer:
            return
        self._writer.write(
            pack_control(0, {"op": 4, "id": stream_id}),
        )
        await self._writer.drain()

    async def shutdown(self) -> None:
        self._closed = True
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        self._writer = None
        self._reader = None


async def run_socks_with_tunnel(
    listen_host: str,
    listen_port: int,
    session: TunnelSession,
    on_log: Callable[[str], None] | None = None,
) -> None:
    async def handle_socks(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            ver = await reader.readexactly(1)
            if ver != b"\x05":
                return
            nmeth = (await reader.readexactly(1))[0]
            await reader.readexactly(nmeth)
            writer.write(b"\x05\x00")
            await writer.drain()
            req = await reader.readexactly(4)
            if req[0] != 5 or req[1] != 1:
                return
            atyp = req[3]
            if atyp == 1:
                host = ".".join(str(b) for b in await reader.readexactly(4))
            elif atyp == 3:
                ln = (await reader.readexactly(1))[0]
                host = (await reader.readexactly(ln)).decode("utf-8")
            elif atyp == 4:
                await reader.readexactly(16)
                writer.write(b"\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00")
                await writer.drain()
                return
            else:
                return
            port = struct.unpack("!H", await reader.readexactly(2))[0]
            try:
                sid, q_in = await session.open_stream(host, port)
            except Exception as e:
                writer.write(b"\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00")
                await writer.drain()
                if on_log:
                    on_log(f"转发失败: {e}")
                return
            writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
            await writer.drain()

            async def pump_up() -> None:
                try:
                    while True:
                        chunk = await reader.read(65536)
                        if not chunk:
                            break
                        await session.send_data(sid, chunk)
                finally:
                    await session.close_stream(sid)

            async def pump_down() -> None:
                try:
                    while True:
                        item = await q_in.get()
                        if item is None:
                            break
                        writer.write(item)
                        await writer.drain()
                finally:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except Exception:
                        pass

            await asyncio.gather(pump_up(), pump_down())
        except Exception as e:
            if on_log:
                on_log(f"SOCKS 连接异常: {e}")
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    srv = await asyncio.start_server(handle_socks, listen_host, listen_port)
    async with srv:
        await srv.serve_forever()
