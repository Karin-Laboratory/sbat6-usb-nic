#!/usr/bin/env python3
"""Reproduce the symbol CRC reference from the exact retained T6B Image."""
import hashlib
from pathlib import Path
import struct
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: extract-reference.py T6B-Image OUTPUT.symvers')
image = Path(sys.argv[1]).read_bytes()
expected = '92fb3e623cf620c4f4169a73e50bc7ba90aa3f86dc3b0d9da1d467de1dfad0fb'
if hashlib.sha256(image).hexdigest() != expected:
    raise SystemExit('Image hash mismatch; these table boundaries do not apply')
rows = []
for index, entry in enumerate(range(0xcdcbf0, 0xcfaa4c, 12)):
    name_offset = entry + 4 + struct.unpack_from('<i', image, entry + 4)[0]
    end = image.index(b'\0', name_offset)
    name = image[name_offset:end].decode('ascii')
    crc = struct.unpack_from('<I', image, 0xcfaa4c + 4 * index)[0]
    # Export category is normalized for GPL-licensed candidate modules;
    # this is not a reconstruction of the kernel's GPL/namespace policy.
    rows.append(f'0x{crc:08x}\t{name}\tvmlinux\tEXPORT_SYMBOL\t\n')
if len(rows) != 10205:
    raise SystemExit('wrong export count')
rows.sort(key=lambda row: row.split('\t')[1])
Path(sys.argv[2]).write_text(''.join(rows), encoding='ascii')
