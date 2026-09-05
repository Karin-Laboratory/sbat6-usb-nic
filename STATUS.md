# ButlerX / T6A USB NIC status

| Item | Status |
|---|---|
| Current proven baseline | Exact existing bbd228 artifact re-audited offline: `dev_addr` final ELF codegen is `0x318`; full direct-access ABI audit is FAIL because private/netdev_priv codegen remains generic. |
| Current T6A state | Recovered after automatic reboot: vendor `usb_net` refcount 6, f1-f4 maintained, f5 absent, candidate/telemetry absent, UDC not attached. |
| Solved questions | Vendor evidence places `f` at `+0xa0`, `set_inst_name` at `+0xa8`, and `free_func_inst` at `+0xb0`; old candidate used `+0xa8` for `ncm_free_inst`. |
| Current leading root cause | Unproven. The retained `gether_register_netdev+0x2c/0x8c` NULL dereference is not proven to be a post-dev_addr `register_netdevice` deep fault. |
| Blocked experiments | Candidate functional network test is stopped by kernel Oops during UDC bind. Same-condition retry is prohibited pending diagnosis. Windows enumeration, ping, and iperf were not run. |
| Safety bans | No global `composite.h` patch; no performance changes; no live target operations. |
| Next candidate | None. No new candidate or live deployment until direct-access ABI audit passes. |
| Last experiment | `evidence/experiments/t6a-mtk-ncm-functional-iperf-20260905.md` — candidate insmod/configfs/f5 PASS; UDC bind Oops; vendor restore PASS. |
| Last updated | 2026-09-05 |

The current exact artifact under audit is SHA256
`bbd228debf2c49a55a68729b1a09eff3e8bba34bb6bb0cb7c085b0158ae88e3c`.
Its exact-ELF static gate passes and its `dev_addr` codegen gate passes, but
the required direct-access ABI audit fails because final ELF private accesses
use the generic `netdev_priv` base. The exact audit is recorded in
`evidence/abi/t6a-bbd228-exact-elf-provenance-reaudit-20260905.md`.

Current candidate SHA: `bbd228debf2c49a55a68729b1a09eff3e8bba34bb6bb0cb7c085b0158ae88e3c`.
Latest proven static gate: exact ELF import/version/CRC/vermagic and
`dev_addr=0x318` PASS; direct-access ABI gate FAIL.
Latest live fault: retained pstore `gether_register_netdev+0x2c/0x8c` NULL
dereference; provenance UNPROVEN.
Fault provenance: not established as `register_netdevice+0xb4` deep fault.
Current blocker: vendor-correct private/netdev_priv codegen and complete
direct-access ABI audit.
Live allowed: no.
The functional test did not reach Windows or iperf. The Oops pstore is retained
under `evidence/pstore/20260905/functional-oops-20260905/`.
