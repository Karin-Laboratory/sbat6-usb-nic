#!/usr/bin/env python3
"""Decode the fixed ARM64 Linux Image header without inferring a VA mapping."""
import argparse
import json
import struct
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    args = ap.parse_args()
    data = Path(args.image).read_bytes()[:64]
    if len(data) < 64:
        raise SystemExit("short Image header")
    code0, code1, text_offset, image_size, flags = struct.unpack_from("<IIQQQ", data, 0)
    result = {"code0": f"0x{code0:08x}", "code1": f"0x{code1:08x}",
              "text_offset": f"0x{text_offset:x}", "image_size": f"0x{image_size:x}",
              "flags": f"0x{flags:x}", "magic": data[56:60].decode("ascii", "replace"),
              "mapping_inference": "none"}
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
