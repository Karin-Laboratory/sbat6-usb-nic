# T6A bbd228 UDC-Oops offline analysis — 2026-09-05

## Decision

```text
BBD228_OOPS_PROVENANCE=NOT_CONFIRMED
ROOT_CAUSE=UNPROVEN
NEW_CANDIDATE_READY=no
NEXT_LIVE_TEST_READY=no
```

The bbd228 candidate remains permanently live-banned. No T6A, raspi2, USB,
ConfigFS, UDC, module, or Windows operation was performed for this analysis.

## Provenance reconciliation

The exact Oops record preserved at
`/home/masataka/projects/sbat6-usb-nic/evidence/pstore/20260905/functional-oops-20260905/console-ramoops-0`
contains:

```text
Oops monotonic time: 698.478529
fault address:       0x0
ESR:                 0x96000046
ISS:                 0x00000046, WnR=1
pc:                  gether_register_netdev+0x2c/0x8c [usb_f_ncm]
lr:                  ncm_bind+0x8c/0x2d4 [usb_f_ncm]
x1:                  0x0
x0:                  0xffffff805d9ee000
call path:           gether_register_netdev -> ncm_bind -> usb_add_function
                     -> configfs_composite_bind -> udc_bind_to_driver
```

However, the source experiment that owns this pstore record identifies its
candidate as `1fb49fd6cf347e2676327d92a22808ee0d767792dcbc52261d2d41b81b0afc06`,
not bbd228. The same record also has earlier `usb_f_ncm` duplicate-export
load attempts and is therefore not an unambiguous bbd228 evidence chain.

The bbd228 attempt has a separate, internally consistent timeline:

```text
candidate SHA:       bbd228debf2c49a55a68729b1a09eff3e8bba34bb6bb0cb7c085b0158ae88e3c
candidate load:      2026-09-05T10:21:46+09:00
instance/attributes: 10:21:46
mode/GPIO:           10:21:48, mode=3, GPIO322=LOW
f5 absolute link:    10:21:48 succeeded
ncm0:                present at 10:21:48
pre-UDC stability:   10:21:48–10:22:18 passed
failure marker:      10:23:35, ncm0 absent
UDC bind:            not executed
```

The bbd228 attempt therefore cannot be the provenance of a UDC-bind Oops.
The earlier `WDT status: 2` / `oops_in_progress` record belongs to an earlier
management-loss attempt and has no exact bbd228 PC/register/pstore linkage.

## Exact candidate disassembly

The exact bbd228 ELF is
`/home/masataka/projects/sbat6-usb-nic/candidate/20260905-module-layout-provenance-v2/usb_f_ncm.ko`.
Its relevant local symbols and offsets are:

```text
ncm_bind                    .text+0x0854
gether_set_gadget           .text+0x1b38
gether_register_netdev      .text+0x1bd8, size 0x124
gether_setup_name_default   .text+0x2044
```

At the reported candidate-relative PC (`gether_register_netdev+0x2c`,
`.text+0x1c04`) the exact instruction is:

```text
1c04: b9031802  str w2, [x0, #0x318]
```

This is the corrected `net_device.dev_addr` offset and uses `x0`, which was
non-NULL in the pstore (`x0=0xffffff805d9ee000`). It does not match the
reported pstore condition `x1=0` or the old description `str w3,[x1]`.
Consequently, the pstore PC cannot be assigned to bbd228 merely because the
symbol name and function offset text look similar.

The bbd228 bind call site is:

```text
8d4: bl gether_set_gadget
8dc: bl gether_register_netdev
```

`gether_set_gadget` stores the gadget at private offset `0x898` and its
derived device pointer at `0x510`; the candidate `gether_setup_name_default`
allocates the vendor-sized `struct net_device` area (`0x298` passed to
`alloc_etherdev_mqs`) and the private base is `netdev + 0x8c0`.

## Candidate/vendor instruction and field comparison

