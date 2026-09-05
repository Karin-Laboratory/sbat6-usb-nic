# T6A current truth

Updated 2026-09-05 (RESET STONE 1 complete).

```text
CURRENT_PHASE=RESET_STONE_1_COMPLETE
CURRENT_ARCHITECTURE=vendor lineage reconstruction + staged minimal implementation
CURRENT_CANONICAL_CANDIDATE=none
LIVE_TEST_READY=no
LAST_LIVE_CANDIDATE=052318dea82970df24dfdb7a47942e79f99b35781f791c48d6bbb2ff7b2cdc1f
LAST_LIVE_RESULT=UDC bind FAIL
LAST_FAULT=register_netdevice+0xb4

PROVEN:
- usb_function_instance compatibility and ConfigFS instance live
- bbd228 dev_addr final ELF 0x318
- bbd228 exact ELF static/import gate
- candidate 052318 static ABI gate and pre-UDC gate
- netdev_priv codegen mismatch (bbd228 0x880; vendor-required base 0x8c0)
- netdev_ops mismatch (candidate +0x218; vendor expected +0x1f8)
- RESET STONE 1 Sol audit PASS

UNPROVEN:
- complete vendor struct net_device layout
- exact causal interpretation of register_netdevice+0xb4
- candidate suitable for another live attempt

RETRACTED:
- bbd228 ABI fully fixed
- register_netdevice+0xb4 proves deeper kernel fault
```

The `052318...` candidate passed static admission and the pre-UDC stage, but
the controlled UDC bind caused a NULL dereference, WDT, and reboot. It is
live-banned. The device was returned to the vendor baseline; no candidate is
approved for live testing. Windows enumeration and throughput tests were not
run. Same-condition retry is prohibited.

Evidence index: see [README.md](README.md#current-evidence) and
[docs/T6A_AUTONOMOUS_LOOP_V1.md](docs/T6A_AUTONOMOUS_LOOP_V1.md).
