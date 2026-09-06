# T6A v6 init-time `-EEXIST` root cause and corrected candidate

Date: 2026-09-06 JST

## Result

```text
V6_INIT_EEXIST=PROVEN
V6_INIT_EEXIST_CALLSITE=init_module+0x14 -> usb_function_register(&ncmusb_func); kernel returns -EEXIST because name is "ncm"
V6_FUNCTION_DRIVER_NAME=ncm (bad v6); corrected=t6a_ncm
V5_FUNCTION_DRIVER_NAME=t6a_ncm
V5_V6_INIT_DIFF=bad v6 used DECLARE_USB_FUNCTION_INIT(ncm,...); corrected v6 uses DECLARE_USB_FUNCTION(t6a_ncm,...) plus explicit init/exit
ROOT_CAUSE=v6 reintroduced the vendor-owned usb_function_driver name "ncm", colliding with usb_net
```

The T6A log is decisive: `ncmmod_init` returned `-17`, which is
`-EEXIST`, before any ConfigFS instance or UDC operation. The v6 ELF before
correction had the local init symbol `ncmmod_init`, an object named
`ncmusb_func`, and `alias=usbfunc:ncm`.

The init section of the bad v6 was:

```text
0x00  prologue
0x04  ADRP x0, .data
0x08  ADD  x0, x0, #0
0x0c  MOV  x29, sp
0x10  ADD  x0, x0, #0x240       // &ncmusb_func
0x14  BL   usb_function_register
0x18  epilogue
0x1c  RET                       // returns register result
```

The source macro expands exactly to that call and sets the driver name to
`__stringify(ncm)`. The vendor `usb_net` already owns that name, so this is
the unique init-time `-EEXIST` return site in the module's init path.

v5's ELF instead contains `t6a_ncmusb_func`, `alias=usbfunc:t6a_ncm`, and an
explicit init function that calls `usb_function_register(&t6a_ncmusb_func)`.
The corrected v6 has the same driver name and registration target, with only
the init function's diagnostic logging removed/renamed. A scan of the
corrected v6 source and ELF found no `alias=usbfunc:ncm` and no second
`t6a_ncm` registration object.

## v5 -> v6 source/build/link minimization

The functional `u_ether.c` delta remains the proven timeout fix:

```diff
-       netif_trans_update(net);
+       t6a_netif_trans_update(net);
```

The corrected `f_ncm.c` delta is limited to the registration identity and
the v6 init/exit symbol names. No NCM timeout, wrapping, pending-NTB flush,
queue layout, or USB descriptor code was changed.

The bad v6 was therefore not a linker or compiler collision. It was a source
regression in the registration macro/name. The build logs show the same
kernel output tree, 5.4.238 source, AArch64 compiler, vendor Module.symvers,
and module link procedure for the corrected candidate.

## Loader behavior

The observed shell `insmod RC=0` is not a successful module-init result in
this T6A environment. The vendor loader returned success for the load
command while the kernel initcall later reported `-17` and discarded the
un-recorded module. The authoritative state is the initcall log plus the
absence of `/sys/module`, kallsyms, ConfigFS functions, and `usb0`; therefore
no USB datapath claim was made. This loader-specific mismatch is retained as
a required gate for future live work.

## Corrected candidate and static gates

```text
path=candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.ko
sha256=8d17f76c797d7704f5367441a8000470be73c815495f9016d20fb6b876330799
previous_bad_v6_sha256=12c3f21ce5f387d0d5c21e42d3e3ca0ee8b9840d09c93a45caa66a6223c80212

MODULE_INIT_EEXIST_GATE=PASS
FUNCTION_DRIVER_NAME_COLLISION_GATE=PASS
NULL_SKB_TIMEOUT_PATH_GATE=PASS
TX_DATAPATH_FINAL_ELF_GATE=PASS
FINAL_ELF_VALIDATION=PASS
REPRODUCIBLE_BUILD=PASS
CUSTOM_NCM_NEXT_READY=yes
LIVE_TEST_READY=yes
LIVE_TEST=NOT_RUN
```

The corrected artifact was built twice from clean module outputs; both builds
produced SHA256
`8d17f76c797d7704f5367441a8000470be73c815495f9016d20fb6b876330799`.
The prior proven NULL-SKB semantics remain intact: timeout calls
`ndo_start_xmit(NULL, netdev)` to flush the pending NTB, and the TX timestamp
compatibility remains `net+0x3c0 -> txq+0x88` with the existing queue fields
`num_tx_queues=0x3c8`, `real_num_tx_queues=0x3cc`, `stride=0x140`, and
`state=0x90`.

No live test, SSH operation, module load, UDC bind, ConfigFS mutation, or
host enumeration was performed in this follow-up.
