# T6A netdev_priv/private codegen final candidate — 2026-09-05

## Verdict

The live-banned `bbd228` was not modified. A new offline candidate was built
from a single isolated source/output provenance and checked from its final
AArch64 relocatable ELF.

```text
OLD_BBD228_NETDEV_PRIV_BASE=0x880
EXPECTED_NETDEV_PRIV_BASE=0x8c0
OLD_BBD228_DEV_MAC_ABSOLUTE=0x930
EXPECTED_DEV_MAC_ABSOLUTE=0x970

ROOT_CAUSE_OF_STATIC_ABI_FAILURE=generic netdev_priv() codegen used
                                 ALIGN(sizeof(struct net_device), NETDEV_ALIGN)
                                 = 0x880, while the vendor net_device ABI is 0x8c0
TRANSLATION_UNIT_PROVENANCE=PASS (u_ether.c compiled with vendor-layout header,
                                  generated config, and recorded command line)
NETDEV_PRIV_FINAL_ELF_GATE=PASS
DIRECT_ACCESS_ABI_AUDIT=PASS
NEW_CANDIDATE_SHA256=052318dea82970df24dfdb7a47942e79f99b35781f791c48d6bbb2ff7b2cdc1f
NEXT_LIVE_TEST_READY=yes
```

`NEXT_LIVE_TEST_READY=yes` means all requested static gates passed. The live
sequence itself has not yet been run; the candidate remains offline.

## Artifact and provenance

```text
candidate repo: ../local-projects/sbat6-usb-nic
candidate root: candidate/20260905-netdev-priv-final
final ELF:     candidate/20260905-netdev-priv-final/usb_f_ncm.ko
source TU:     candidate/20260905-netdev-priv-final/source/u_ether.c
linked TU:     candidate/20260905-netdev-priv-final/source/f_ncm.c
srctree:       /tmp/linux-5.4.238-netdev-abi-probe.uMrajx
objtree:       ./tmp-kernel-out.vendorcrc-20260905
ARCH:          arm64
CROSS_COMPILE: aarch64-linux-gnu-
KCFLAGS:       -DCONFIG_WIRELESS_EXT=1 -DCONFIG_T6A_VENDOR_NETDEV_COMPAT=1
```

The srctree's `include/linux/netdevice.h` contains the recovered vendor
32-byte region under `CONFIG_T6A_VENDOR_NETDEV_COMPAT`; the generated config
and command line also retain `CONFIG_WIRELESS_EXT=1`, which is required for
the vendor `dev_addr` offset. Header/config hashes:

```text
netdevice.h  9214601db460247e6f1b51110d8c0d694ec09729164073066339055371440286
.config      c57353bbf7c6af04aa1f40b088dce140dea129782ad2b3dc7f44cf079b49334b
auto.conf    a1a9bb5f0ce56c3be5b2455a4854e30ef1cae7c90d6cc76387ae4eae9a7b7071
autoconf.h   002a8d13e22f74f03e38f07ac92fd4b24f7fc3dec73ecadd82acfff499ec6c84
```

The authoritative vendor map used for the final modpost pass was the existing
84-record `vendor-kimage-extended.Module.symvers`; its temporary objtree
replacement was restored byte-for-byte after the build. `vmlinux` was also
temporarily renamed only during modpost and was restored and checked present.

## TU-local assertions and preprocessed context

`u_ether.c` evaluates these assertions from `gether_setup_name()`; they are
not in a separate probe translation unit:

```c
BUILD_BUG_ON(sizeof(struct net_device) != 0x8c0);
BUILD_BUG_ON(ALIGN(sizeof(struct net_device), NETDEV_ALIGN) != 0x8c0);
BUILD_BUG_ON(offsetof(struct net_device, dev_addr) != 0x318);
BUILD_BUG_ON(offsetof(struct net_device, dev) != 0x510);
```

The same TU fixes the directly accessed `struct eth_dev` layout:

```text
lock=0x00 req_lock=0x20 net=0x10 gadget=0x18
tx_qlen=0x48 rx_frames=0x50 host_mac=0xaa dev_mac=0xb0
```

The preprocessed file is retained at
`candidate/20260905-netdev-priv-final/u_ether.i`. It contains the vendor
`t6a_vendor_private[32]` member and the expanded compile-time assertion
expressions for both structures.

## Direct-access inventory

The linked source files are `u_ether.c` and `f_ncm.c`. `netdev_priv()` and
`container_of()` accesses are compiler-derived; no hand-written private offset
was inserted.

