# Known non-working and rejected candidates

## runtime2 — DO NOT REUSE

Repeated execution of `insmod sbat6_usb_role_runtime2.ko role=2` reproduced SSH loss, `raspi2 eth0` `NO-CARRIER`, abnormal T6A LED state, and temporary loss of T6A operability. This candidate is prohibited from reuse.

## RX max 8192

Changing host `cdc_ncm/rx_max` from `16384` to `8192` collapsed throughput to about 6 Mbps, produced TCP Retr 867, and increased host RX errors. It was restored to `16384`.

```text
Result: REGRESSION
Confidence: HIGH
Reverted: YES
```

## Excessive debug/tracing

Hot-path trace/event recording produced a measured approximately 482 Mbps state. Disabling the event set recovered about 1.33 Gbit/s.

```text
Result: REGRESSION
Confidence: HIGH
Reverted: YES
```

## Runtime tuning

The following did not materially improve the repeated baseline: IRQ affinity, `tx_buff_num`, `qmult`, `uether_tx_max_aggr_num`, `u_ether_tx_req_threshold`, `tx_queue_len`, and multi-TCP-stream variants. Retain the detailed per-experiment records; do not treat these as untested ideas.

```text
Result: NO_IMPROVEMENT
Confidence: HIGH
Reverted: YES
```

## Candidate ConfigFS reconstruction

The 2026-09-04 observation-only/provider replacement attempt lost the T6A management path during symlink reconstruction. No UDC bind, Windows enumeration, iperf, or telemetry measurement followed. The result is `ABORTED`/`BLOCKED`, not a performance result. Normal reboot and the vendor recovery sequence restored the known baseline.
