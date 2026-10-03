# T6B / SBA6D RTL8156 (r8152): canonical compatibility build and Stage C success

Status date: 2026-10-04.

This directory records the second USB host NIC driver successfully brought up on the
test T6B/SBA6D vendor Linux 5.4.238 kernel after the AX88179 work.

Target hardware and driver:

- target: SoftBank Air Terminal 6 / SBA6D test unit
- kernel: Linux 5.4.238, ARM64
- NIC: Realtek RTL8156, USB ID `0bda:8156`
- source: `wget/realtek-r8152-linux`
- source commit: `9ff8b9d961f3927a211a25b187c749daf0769318`
- driver version: v2.21.4

The current verified result is **Stage C PASS**:

- r8152 loads,
- RTL8156 enumerates and automatically binds,
- a netdev is created,
- the MAC address is read correctly,
- `ip link set dev eth2 up` succeeds,
- the interface remains stable in UP/NO-CARRIER state,
- no r8152-related WARN/Oops/panic occurred in the captured interval,
- the previously reproducible `__rtl8152_set_mac_address` crash no longer occurs.

The physical Ethernet link was not connected during Stage C, so carrier, negotiated
speed, packet transfer, DHCP, ICMP and throughput are still untested for this exact build.

## Successful runtime evidence

### Stage B

Observed runtime state:

- USB device `0bda:8156` remained stably enumerated.
- USB interface `2-1.1.4:1.0` automatically bound to `r8152`.
- netdev `eth2` was created.
- MAC address: `80:3f:5d:f6:8f:20`.
- 25 checks over about 25 seconds all succeeded.
- boot_id stayed unchanged.
- no Oops or panic occurred.
- no network configuration, reboot or persistent change was made.

### Stage C

The interface was then opened without assigning an IP address.

Observed result:

- `ip link set dev eth2 up`: PASS
- final state: `NO-CARRIER,BROADCAST,MULTICAST,UP`
- carrier: 0 because no physical Ethernet link was present
- RX packets: 0
- TX packets: 0
- boot_id unchanged
- no r8152-related WARN
- no Oops/panic
- management ping and SSH stayed healthy for about 42 seconds
- no IP address, route, bridge membership or persistent network setting was added

This demonstrates successful module load, USB probe/bind, MAC setup, netdev creation and
interface-open execution. It does not yet demonstrate the data path.

## Why the first r8152 build crashed

The first external r8152 build looked correct by ordinary module metadata:

- vermagic matched,
- `module_layout` CRC matched,
- imported symbol CRCs matched 127/127,
- the RTL8156 `0bda:8156` alias was present,
- `insmod` returned success.

Nevertheless, bind caused an Oops and reboot.

pstore identified the useful fault site as:

`__rtl8152_set_mac_address+0x9c`

The old module disassembly used:

```text
ldr x0, [x21,#0x2e8]
```

That artifact therefore treated `netdev->dev_addr` as offset `0x2e8`.

Independent vendor-kernel evidence established the SBA6D value as `0x318`.
The crash was therefore a direct structure-layout mismatch: an upstream-layout inline
field access was compiled into a module running against the vendor-layout
`struct net_device`.

The key lesson is that **matching MODVERSIONS CRCs do not prove inline structure accesses
are correct**. A compiler can embed a wrong field offset directly in the module while all
imported symbol CRCs still match.

## Why the investigation became difficult

The target reports Linux 5.4.238, but its compile-time ABI is not reproduced by simply
taking pristine 5.4.238 and normalizing the saved configuration through upstream Kconfig.

Two independent layout problems appeared.

### struct net_device

The AX88179 work had already recovered the compatibility model needed here:

- preserve `CONFIG_WIRELESS_EXT`,
- preserve the recovered 32-byte opaque compatibility region immediately before
  `dev_addr`,
- do not assign invented vendor semantics to that region.

Important anchors used during the r8152 work include:

| field/base | target offset/value |
|---|---:|
| state | 0x48 |
| features | 0x0d0 |
| hw_features | 0x0d8 |
| vlan_features | 0x0e8 |
| stats | 0x110 |
| netdev_ops | 0x1f8 |
| ethtool_ops | 0x200 |
| flags | 0x208 in vendor-ELF analysis; retained as a special revalidation point |
| mtu | 0x228 |
| addr_len | 0x27f |
| dev_addr | 0x318 |
| _tx | 0x3c0 |
| tx_global_lock | 0x45c |
| watchdog_timeo | 0x460 |
| embedded dev | 0x510 |
| dev.parent effective | 0x550 |
| netdev_priv base | 0x8c0 |
| TX queue stride | 0x140 |
| TX queue state | +0x90 |