| structure | directly accessed fields / operation | source | expected relative | expected absolute |
|---|---|---|---:|---:|
| `struct net_device` | `dev_addr` | `u_ether.c` setup/register | `0x318` | `0x318` |
| `struct net_device` | `dev` / `dev.parent` | `u_ether.c` setup | `0x510` | `0x510` |
| `struct eth_dev` | `lock`, `port_usb`, `net`, `gadget`, `req_lock` | `u_ether.c` | `0x00..0x20` | `0x8c0..0x8e0` |
| `struct eth_dev` | `tx_reqs`, `rx_reqs`, `tx_qlen`, `rx_frames` | `u_ether.c` | `0x28,0x38,0x48,0x50` | `0x8e8,0x8f8,0x908,0x910` |
| `struct eth_dev` | `qmult`, `header_len`, `wrap`, `unwrap`, `work`, `todo` | `u_ether.c` | `0x68..0xa0` | `0x928..0x960` |
| `struct eth_dev` | `host_mac`, `dev_mac` | `u_ether.c` | `0xaa`, `0xb0` | `0x96a`, `0x970` |
| `struct f_ncm` / `net_device` | `ncm->netdev`, `stats.tx_dropped`, `netdev_ops->ndo_start_xmit` | `f_ncm.c` | compiler-derived | compiler-derived |

Final-ELF scan of all relevant linked code:

```text
NETDEV_PRIV_FINAL_ELF_BASE=0x8c0
ETH_DEV_DEV_MAC_FINAL_ELF_ABSOLUTE=0x970
final ELF #0x8c0 occurrences=7
final ELF #0x970 occurrences=3
final ELF #0x880 occurrences=0
final ELF #0x930 occurrences=0
```

## Old versus new final ELF

Old exact `bbd228` (`bbd228de...`) contained:

```text
gether_register_netdev: add x21, x20, #0x8c0  (the explicit dev_addr helper)
dev_mac source:        net + 0x930 / +0x934
ordinary netdev_priv:  net + 0x880 elsewhere
```

The new final ELF contains:

```text
gether_register_netdev:
  add x22, x0, #0x970
  ldr w3, [x0, #0x970]
  ldrh w2, [x0, #0x974]
  str w3, [x1]
  strh w2, [x1, #4]

private-base accesses elsewhere:
  add ..., #0x8c0
```

Thus the requested correction is proven in machine code:
`0x930 -> 0x970`, while the `dev_addr` destination remains `0x318`.

## Raw static gates

```text
[PASS] exact final ELF exists
[PASS] final ELF SHA256 = 052318dea82970df24dfdb7a47942e79f99b35781f791c48d6bbb2ff7b2cdc1f
[PASS] actual undefined symbols have __versions (81/82; module_layout excluded)
[PASS] kernel import CRCs exact (74/74)
[PASS] telemetry import CRCs exact (7/7)
[PASS] module_layout = 0x3a3eb6e9
[PASS] vermagic = 5.4.238 SMP mod_unload modversions aarch64
[PASS] net_device sizeof = 0x8c0 in actual u_ether.c TU
[PASS] ALIGN(sizeof(struct net_device), NETDEV_ALIGN) = 0x8c0 in actual u_ether.c TU
[PASS] offsetof(struct net_device, dev_addr) = 0x318 in actual u_ether.c TU
[PASS] offsetof(struct net_device, dev) = 0x510 in actual u_ether.c TU
[PASS] struct eth_dev dev_mac = 0xb0 in actual u_ether.c TU
[PASS] final ELF private base has #0x8c0 and no #0x880
[PASS] final ELF dev_mac has #0x970 and no #0x930
[PASS] final ELF gether_register_netdev dev_addr destination = 0x318
[PASS] function_instance f = +0xa0
[PASS] function_instance set_inst_name = +0xa8
[PASS] function_instance free_func_inst = +0xb0
MODULE_VERSIONS_GATE=PASS
FUNCTION_INSTANCE_GATE=PASS
NET_DEVICE_PROBE_GATE=PASS
NET_DEVICE_TU_GATE=PASS
NETDEV_PRIV_FINAL_ELF_GATE=PASS
DIRECT_ACCESS_ABI_AUDIT=PASS
```

## Safety status

No T6A module load, UDC bind, Windows connection, `/proc/kcore` analysis, or
live test was performed. bbd228 remains live-banned. The new candidate is
offline-proven static-ready, and `NEXT_LIVE_TEST_READY=yes`. The candidate is
eligible for the controlled recovery/live procedure, but that procedure was
not run in this build/audit step.
