# ButlerX / T6A USB NIC status

| Item | Status |
|---|---|
| Current proven baseline | 2026-09-05 candidate loaded and created the corrected ConfigFS instance; UDC bind reached `usb_f_ncm:ncm_bind` and triggered a pstore-recorded NULL dereference. |
| Current T6A state | Recovered after automatic reboot: vendor `usb_net` refcount 6, f1-f4 maintained, f5 absent, candidate/telemetry absent, UDC not attached. |
| Solved questions | Vendor evidence places `f` at `+0xa0`, `set_inst_name` at `+0xa8`, and `free_func_inst` at `+0xb0`; old candidate used `+0xa8` for `ncm_free_inst`. |
| Current leading root cause | `USB_FUNCTION_INSTANCE_ABI_MISMATCH` → `WRONG_SET_INST_NAME_CALLBACK` → ConfigFS corruption is the high-confidence leading hypothesis, not a final proof. |
| Blocked experiments | Candidate functional network test is stopped by kernel Oops during UDC bind. Same-condition retry is prohibited pending diagnosis. Windows enumeration, ping, and iperf were not run. |
| Safety bans | No global `composite.h` patch; no performance changes; no live target operations. |
| Next candidate | No repeat deployment until the `gether_register_netdev+0x2c/0x8c [usb_f_ncm]` NULL dereference is diagnosed. |
| Last experiment | `evidence/experiments/t6a-mtk-ncm-functional-iperf-20260905.md` — candidate insmod/configfs/f5 PASS; UDC bind Oops; vendor restore PASS. |
| Last updated | 2026-09-05 |

The ABI gate artifact used in this experiment was the approved candidate with
SHA256 `1fb49fd6cf347e2676327d92a22808ee0d767792dcbc52261d2d41b81b0afc06`.
The functional test did not reach Windows or iperf. The Oops pstore is retained
under `evidence/pstore/20260905/functional-oops-20260905/`.
