# Telemetry design

The telemetry sink is intentionally separate from the vendor data path. A reviewed vendor-tree patch may call the exported functions at NTB handoff, queue, completion, RX unwrap, error, and MTU3 event boundaries. The sink aggregates per-CPU counters and exposes a debugfs snapshot.

Counters are sums, not rates. Capture two snapshots around equal-duration tests and derive rates, fill ratio, completion intervals, and error deltas from the difference. Keep instrumentation out of hot paths unless the measurement explicitly targets instrumentation overhead.

The current design avoids kprobes and ftrace because the target configuration has `CONFIG_KPROBES` and `CONFIG_FUNCTION_TRACER` disabled. It also avoids printk in throughput paths.
