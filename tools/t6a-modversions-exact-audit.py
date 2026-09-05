#!/usr/bin/env python3
"""Read-only exact ELF __versions audit for the T6A offline gate."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


def sections(blob: bytes):
    if blob[:4] != b"\x7fELF" or blob[4] != 2 or blob[5] != 1:
        raise ValueError("expected little-endian ELF64")
    _, _, _, _, _, _, shoff, _, _, _, _, shentsize, shnum, shstrndx = struct.unpack_from(
        "<16sHHIQQQIHHHHHH", blob, 0
    )
    raw = []
    for i in range(shnum):
        p = shoff + i * shentsize
        raw.append(struct.unpack_from("<IIQQQQIIQQ", blob, p))
    names = raw[shstrndx]
    strings = blob[names[4] : names[4] + names[5]]
    result = {}
    for s in raw:
        name_off, _, _, _, off, size, _, _, _, _ = s
        end = strings.find(b"\0", name_off)
        result[strings[name_off:end].decode()] = blob[off : off + size]
    return result


def versions(blob: bytes):
    data = sections(blob)["__versions"]
    if len(data) % 64:
        raise ValueError("unexpected __versions record size")
    result = {}
    for i in range(0, len(data), 64):
        crc = struct.unpack_from("<I", data, i)[0]
        name = data[i + 8 : i + 64].split(b"\0", 1)[0].decode()
        if name:
            result[name] = f"0x{crc:08x}"
    return result


def mapping(path: Path):
    result = {}
    for line in path.read_text().splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        if fields[0].startswith("0x"):
            result[fields[1]] = fields[0].lower()
        else:
            result[fields[0]] = fields[1].lower()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("elf", type=Path)
    ap.add_argument("--map", dest="vendor_map", type=Path, required=True)
    ap.add_argument("--saved-map", type=Path)
    args = ap.parse_args()
    elf = versions(args.elf.read_bytes())
    vendor = mapping(args.vendor_map)
    print(f"ELF={args.elf}")
    print(f"ELF_RECORDS={len(elf)}")
    print(f"ELF_MODULE_LAYOUT={elf.get('module_layout', 'MISSING')}")
    for label, other in (("VENDOR_MAP", vendor), ("SAVED_MAP", mapping(args.saved_map) if args.saved_map else {})):
        overlap = set(elf) & set(other)
        mismatches = sorted(name for name in overlap if elf[name] != other[name])
        missing = sorted(set(elf) - set(other))
        print(f"{label}_OVERLAP={len(overlap)}")
        print(f"{label}_MISMATCH_COUNT={len(mismatches)}")
        print(f"{label}_MISSING_COUNT={len(missing)}")
        for name in mismatches:
            print(f"{label}_MISMATCH={name}:{elf[name]}:{other[name]}")
    if args.saved_map:
        print("CASE_B=YES" if all(elf[n] == vendor.get(n) for n in elf) and any(elf[n] != mapping(args.saved_map).get(n) for n in elf) else "CASE_B=NO")


if __name__ == "__main__":
    main()
