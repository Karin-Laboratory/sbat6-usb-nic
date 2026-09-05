# Offline build guide

Builds are permitted only for an explicitly hash-pinned source/config/toolchain
bundle. Run the direct-access inventory first:

```sh
python3 tools/t6a-direct-access-inventory.py --json path/to/u_ether.c path/to/f_ncm.c
```

An `UNKNOWN` field is a blocker. Header assertions alone do not satisfy the
final ELF gate; the resulting `.ko` machine code must be inspected separately.