These anchors do not all have equal evidence strength. Final ELF code generation remains
the deciding evidence for each driver-specific path.

### struct module

Vendor modules consistently showed:

- `.gnu.linkonce.this_module` size `0x340`
- init location `0x150`
- cleanup location `0x328`

A naive pristine 5.4.238 build produced `0x280` instead.

The investigation temporarily explored normal Kconfig closures, HW_NAT and Android common
KABI because some combinations could also produce a 0x340-sized structure. Those paths
were useful controls, but they were not the practical solution for this target.

The already-working AX88179 recipe contained the answer: vendor compile macros that
upstream Kconfig normalization drops must still be present during compilation.

The working environment preserves:

- TRACEPOINTS
- TRACING
- EVENT_TRACING
- MODULES_TREE_LOOKUP

through **KCFLAGS applied to all compilation, including generated `.mod.c`**.

Using only `ccflags-y` is not equivalent. Earlier compatibility work left cleanup at
`0x258`; the working environment produces the vendor-compatible `0x328`.

## Why the final build worked

The decisive strategy change was to stop trying to reconstruct the SBA6D ABI from zero.

The AX88179 recipe in `driver/t6b-ax88179/` was already a hardware-tested compatibility
environment. The r8152 work reused that environment as canonical and added only
driver-specific source/build logic and ABI checks.

The successful method was:

1. keep the AX88179 kernel config, header compatibility patch, Image-derived symbol map
   and global KCFLAGS behavior unchanged,
2. add the RTL8156-capable r8152 source and build integration,
3. audit the additional ABI surface directly touched by r8152,
4. inspect final code generation for the old crash path and critical inline helpers,
5. use the dedicated test SBA6D as an oracle and advance through short runtime stages.

That was more effective than demanding a complete vendor-structure proof before every
load.

## CRC evidence

Live/kernel evidence also showed why CRC mismatch was no longer the primary blocker:

- vendor `module_layout`: `0x3a3eb6e9`
- old r8152 `module_layout`: `0x3a3eb6e9`
- vendor `alloc_etherdev_mqs`: `0x224a0869`
- candidate `alloc_etherdev_mqs`: `0x224a0869`
- vendor `register_netdev`: `0xe17e26a0`
- candidate `register_netdev`: `0xe17e26a0`

These matches are valuable fingerprints, but the original crash proves they are not a
load-safety certificate.

## Development method after the first crash

Because this SBA6D is a dedicated test environment, later iterations deliberately used
the hardware as an ABI oracle. Oops/panic/reboot was acceptable if the evidence was
captured and the next iteration changed only one relevant item.

The progression was:

1. module load,
2. RTL8156 enumeration and bind,
3. pass the old `__rtl8152_set_mac_address` crash point,
4. netdev creation and MAC retrieval,
5. down-state stability observation,
6. `ip link set eth2 up`,
7. open/NAPI/queue/carrier/runtime-PM path observation without changing routing or
   persistent configuration.

Stage C completed successfully.

## Remaining validation

The next test requires a physical Ethernet link.

Recommended progression:

1. establish physical carrier,
2. confirm negotiated speed and duplex,
3. inspect RX/TX counters before IP configuration,
4. use an isolated temporary subnet,
5. test ARP and ICMP,
6. then measure throughput and CPU/IRQ/softirq behavior.

Do not claim 2.5 Gb/s operation from Stage C alone.

## Project significance

AX88179 showed that the SBA6D vendor ABI could be modeled well enough to build and run one
USB host NIC driver.

r8152/RTL8156 now shows that the same environment can be reused for a structurally
different driver that directly touches more net_device/NAPI/queue state.

That turns the AX88179 result from a one-off compatibility trick into the beginning of a
small SBA6D external-driver SDK.

For another source-available driver, start from the canonical compatibility environment
and add only driver-specific checks for:

- new imported symbols and CRCs,
- direct structure accesses,
- inline helpers,
- dependency modules,
- firmware blobs,
- allocation sizes,
- callbacks and nested structures,
- final-ELF field offsets.

Do not restart from pristine Linux 5.4.238 and assume the release string defines the ABI.

## Binary publication rule

The repository binary must be the **exact ELF that passed Stage B and Stage C**, identified
by its SHA256. A new rebuild that merely appears equivalent is not a substitute for the
runtime-tested bytes.

The tested workspace is:

`/home/masataka/projects/butlerx/work/r8152-rtl8156-sbat6b-canonical-20261004`

The exact tested ELF and SHA256 are intentionally not invented here. They must be copied
from that workspace before the artifact manifest is updated.
