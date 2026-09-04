# ButlerX / T6A USB NIC status

| Item | Status |
|---|---|
| Current proven baseline | 2026-09-04 candidate reproduced directory-only ConfigFS behavior; pstore records `__configfs_open_file` NULL dereference. |
| Current T6A state | Unchanged; no candidate copy, insmod, ConfigFS, UDC, reboot, or live experiment in this task. |
| Solved questions | Vendor evidence places `f` at `+0xa0`, `set_inst_name` at `+0xa8`, and `free_func_inst` at `+0xb0`; old candidate used `+0xa8` for `ncm_free_inst`. |
| Current leading root cause | `USB_FUNCTION_INSTANCE_ABI_MISMATCH` → `WRONG_SET_INST_NAME_CALLBACK` → ConfigFS corruption is the high-confidence leading hypothesis, not a final proof. |
| Blocked experiments | T6A deployment and all ConfigFS/UDC/insmod/reboot operations are blocked by the current instruction. Vendor CRCs work only after isolating vmlinux, but the MTK candidate still fails the required 74-import-set gate (72 common CRCs identical; 2 old imports missing). |
| Safety bans | No global `composite.h` patch; no performance changes; no live target operations. |
| Next candidate | `candidate/20260905-mtk-fi-compat/`, private compat instance layout only. |
| Next single live experiment | After separate approval: deploy this candidate and repeat the smallest directory/attribute-read test, with pstore capture. |
| Last updated | 2026-09-05 |

The 2026-09-05 vendor-map diagnostic has `RESULT=FAIL`; no new deployable
artifact was saved. Its 72 common imported CRCs match the old candidate, but
the import set is not identical. T6A deployment remains forbidden.
