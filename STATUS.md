# ButlerX current truth — T6A custom NCM

Updated 2026-09-05 15:53 JST.

```text
STATIC_ABI=PASS for candidate 052318dea82970df24dfdb7a47942e79f99b35781f791c48d6bbb2ff7b2cdc1f
UDC_BIND_LIVE=FAIL (fresh register_netdevice+0xb4 Oops)
WINDOWS_NCM_ENUMERATION=NOT_RUN
BIDIRECTIONAL_PING=NOT_RUN
BIDIRECTIONAL_IPERF=NOT_RUN
STABILITY=NOT_RUN
KERNEL_OOPS=1
WDT=1
SPONTANEOUS_REBOOT=1
CUSTOM_NCM_DRIVER_COMPLETE=NOT_COMPLETE
CURRENT_CANDIDATE=NONE (052318 is live-banned)
SOL_LIVE_TEST_READY=no
```

The T6A returned to the vendor baseline after WDT reboot: vendor `usb_net`
loaded, UDC not attached, and no `ncm0`. The fresh fault and provenance are
recorded in
`evidence/experiments/t6a-netdev-final-live-oops-20260905.md`.

Next permitted work is offline ABI reconstruction. The active Image evidence
shows `register_netdevice` consumes `net_device + 0x1f8` as a pointer, while
the banned candidate stores `netdev_ops` at `+0x218`. A new candidate must
re-derive all dependent offsets and pass source/TU/final-ELF gates before any
further live operation. Windows testing is prohibited until Sol re-approves.
