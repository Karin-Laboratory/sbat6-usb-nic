# T6B / SBA6D RTL8156 (r8152): canonical compatibility build, 2.5GbE datapath and iperf3

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

The current verified result is **Stage D PASS with 2.5GbE datapath and iperf3 validation**:

- r8152 loads,
- RTL8156 enumerates and automatically binds,
- a netdev is created,
- the MAC address is read correctly,
- `ip link set dev eth2 up` succeeds,
- 2.5 Gb/s Full Duplex physical link is negotiated,
- bidirectional IPv4 ping succeeds with 0% loss,
- iperf3 reaches 2.27 Gbit/s with P1 and 2.15 Gbit/s with P4,
- retransmissions are 0 in both iperf3 runs,
- RX/TX errors and drops remain 0,
- no r8152-related WARN/Oops/panic occurred,
- the previously reproducible `__rtl8152_set_mac_address` crash no longer occurs.

The remaining untested area is long-duration stability and broader traffic characterization,
not basic driver functionality or 2.5GbE datapath.

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
interface-open execution. Stage D and the later iperf3 run then demonstrated the actual
2.5GbE data path.

## Stage D: physical link and IP datapath

The RTL8156 port was connected directly to a Pavilion 5GbE port. The RTL8156 side
negotiated at its expected maximum:

- carrier: `1`
- speed: `2500Mb/s`
- duplex: `Full`
- temporary SBA6D address: `192.168.50.2/24`
- peer: `192.168.50.1`

Basic connectivity:

- initial ping: 3/3, 0% loss
- 60-second ping: 60 transmitted / 60 received / 0% loss
- RTT min/avg/max: `1.815/2.799/3.951 ms`
- RX packets before/after: `102 / 176`
- TX packets before/after: `9 / 74`
- RX errors/drops: `0 / 0`
- TX errors/drops: `0 / 0`
- boot_id unchanged
- no USB reset/disconnect
- no r8152 WARN
- no Oops/panic

The temporary IP was removed after the test.

Verdict: **Stage D PASS**.

## iperf3 throughput

A later iperf3 server was started on the Pavilion at `192.168.50.1:5201`.
SBA6D transmitted over `eth2`.

Observed:

- P1, 10 seconds: **2.27 Gbit/s**, retransmissions 0
- P4, 10 seconds: **2.15 Gbit/s**, retransmissions 0
- ping after the throughput test: 3/3, 0% loss
- link remained 2500 Mb/s Full Duplex
- RX/TX errors and drops remained 0
- boot_id unchanged
- management path remained available
- temporary `192.168.50.2/24` address removed after the test

The peer was running iperf3, so an iperf2 client attempt was not protocol-compatible and
was discarded as a test-method mismatch rather than a driver failure.

This result validates practical near-line-rate-class 2.5GbE transmission on the tested
path. It is not yet a long-duration soak test.

## Tested binary identity

The exact r8152 ELF used for the successful Stage D and iperf3 work is:

`build-d/artifact-a/r8152.ko`

SHA256:

`6890208bc3375d6d71b5d1a661a1dc3b70fe5825675d75c6e5391c7cbfa79d78`

Canonical local workspace:

`/home/masataka/projects/butlerx/work/r8152-rtl8156-sbat6b-canonical-20261004`

The repository artifact, when added, must be these exact tested bytes.

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

Basic 2.5GbE datapath and short iperf3 throughput are now validated.

Remaining work is optional characterization rather than basic bring-up:

1. reverse-direction iperf3,
2. longer soak tests,
3. mixed P1/P4/P10 runs,
4. CPU/IRQ/softirq observation,
5. repeated unplug/replug and module reload testing.

Do not generalize the measured 2.27 Gbit/s result to other firmware, hosts, cables or NIC revisions.

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

The repository binary must be the **exact ELF that passed Stage B, Stage C, Stage D and
the iperf3 test**, identified by its SHA256. A new rebuild that merely appears equivalent is not a substitute for the
runtime-tested bytes.

The tested workspace is:

`/home/masataka/projects/butlerx/work/r8152-rtl8156-sbat6b-canonical-20261004`

Exact tested SHA256: `6890208bc3375d6d71b5d1a661a1dc3b70fe5825675d75c6e5391c7cbfa79d78`.

The binary itself still must be copied from the canonical workspace before the artifact
manifest is updated.