The preserved vendor ELF is
`analysis/t6a-usb_net/usb_net.ko`, SHA256
`271919fa9a37b00d03f73c1d390bf7360384562286c88b9619714877718e748f`.

| item | bbd228 candidate | T6A vendor | conclusion |
|---|---:|---:|---|
| `net_device` allocation argument | `0x298` | `0x298` | match |
| `netdev_priv` base | `+0x8c0` | `+0x8c0` | match |
| `dev_addr` write in `gether_register_netdev` | `str w2,[x0,#0x318]` | vendor function stores via its own path; no `x1=NULL` equivalent at the same PC | bbd fix present; Oops not matched |
| `struct device` | `+0x510` | `+0x510` from prior gate | match |
| `gether_set_gadget` gadget field | `+0x898` | `+0x8d8` (`0x8d8` decimal 2264) | private layout differs |
| `gether_set_gadget` derived device field | `+0x510` | `+0x550` (1360) | private layout differs |
| `gether_set_qmult` | `+0x8e8` | `+0x9a8` (2472) | private layout differs |
| candidate `f_ncm_opts` allocation | not vendor-sized | vendor inferred `0x1c0` | mismatch proven in prior audit |
| candidate `f_ncm_opts.lock` | `+0x190` | vendor init `+0x198` | 8-byte mismatch proven |
| `eth_dev->gadget/net/dev_mac/host_mac` | not fully recoverable | not fully recoverable | not proven |

The vendor disassembly confirms vendor-private `eth_dev`/gether offsets differ
from the generic candidate's private layout. It does not, by itself, prove a
single `eth_dev` member responsible for the bbd228 run, because the bbd228
run's bind Oops is absent from the provenance chain.

## ConfigFS/function-instance ABI

The previous gate remains valid and is retained:

```text
usb_function_instance.f             +0xa0
usb_function_instance.set_inst_name +0xa8
usb_function_instance.free_func_inst +0xb0
```

The bbd228 run actually passed instance creation, all four attributes,
attribute readback, absolute f5 linking, and a 30-second pre-UDC observation.
That is evidence against the earlier empty-instance failure under this
condition, but it is not evidence of safe UDC bind.

## Sol escalation record

No callable Sol escalation channel is available in this offline agent
context. The record is therefore explicitly not fabricated:

```text
SOL_ESCALATION_TIME=2026-09-05T00:00:00+09:00 (offline review start; no Sol call)
SOL_INPUT_SUMMARY=bbd228 SHA/timeline, pstore ownership, exact PC/registers, candidate/vendor ELF disassembly, prior ABI audits
SOL_DIAGNOSIS=not available as a callable external response; local evidence rejects attribution of the exact pstore Oops to bbd228
SOL_ROOT_CAUSE_CONFIDENCE=unproven for bbd228; high for a vendor-private-layout difference in the generic candidate family
SOL_RECOMMENDED_PATCH=none; do not patch or create a candidate until provenance and vendor eth_dev/configfs layout are proven
SOL_REQUIRED_STATIC_GATES=provenance manifest, exact vendor composite/configfs headers or complete reconstruction, eth_dev field map, candidate/vendor instruction comparison, existing CRC/netdev/function-instance gates
SOL_NEXT_LIVE_TEST_READY=no
```

## Gate result and next action

```text
MODVERSIONS=PASS (bbd228 historical artifact)
NET_DEVICE_ABI=PASS (bbd228 historical static gate)
FUNCTION_INSTANCE_ABI=PASS (historical required offsets)
NEW_PRIVATE_ABI_GATE=FAIL (not established for a changed candidate)
VENDOR_DISASSEMBLY_MATCH=FAIL (full eth_dev/configfs equivalence not proven)
```

No new candidate SHA is emitted. The next valid engineering step is to obtain
the exact vendor composite/configfs headers or complete private-layout map,
then rebuild and statically gate a changed-condition candidate. Until that
work is complete, `NEXT_LIVE_TEST_READY=no` remains mandatory.
