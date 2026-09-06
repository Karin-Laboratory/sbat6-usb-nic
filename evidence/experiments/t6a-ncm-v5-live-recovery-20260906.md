# T6A custom NCM v5 live-test recovery evidence

Date: 2026-09-06 JST
Route: agent-101-vm -> raspi2 -> root@192.168.3.2
Candidate SHA256: `9c00e3d3517c14868cf0bf991c3a9cc4c5e2b5d5017def3da65fbe800736bd9f`

## Recovery observation

- Management SSH through `raspi2` succeeded before and after the required 30-second wait.
- T6A uptime at observation: `up 6 min`; this proves a spontaneous reboot occurred during the v5 live test.
- pstore: `/sys/fs/pstore/console-ramoops-0`, 179740 bytes.
- pstore SHA256: `073963c94ab7ba30ca781cd5f48ca43cc1858dede9181af89e66e82dffb3f141`.
- Crash: NULL dereference at VA `0x88`, `pc=eth_start_xmit+0x294/0x2f8`, reached from `ncm_tx_timeout+0x3c/0x50` in `t6a_usb_ncm_canonical_v5`.

## Post-reboot state

- mode: `2`
- GPIO322: `1`
- UDC value: `11201000.usb`
- UDC state: `not attached`
- custom gadget: absent
- custom `usb0`: absent
- custom `ncm0`: absent
- vendor `g1/configs/b.1/f1..f4`: restored
- vendor `g1/functions/ncm.gs8`: present
- vendor `g1/configs/b.1/f5`: absent
- vendor management `br-lan`: `192.168.3.2/24` present

No blind retry, ADB operation, power-cycle, or additional mutation was performed in this recovery check.
