"""Generate the app's small disc icon without third-party libraries."""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path


SIZE = 256
OUT = Path(__file__).resolve().parents[1] / "assets" / "app.ico"


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


rows = []
for y in range(SIZE):
    row = bytearray(b"\x00")
    for x in range(SIZE):
        dx, dy = x - 127.5, y - 127.5
        r = math.hypot(dx, dy)
        outer = max(0, min(255, int((115 - r) * 255)))
        if r > 115:
            rgba = (0, 0, 0, 0)
        elif r < 28:
            hole = max(0, min(255, int((28 - r) * 255)))
            rgba = (250, 252, 253, min(outer, hole))
        elif r < 31 or r > 111:
            rgba = (32, 102, 132, outer)
        elif 47 < r < 50 or 86 < r < 88:
            rgba = (125, 178, 199, outer)
        else:
            shine = max(0, 1 - math.hypot(x - 75, y - 68) / 130)
            rgba = (int(169 + 40 * shine), int(205 + 31 * shine),
                    int(220 + 25 * shine), outer)
        row.extend(rgba)
    rows.append(bytes(row))

raw = b"".join(rows)
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 9))
       + chunk(b"IEND", b""))
header = struct.pack("<HHH", 0, 1, 1)
entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 22)
OUT.parent.mkdir(exist_ok=True)
OUT.write_bytes(header + entry + png)
print(OUT)
