#!/usr/bin/env python3
"""Summarize vendor __this_module ELF sections without modifying inputs.

This reports aggregate facts only. It requires pyelftools and accepts a
directory containing vendor .ko files.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from elftools.elf.elffile import ELFFile


def inspect(path: Path) -> tuple[int, int | None, str | None]:
    try:
        with path.open("rb") as stream:
            elf = ELFFile(stream)
            section = elf.get_section_by_name(".gnu.linkonce.this_module")
            if section is None:
                return 0, None, "missing_section"
            size = section["sh_size"]
            symbol_size = None
            for table in (elf.get_section_by_name(".symtab"),
                          elf.get_section_by_name(".dynsym")):
                if table is None:
                    continue
                for symbol in table.iter_symbols():
                    if symbol.name == "__this_module":
                        symbol_size = symbol["st_size"]
                        break
                if symbol_size is not None:
                    break
            error = None if symbol_size == size else "symbol_section_size_mismatch"
            return 1, size, error
    except Exception as exc:  # malformed vendor artifacts are data, not fatal
        return 0, None, type(exc).__name__


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    args = parser.parse_args()
    valid = Counter()
    invalid = Counter()
    scanned = 0
    for path in sorted(args.corpus.rglob("*.ko")):
        scanned += 1
        ok, size, error = inspect(path)
        if ok and error is None:
            valid[size] += 1
        else:
            invalid[error or "invalid"] += 1
    print(f"VENDOR_MODULE_CORPUS_SCANNED={scanned}")
    print(f"VENDOR_THIS_MODULE_VALID={sum(valid.values())}")
    print(f"VENDOR_THIS_MODULE_SIZE_COUNTS={dict(sorted(valid.items()))}")
    print(f"VENDOR_THIS_MODULE_INVALID={dict(sorted(invalid.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
