# T6A piecewise layout and vendor lineage continuation — 2026-09-05

Offline/read-only continuation. Candidate build, module load, UDC bind, and
live testing remain forbidden.

## Current piecewise anchors

| field | generic offset | vendor offset | delta | evidence | confidence |
|---|---:|---:|---:|---|---|
| `netdev_ops` | `0x218` | `0x1f8` | `-0x20` | repeated vendor producer stores and confirmed consumer slot | high |
| `ethtool_ops` | `0x220` | `0x200` | `-0x20` | paired vendor producer stores | high |
| `dev_addr` | `0x2e8` | `0x318` | `+0x30` | vendor/candidate machine-code evidence | medium/high |
| `dev` | `0x4d0` | `0x510` | `+0x40` | vendor/candidate parent codegen evidence | medium |
| `netdev_priv` base | `0x880` | `0x8c0` | `+0x40` | repeated vendor derivations | high |

These anchors already disprove a single global shift. The interval between
`ethtool_ops` and `dev_addr` contains at least one transition; the interval
from `dev` to the private base is separately constrained.

## Next information-gain field

`addr_assign_type` is selected next. It is a byte-sized field written on more
than one recognizable MAC-selection path and lies between the callback-table
region and the hardware-address region. Two semantically matching vendor
stores, with their branch/data-flow context tied to the same `net_device *`,
can narrow the first transition more effectively than an isolated early field.

Required extraction is: multiple `strb` stores, controlling assigned/random MAC
branches, the nearby six-byte MAC access at `dev_addr`, and relevant helper
relocations. A lone immediate displacement is not sufficient evidence.

After that, `min_mtu` and `max_mtu` should be extracted as a paired 32-bit
signature. `name` and `stats` remain unknown; no guessed offset is promoted.

## Lineage status

Already supported by the retained vendor binary and source comparison:

```text
allocation / net_device setup       PARTIAL_PASS
callback installation               PASS for netdev_ops/ethtool_ops
register_netdev / cleanup           PASS at call/relocation level
NCM bind / ConfigFS lifecycle       PASS at broad call-path level
function instance lifecycle         PASS for existing ABI offsets
request allocation / queue path     PASS at broad binary level
```

Still required for `VENDOR_LINEAGE_RECONSTRUCTION=PASS`:

```text
exact vendor source or equivalent semantic reconstruction of field writes
addr_assign_type/min_mtu/max_mtu/name/stats offsets
complete eth_dev private member ownership and lifetime ordering
UDC bind/unbind and function-instance cleanup correspondence
refcount and failure-unwind equivalence
```

Safe compatibility reduction candidates are module-owned `stats`, naming
through allocation/API paths, and private `eth_dev` members. `netdev_ops`,
`ethtool_ops`, and `dev.parent` still require exact layout evidence; unsafe
magic-offset shims are not allowed.
