# Telemetry

`telemetry/source/sbat6_ncm_telemetry.c` is an observation-only counter sink for a separately reviewed vendor-tree instrumentation patch. It has no kprobes, ftrace hooks, USB registration, ConfigFS access, UDC access, netdev access, timer, or workqueue. Until reviewed vendor code calls its exported APIs, counters remain zero.

The sink records NTB payload/capacity, frames and flushes, queue/completion state, latency and gap bins, RX unwrap/allocation/error counters, and MTU3 event hints. Read two snapshots around equal-duration iperf runs; one snapshot is not a rate measurement.

The candidate was built for vendor Linux 5.4.238 and the recorded SHA256 is `94b157ad17cbe678f2484d058b2e5f8231e5ed6de6fe33f8349ee1588ca6ebf5`. A later candidate integration lost the management path during ConfigFS reconstruction, before any NCM measurement; that failure is retained and is not a performance result.
