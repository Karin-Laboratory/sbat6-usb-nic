# CRC reproduction status (2026-09-05)

## Authoritative baseline

The authoritative baseline is the 2026-09-04 candidate:

```text
SHA256 d2257ff360fa82c6f2ea639a9856ebd5db7e018b1e71c1113eb74e48ffe7e783
```

Its ELF `__versions` was parsed directly. Critical values are:

```text
module_layout                    0x3a3eb6e9
usb_put_function_instance        0x894defe7
config_group_init_type_name      0x875b9ac1
usb_function_register            0x6571549d
usb_function_unregister          0x50fcff8a
usb_os_desc_prepare_interf_dir   0xfc7b3f68
```

All 74 ELF imports match `candidate/20260904/abi/vendor-kimage.Module.symvers`.

## Reproduction gate

The existing output at
`./tmp-kernel-out.yf9KMT` was checked first.
Its `Module.symvers` SHA256 is:

```text
52eab42809a1ba81b0e1b085415f055b01840bff3d209fccf19d0a43c14044fb
```

It produces `module_layout=0x6006b85e` and
`usb_put_function_instance=0x3d61e770`, so it fails the required equality gate.
The same-O= compatibility rebuild was consequently skipped.

The 2026-09-05 compatibility artifact remains:

```text
SHA256 237b2532b0cd41ca243a0eab03d431fba9e895ecd1892262475b1af1bca7346a
static gate RESULT=FAIL
```

Its structural ABI checks pass, but its required CRC checks fail. The artifact
must not be loaded into T6A.

## Reproducible next input

The next valid offline build requires all of the following as preserved inputs:

1. the exact vendor-kimage `Module.symvers` map, not the upstream-style map
   currently in the old O= directory;
2. the exact generated headers and `.config` from the matching kernel output;
3. the telemetry `Module.symvers` as an additional external-symbol input;
4. an isolated output directory or a byte-for-byte backup/restore protocol so
   the vendor map is not confused with the kernel tree's ordinary map.

CRC hand-patching and ELF binary patching are not part of this plan.

## Safety status

No copy to T6A, `insmod`, ConfigFS, UDC, reboot, or other runtime operation was
performed. Hardware deployment remains prohibited until the complete static
gate reports `RESULT=PASS`.
