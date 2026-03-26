"""二进制帧：TLS 之上的多路复用（控制 JSON + 数据流）。"""
from __future__ import annotations

import json
import struct
from enum import IntEnum
from typing import Any

MSG_CONTROL = 0
MSG_DATA = 1

HEADER_STRUCT = struct.Struct("!B I I")  # type, stream_id, payload_len


class FrameError(ValueError):
    pass


def pack_control(stream_id: int, obj: dict[str, Any]) -> bytes:
    raw = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    return HEADER_STRUCT.pack(MSG_CONTROL, stream_id, len(raw)) + raw


def pack_data(stream_id: int, chunk: bytes) -> bytes:
    return HEADER_STRUCT.pack(MSG_DATA, stream_id, len(chunk)) + chunk


def unpack_header(buf: bytes) -> tuple[int, int, int]:
    if len(buf) != HEADER_STRUCT.size:
        raise FrameError("header size")
    t, sid, ln = HEADER_STRUCT.unpack(buf)
    if ln > 512 * 1024:
        raise FrameError("payload too large")
    return t, sid, ln


def parse_control_payload(raw: bytes) -> dict[str, Any]:
    return json.loads(raw.decode("utf-8"))


class CtrlOp(IntEnum):
    OPEN = 1
    OPEN_OK = 2
    OPEN_ERR = 3
    CLOSE = 4
    CLOSE_REMOTE = 5
