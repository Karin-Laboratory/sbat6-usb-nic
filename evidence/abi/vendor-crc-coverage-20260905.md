# Vendor CRC coverage investigation (2026-09-05)

## Decision

```text
BLOCKER=VENDOR_CRC_MAP_INCOMPLETE
RESULT=FAIL
LIVE_MINIMAL_TEST_READY=no
```

T6A was not modified. No module load, ConfigFS, UDC, reboot, or ADB
operation was performed.

## Current map provenance

`candidate/20260904/abi/vendor-kimage.Module.symvers` is a 74-line map. Its
kernel side has 67 entries and its telemetry side has 7 entries. The map was
introduced by commit `1bac781` without a generation script, full-kernel log,
or complete kernel-image export inventory. Its README describes it as a
vendor-kernel-image map, but the retained evidence contains only the symbols
needed by the then-current candidate. No evidence establishes that it is a
complete kernel export map; it is therefore classified as a partial map.

The saved vendor binary is `candidate/20260904/vendor/usb_net.ko` (SHA256
`271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f`). It is a
relocatable provider module and contains vendor-private implementation CRCs,
but no CRC entries for the ten missing kernel exports. No matching complete
vendor `vmlinux`, `/proc/kallsyms` capture, or full vendor `Module.symvers` was
found in the saved workspace.

## T6A read-only SSH attempt

The documented management path was used: agent host -> `raspi2` ->
`T6A-MGMT-IP`. From raspi2, read-only SSH attempts to T6A ports 22 and 2222
timed out for both `root` and `codex`. No WebUI/RCE fallback was used because
the requested management path was LAN/SSH only.

Requested `/proc/kallsyms` query:

```sh
grep -E '__crc_(hrtimer_init|kmem_cache_alloc|usb_assign_descriptors|usb_ep_)' /proc/kallsyms
```

Status: unavailable; SSH did not reach a shell.

## Offline candidates rejected

The only saved `vmlinux` files are byte-identical 5.4.238 upstream-style
outputs, timestamped 2026-08-25. Their `Module.symvers` provenance is the
old O= output, whose known values include `module_layout=0x6006b85e`, while
the authoritative vendor map requires `module_layout=0x3a3eb6e9`. They are
not the T6A vendor image and cannot supply vendor CRCs.

For audit completeness, the following values were visible as `__crc_*` ABS
symbols in that rejected upstream-style `vmlinux`; they were **not** added to
any map and have confidence `REJECTED / wrong provenance`:

| symbol | observed value | source | confidence |
|---|---:|---|---|
| hrtimer_init | 0x1ee7d3cd | saved upstream-style vmlinux | rejected |
| kmem_cache_alloc | 0x1aa829bc | saved upstream-style vmlinux | rejected |
| usb_assign_descriptors | 0x5079b8ae | saved upstream-style vmlinux | rejected |
| usb_ep_alloc_request | 0xa0e62d4b | saved upstream-style vmlinux | rejected |
| usb_ep_dequeue | 0xc8ea074a | saved upstream-style vmlinux | rejected |
| usb_ep_disable | 0xc41263c7 | saved upstream-style vmlinux | rejected |
| usb_ep_enable | 0x6bfad17f | saved upstream-style vmlinux | rejected |
| usb_ep_free_request | 0xa36ea15e | saved upstream-style vmlinux | rejected |
| usb_ep_queue | 0x0ffaa944 | saved upstream-style vmlinux | rejected |
| usb_ep_set_halt | 0x40f79de7 | saved upstream-style vmlinux | rejected |

Thus all ten vendor CRC values remain unavailable. No CRC was guessed,
borrowed from upstream, or patched into an ELF.

## Build gate

No extended map was created and no rebuild was run because the ten values were
not all obtained from an admissible vendor source. The previous diagnostic
artifact remains audit-only:

```text
kernel CRC coverage = 64/74
telemetry CRC = 7/7
module_layout = 0x3a3eb6e9
structural ABI = PASS
vermagic = PASS
static gate RESULT = FAIL
```

