# Performance

## Baseline

Vendor NCM measured approximately 1.37 Gbit/s T6A→Windows and 1.02 Gbit/s Windows→T6A. The forward baseline runs recorded TCP Retr 0.

## Method

Every candidate must change one variable, receive its own commit and evidence file, be benchmarked against a repeated baseline, and have an explicit rollback. Leave trace/debug events disabled during performance measurement: enabled tracing was directly associated with a 474–482 Mbit/s state, while disabling the event set recovered about 1.33 Gbit/s.

The current priority is NTB packing/flush behavior, copy/DMA cost, completion intervals, and MTU3 batching. Host URB starvation and `bMaxBurst=15` are not currently supported as the primary wall by the retained captures.

The 64 KiB NTB, NTB32, request-depth, and flush-policy ideas remain hypotheses. No 2 Gbit/s or 3 Gbit/s claim is made.
