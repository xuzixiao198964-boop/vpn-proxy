"""
VPN 隧道服务端：TLS + 多路复用 TCP 转发。
监听默认 18443；SSH 22 仅运维，与本服务无关。
"""
from __future__ import annotations

import asyncio
import json
import logging
import ssl
import struct
from pathlib import Path
from typing import Any

# 包根目录：vpn-proxy-client
ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vpnproxy.auth_store import AuthStore
from vpnproxy.cert_util import ensure_server_cert
from vpnproxy.framing import (
    HEADER_STRUCT,
    MSG_CONTROL,
    MSG_DATA,
    parse_control_payload,
    unpack_header,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("tunnel-server")

DATA_DIR = ROOT / "server" / "data"
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 18443


async def _read_line(reader: asyncio.StreamReader) -> bytes:
    return await reader.readuntil(b"\n")


async def _handle_connection(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    auth: AuthStore,
) -> None:
    peer = writer.get_extra_info("peername")
    streams: dict[int, tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}
    outgoing_tasks: dict[int, asyncio.Task[None]] = {}

    try:
        raw = await _read_line(reader)
        msg = json.loads(raw.decode("utf-8"))
        if msg.get("cmd") != "login":
            raise ValueError("need login")
        user = str(msg.get("user", ""))
        pw = str(msg.get("pass", ""))
        if not auth.verify(user, pw):
            writer.write(json.dumps({"ok": False, "reason": "auth"}).encode("utf-8") + b"\n")
            await writer.drain()
            return
        writer.write(json.dumps({"ok": True}).encode("utf-8") + b"\n")
        await writer.drain()
        log.info("login ok user=%s peer=%s", user, peer)

        while True:
            header = await reader.readexactly(HEADER_STRUCT.size)
            msg_type, stream_id, length = unpack_header(header)
            payload = await reader.readexactly(length) if length else b""

            if msg_type == MSG_CONTROL:
                ctl = parse_control_payload(payload)
                op = int(ctl.get("op", 0))
                if op == 1:  # OPEN
                    sid = int(ctl["id"])
                    host = str(ctl["host"])
                    port = int(ctl["port"])
                    if sid in streams:
                        writer.write(
                            _ctl_pack(
                                {"op": 3, "id": sid, "msg": "exists"},
                            )
                        )
                        await writer.drain()
                        continue
                    try:
                        r2, w2 = await asyncio.wait_for(
                            asyncio.open_connection(host, port),
                            timeout=20.0,
                        )
                    except Exception as e:
                        log.warning("open %s:%s fail %s", host, port, e)
                        writer.write(
                            _ctl_pack({"op": 3, "id": sid, "msg": str(e)[:200]}),
                        )
                        await writer.drain()
                        continue
                    streams[sid] = (r2, w2)

                    async def pump_remote(s: int, rr: asyncio.StreamReader) -> None:
                        try:
                            while True:
                                chunk = await rr.read(65536)
                                if not chunk:
                                    break
                                writer.write(_data_pack(s, chunk))
                                await writer.drain()
                        finally:
                            ctl_w = _ctl_pack({"op": 5, "id": s})
                            try:
                                writer.write(ctl_w)
                                await writer.drain()
                            except Exception:
                                pass
                            pair = streams.pop(s, None)
                            if pair:
                                try:
                                    pair[1].close()
                                    await pair[1].wait_closed()
                                except Exception:
                                    pass
                            outgoing_tasks.pop(s, None)

                    outgoing_tasks[sid] = asyncio.create_task(pump_remote(sid, r2))
                    writer.write(_ctl_pack({"op": 2, "id": sid}))
                    await writer.drain()

                elif op == 4:  # CLOSE from client
                    sid = int(ctl["id"])
                    pair = streams.pop(sid, None)
                    t = outgoing_tasks.pop(sid, None)
                    if t and not t.done():
                        t.cancel()
                    if pair:
                        try:
                            pair[1].close()
                            await pair[1].wait_closed()
                        except Exception:
                            pass

            elif msg_type == MSG_DATA:
                pair = streams.get(stream_id)
                if not pair:
                    continue
                try:
                    pair[1].write(payload)
                    await pair[1].drain()
                except Exception:
                    pass

    except asyncio.IncompleteReadError:
        log.info("peer closed %s", peer)
    except Exception as e:
        log.warning("handler error %s: %s", peer, e)
    finally:
        for t in list(outgoing_tasks.values()):
            if not t.done():
                t.cancel()
        for sid, pair in list(streams.items()):
            try:
                pair[1].close()
                await pair[1].wait_closed()
            except Exception:
                pass
        streams.clear()
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


def _ctl_pack(obj: dict[str, Any]) -> bytes:
    raw = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    return struct.pack("!B I I", MSG_CONTROL, 0, len(raw)) + raw


def _data_pack(stream_id: int, chunk: bytes) -> bytes:
    return struct.pack("!B I I", MSG_DATA, stream_id, len(chunk)) + chunk


async def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cert, key = ensure_server_cert(DATA_DIR)
    auth = AuthStore(DATA_DIR / "users.db")

    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(cert, key)

    server = await asyncio.start_server(
        lambda r, w: _handle_connection(r, w, auth),
        LISTEN_HOST,
        LISTEN_PORT,
        ssl=ssl_ctx,
    )
    log.info("listening TLS %s:%s data=%s", LISTEN_HOST, LISTEN_PORT, DATA_DIR)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
