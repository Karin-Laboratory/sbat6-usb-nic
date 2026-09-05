# T6A compatibility toolkit ABI evidence

This repository currently contains an offline, fail-closed scaffold. The
proven direct root cause is `register_netdevice+0xb4` loading
`net_device->netdev_ops` at `0x1f8`; it does not prove the complete vendor
layout. The evidence and gate state are maintained in [STATUS.md](../STATUS.md).

Stable public compatibility headers will only be enabled after exact
vendor-lineage source/config provenance, actual-TU assertions, final ELF
verification, and loader ABI proof all pass.
