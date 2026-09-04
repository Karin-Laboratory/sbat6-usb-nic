# Device mode and GPIO322 observation

On the same T6A, with the same USB A-A cable and the same Windows USB port, the following reversible observations were recorded:

| State | Observed USB result | Throughput |
|---|---|---:|
| GPIO322 HIGH | `current_speed=high-speed`, USB 2.0 | about 333–350 Mbit/s |
| GPIO322 LOW, then UDC rebind | `current_speed=super-speed` | about 1.38 Gbit/s |

This establishes that GPIO322 state was associated with the observed SuperSpeed outcome in this setup. It does not establish the internal hardware causal mechanism. Do not generalize beyond the tested device, cable, port, and sequence without a new experiment.

The safe DEVICE entry observed from the vendor mode node is `mode=3`; after the host role is removed, xHCI is absent, GPIO322 is low, and VBUS is measured at 0 V before host attachment.
