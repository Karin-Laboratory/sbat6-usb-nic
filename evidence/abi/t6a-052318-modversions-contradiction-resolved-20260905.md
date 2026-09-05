# 052318 MODVERSIONS contradiction — resolved

This is a read-only audit. No candidate was rebuilt, loaded, copied to T6A,
or used for a live test.

## Exact artifact

```text
ELF=/home/masataka/projects/sbat6-usb-nic/candidate/20260905-netdev-priv-final/source/usb_f_ncm.ko
SHA256=052318dea82970df24dfdb7a47942e79f99b35781f791c48d6bbb2ff7b2cdc1f
vermagic=5.4.238 SMP mod_unload modversions aarch64
```

The audit parsed the ELF `__versions` section directly. It contains 82
records, including:

```text
module_layout=0x3a3eb6e9
```

The authoritative vendor extended map is the recovered 84-record map whose
82 names overlap this ELF. All 82 overlapping CRCs match exactly. In
particular, the vendor map also gives `module_layout=0x3a3eb6e9`.

The retained `modcrc.tsv` is not the same evidence: all 82 names overlap, but
40 CRCs differ, including:

```text
module_layout: ELF 0x3a3eb6e9, saved modcrc.tsv 0x6006b85e
usb_assign_descriptors: ELF 0x11ebaf0f, saved modcrc.tsv 0x5079b8ae
register_netdev: ELF 0xe17e26a0, saved modcrc.tsv 0xaa9f4143
```

## Classification

```text
052318_MODVERSIONS_CONTRADICTION=RESOLVED
ROOT_CAUSE=stale or wrong-source modcrc.tsv; it does not describe the exact ELF/vendor CRC population
CASE_A=NO
CASE_B=YES
CASE_C=NOT_APPLICABLE_TO_THIS_CONTRADICTION
```

This resolves the contradiction only. It does not establish clean-build
reproducibility: the immutable source/config/compiler/output bundle needed to
recreate this exact ELF and its CRC records is still incomplete.

## Gate disposition

```text
MODVERSIONS_GATE=PASS_FOR_EXACT_ELF_AGAINST_VENDOR_MAP
MODULE_LAYOUT_GATE=PASS
VERMAGIC_GATE=PASS
LOADER_GATE_REPRODUCIBLE=NO
LIVE_TEST=FORBIDDEN
```

The reusable audit is
`tools/t6a-modversions-exact-audit.py`. It accepts the exact ELF, the
authoritative vendor map, and the saved map, and performs no writes.
