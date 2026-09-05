# ButlerX current truth — T6A custom NCM

Updated 2026-09-05 16:50 JST.

```text
STATIC_ABI=RETRACTED for candidate 052318dea82970df24dfdb7a47942e79f99b35781f791c48d6bbb2ff7b2cdc1f (full admission coverage incomplete)
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
SOL_RESET_REVIEW_1=COMPLETE
SOL_RECOMMENDED_LOOP_V1=T6A_AUTONOMOUS_LOOP_V1.md
AUTONOMOUS_LOOP_V2=DESIGNED_OFFLINE (docs/T6A_AUTONOMOUS_LOOP_V2.md)
052318_FULL_STATIC_ADMISSION=RETRACTED
052318_KNOWN_ABI_GATES=PASS
052318_DIRECT_ACCESS_COVERAGE=INCOMPLETE
052318_MODVERSIONS_CONTRADICTION=RESOLVED_CASE_B (exact ELF matches vendor map; saved modcrc.tsv is wrong-source/stale)
052318_MODVERSIONS_REPRODUCIBILITY=RESOLVED_CONTRADICTION_ONLY
PROCESS_FAILURE_PROVEN=known direct-access fields existed in the inventory but were not mechanically required by candidate admission
SELECTED_ARCHITECTURE=B vendor source lineage, validated incrementally using E
ACTIVE_IMAGE_MAPPING=UNPROVEN
SOL_USAGE_METRICS_AVAILABLE=no
ABI_MANIFEST_SYSTEM=IN_PROGRESS_FAIL_CLOSED
SOURCE_MANIFEST_COVERAGE=100% (lexical field set; actual TU/codegen pending)
SOURCE_DIRECT_ACCESS_COUNT=10
MANIFEST_DIRECT_ACCESS_COUNT=33
SPECIAL_DIRECT_ACCESS_COUNT=37
UNGATED_DIRECT_ACCESS_COUNT=0
INDEPENDENT_RAW_KALLSYMS=SAVED
LOADER_GATE_REPRODUCIBLE=PASS_FOR_REPRODUCED_SOURCE_CONFIG (two independent offline clean builds; exact 052318 provenance still incomplete)
PIECEWISE_NET_DEVICE_MAP=INSUFFICIENT
VENDOR_LINEAGE_RECONSTRUCTION=INCOMPLETE
RESET_STONE_2_READY=no
```

The T6A returned to the vendor baseline after WDT reboot: vendor `usb_net`
loaded, UDC not attached, and no `ncm0`. The fresh fault and provenance are
recorded in
`evidence/experiments/t6a-netdev-final-live-oops-20260905.md`.

Next permitted work is offline vendor-lineage reconstruction and multi-anchor
active-Image VA/file mapping. Vendor paired callback producer evidence suggests
`netdev_ops/ethtool_ops = +0x1f8/+0x200`, while `052318` stores at `+0x218/+0x220`,
but the active Image opcode mapping remains unproven. A new candidate must
re-derive every dependent offset and pass loop v1 gates before rebuild, load, or
UDC bind. Windows testing is prohibited until Sol re-approves.

CURRENT_CANONICAL_CANDIDATE=NONE
CURRENT_PROVEN_FACTS=vendor baseline recovered; custom candidates live-banned; Sol RESET STONE 1 complete; T6A read-only baseline healthy
CURRENT_HYPOTHESES=hybrid private ABI is malformed; vendor source lineage is best route; active Image mapping may resolve register_netdevice consumer
RETRACTED_CLAIMS=CRC proves private ABI; static PASS proves live safety; anonymous 32-byte insertion is complete; active Image +0xb4 field is proven
LATEST_LIVE_RESULT=052318 UDC bind Oops/WDT/reboot, then vendor recovery
CURRENT_BLOCKER=complete vendor ABI and active Image mapping are not proven
NEXT_ACTION=offline runtime-text evidence redesign plus piecewise vendor source-lineage audit

Continuation review 2026-09-05:

```text
SOL_HEALTHCHECK=PASS
BUTLERX_SOL_E2E=PASS
SOL_CONTINUATION_REVIEW=JUSTIFIED_OFFLINE_ONLY
ACTIVE_IMAGE_IDENTITY=PARTIALLY_PROVEN
VA_IMAGE_MAPPING=FAIL
VENDOR_LINEAGE_RECONSTRUCTION=INCOMPLETE
DIRECT_ACCESS_ABI_AUDIT=FAIL_INCOMPLETE
LOADER_GATE_REPRODUCIBLE=PASS_FOR_REPRODUCED_SOURCE_CONFIG
FINAL_ELF_CODEGEN_AUDIT=FAIL
CANDIDATE_LIVE_READY=NO
```

The read-only identity consolidation is recorded in
`evidence/manifests/t6a-active-kernel-identity-20260905.json`. An independent
raw kallsyms capture is now hash-pinned at
`evidence/manifests/t6a-kallsyms-raw-20260905.txt`; multi-symbol VA-to-Image
byte proof is still missing. The V2 single-source manifest is
`evidence/manifests/t6a-abi-manifest-v2.json`.
