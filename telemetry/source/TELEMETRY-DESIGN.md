# T6A USB NCM telemetry design

Date: 2026-09-04

## Decision

The first implementation is a counter sink, not an automatic hook. It uses
per-CPU counters and a read-only debugfs file. It does not register a USB
function, touch configfs or a UDC, access a netdev, install kprobes/ftrace, or
print per packet. The expected overhead at each call site is a few per-CPU
increments; timestamp work is limited to completion events.

The module is not an end-to-end measurement until a separately reviewed
vendor-kernel patch calls its exported functions. The saved vendor object has
private/anonymous data-path functions and its exact prototypes are not
available from kallsyms alone. Automatic probing those addresses is therefore
not used.

## Counters and call sites

| API | vendor call site to instrument | measurements |
|---|---|---|
| `sbat6_ncm_tx_ntb` | immediately before TX `usb_ep_queue` | NTBs, payload/capacity, fill, Ethernet frames, flush/full |
| `sbat6_ncm_tx_queue` | queue return path | queue/completion attempts, failures, retries, in-flight |
| `sbat6_ncm_tx_complete` | TX completion callback | completion count, queue-to-completion latency, interval |
| `sbat6_ncm_rx_ntb` | after valid NTB header/NDP parse | NTBs, payload, datagrams |
| `sbat6_ncm_rx_unwrap` | around frame unwrap and skb allocation | unwraps, allocations, elapsed time |
| `sbat6_ncm_rx_complete` | RX completion/refill path | completion interval, in-flight |
| `sbat6_ncm_rx_error` | malformed/drop/error branches | error classes |
| `sbat6_ncm_mtu3_event` | reviewed mtu3 queue/completion/DMA branches | IRQ, DMA map, starvation/empty/full, NAK, idle |

All API arguments are plain values captured by the caller. No skb, request,
endpoint, lock, or pointer is retained. Histograms use 12 logarithmic bins,
starting at 1 us and ending at 1.024 ms or more.

## Required vendor patch points

The next source-level patch must identify exact prototypes and locking context
for `rx_fill`, the NCM TX aggregation/flush path, its completion callback,
NCM unwrap, and mtu3 QMU queue/completion/DMA paths. It must call the APIs only
after the relevant local values are known, preserve return values, and avoid
calls that can sleep. If the vendor tree cannot export the API symbols, link
the counter implementation into the same kernel build or export only these
GPL symbols in a reviewed patch.

## Readout and interpretation

Read `/sys/kernel/debug/sbat6_ncm_telemetry/stats` before and after a fixed
iperf3 interval. Compute deltas, not absolute values. Fill rate is
`delta(tx_payload) / delta(tx_capacity)`. Average payload and frame counts are
the corresponding sums divided by `tx_ntb`; average completion interval and
latency use their `_n` denominators. Counters are intentionally not reset by
read, so the test harness must record start/end snapshots.

The first run should capture baseline only. Then change exactly one of flush
delay, request depth, or NTB size, with Windows link renegotiation and USB
descriptor/control-request capture recorded for every run.
