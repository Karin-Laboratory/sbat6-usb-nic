# T6A offline continuation status — 2026-09-05

Read-only continuation. No candidate build, promotion, module load, ConfigFS
operation, UDC bind, or live test was performed.

## Mechanical source of truth

The current generator was run against `evidence/manifests/t6a-abi-manifest-v2.json`:

```text
CANDIDATE_GATE_GENERATION=FAIL
DIRECT_ACCESS_FIELDS=8
UNKNOWN_VENDOR_OFFSET_COUNT=2
UNKNOWN_VENDOR_OFFSET=struct net_device::addr_assign_type/min_mtu/max_mtu/name/mtu/stats
UNKNOWN_VENDOR_OFFSET=struct eth_dev::net/gadget/lock/req_lock/rx_reqs/tx_reqs/rx_frames/tx_qlen/port_usb/qmult/header_len/host_mac/dev_mac/no_skb_reserve/wrap/unwrap/work/todo/zlp
```

The two original manifest rows were retained for provenance. Concrete field
records and decisions were added under `unknown_groups`; they do not silently
turn an unresolved required access into a pass.

## Unknown groups and decisions

### UNKNOWN_GROUP_1

`struct net_device`: `addr_assign_type`, `min_mtu`, `max_mtu`, `name`, `mtu`,
and `stats`.

| field | access | current TU | vendor | decision | evidence/status |
|---|---|---:|---:|---|---|
| `addr_assign_type` | write | `0x24f` | UNKNOWN | B | producer store absent; remove/isolate address-provenance write only through a verified helper/allocation design |
| `min_mtu` | write | `0x21c` | `0x22c` observed | B | paired vendor store visible in `gether_setup_name`; current candidate provenance/TU gate is not canonical |
| `max_mtu` | write | `0x220` | `0x230` observed | B | paired vendor store visible; preserve equivalent `ndo_change_mtu` semantics before eliminating |
| `name` | write | `0x000` | `0x000` | B | use verified allocation-time naming pattern/API; registration still requires a valid name |
| `mtu` | read | `0x218` generic | UNKNOWN | C | remove only if minimal path supplies an equivalent size source; otherwise exact offset evidence is required |
| `stats` | read/write | macro/per-cpu | UNKNOWN | B | move counters to module-owned storage and expose via `ndo_get_stats64`; not yet implemented/gated |

For each row, `CAN_PROVE_FROM_VENDOR_BINARY` is `yes` only where the vendor
instruction and semantics are visible. `addr_assign_type` remains `no`.

### UNKNOWN_GROUP_2

`struct eth_dev`: `net`, `gadget`, `lock`, `req_lock`, request lists and queue
state, callbacks, work state, MAC storage, and related private members.

Decision: **C for vendor-private ABI admission**. These members are owned by
the replacement and need not match a vendor-private layout. This does not
waive the candidate's own actual-TU and final-ELF gates. No vendor offset is
invented and no padding shim is permitted.

## Vendor producer anchors

The following are directly visible in the retained `vendor/usb_net.ko`
disassembly (`analysis/t6a-usb_net/disasm.txt`):

1. `gether_setup_name` / `gether_setup_name_default`: callback pointer pair
   stores at `net + 0x1f8` and `net + 0x200`; relocation-backed static callback
   addresses. Semantics: `netdev_ops` and `ethtool_ops`. Confidence: high.
2. The same setup functions: paired 32-bit MTU stores at `net + 0x22c` and
   `net + 0x230` (the retained source/binary lineage identifies these as
   `min_mtu` and `max_mtu`). Confidence: medium/high pending canonical TU
   reproduction.
3. `gether_setup_name` and `gether_setup_name_default`: six-byte MAC source
   accesses at private `eth_dev` offset `0xa7f`, reached from a proven private
   base `net + 0x8c0`; semantics: `dev_mac`. Confidence: high for vendor
   private codegen, not a `net_device` field proof.

`addr_assign_type` has no identified vendor producer store. The old probe value
`0x27f` remains rejected; no offset is promoted.

## Required piecewise map

```text
DIRECT_ACCESS_REQUIRED_REGION_1=callback installation: netdev_ops 0x1f8, ethtool_ops 0x200
DIRECT_ACCESS_REQUIRED_REGION_2=address/MTU setup: dev_addr 0x318; addr_assign_type unresolved; min_mtu/max_mtu observed 0x22c/0x230
DIRECT_ACCESS_REQUIRED_REGION_3=embedded device parent: dev 0x510
DIRECT_ACCESS_REQUIRED_REGION_4=candidate private base: netdev_priv 0x8c0; candidate-owned eth_dev members require self-layout audit
PIECEWISE_NET_DEVICE_MAP=INSUFFICIENT
```

The map is not sufficient for all direct accesses because the current
candidate has not eliminated `addr_assign_type`, `mtu`, and `stats`, and has
not produced a canonical source/TU/final-ELF set for the callback/MTU stores.

## VA/Image mapping decision

```text
VA_IMAGE_MAPPING_GLOBAL_BLOCKER=no
VA_MAPPING_REQUIRED_CLAIMS=active-kernel consumer opcode/dataflow at register_netdevice+0xb4; exact T6A instruction identity
VA_MAPPING_INDEPENDENT_CLAIMS=vendor usb_net producer offsets; candidate-owned eth_dev self-layout; loader CRC/vermagic/UND audit; source-manifest coverage; vendor lineage call/relocation evidence
REGISTER_NETDEVICE_B4_DATAFLOW=UNPROVEN
```

Thus VA mapping is demoted from a global blocker only for claims that can be
proved independently. It remains a hard blocker for the active-kernel
consumer claim and is not replaced by the vendor producer inference.

## Loader provenance

`LOADER_GATE_REPRODUCIBLE=PASS_FOR_REPRODUCED_SOURCE_CONFIG` remains
conditional. Canonical `PASS` requires one immutable bundle with matching
source SHA, exact header SHA, `.config`/autoconf SHA, `Module.symvers` SHA,
`KBUILD_EXTRA_SYMBOLS`, compiler command, linker command, preprocessed TU,
objects, `mod.c`, and final ELF. The retained `.cmd` files include temporary
tree paths and the prior forced compatibility defines, so they are not a
canonical match for a future candidate. No ambiguous promotion was made.

## Minimal candidate and readiness

The minimal surface is limited to callback slots, `dev_addr`, embedded
`dev.parent`, private base, function-instance callbacks, and the candidate's
own private `eth_dev` object. `addr_assign_type`, `mtu`, and `stats` remain
design obligations until eliminated and gated; MTU bounds remain obligations
until equivalent validation is proven.

```text
UNKNOWN_REQUIRED_FIELD_COUNT=nonzero
GATE_GENERATOR=FAIL
REPRO_BUILD_GATE=NOT_RUN_FOR_CANONICAL_CANDIDATE
LOADER_GATE_REPRODUCIBLE=CONDITIONAL
VENDOR_LINEAGE_RECONSTRUCTION=INCOMPLETE
MINIMAL_CANDIDATE_ABI_SURFACE=NOT_FULLY_PROVEN
RESET_STONE_2_READY=no
```

Next offline action is to make the field records authoritative in the
generator, then either implement and audit the safe eliminations or obtain
additional vendor producer evidence. No live action is justified.
