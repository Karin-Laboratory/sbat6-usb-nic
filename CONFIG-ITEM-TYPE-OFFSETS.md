# ConfigFS shared layouts

Compile-time helper: `audit/configfs-abi-layout.c`, compiled with the same
Linux 5.4.238 arm64 kernel headers and `aarch64-linux-gnu-gcc` used for the
candidate ABI audit. ELF array sizes encode each value as value+1.

| type | sizeof | member | offset |
|---|---:|---|---:|
| `struct config_item` | `0x50` | `ci_type` | `0x48` |
| `struct config_group` | `0x88` | `cg_children` | `0x50` |
| `struct config_item_type` | `0x28` | `ct_owner` | `0x00` |
|  |  | `ct_item_ops` | `0x08` |
|  |  | `ct_group_ops` | `0x10` |
|  |  | `ct_attrs` | `0x18` |
|  |  | `ct_bin_attrs` | `0x20` |
| `struct configfs_attribute` | `0x28` | `ca_name` | `0x00` |
|  |  | `ca_owner` | `0x08` |
|  |  | `ca_mode` | `0x10` |
|  |  | `show` | `0x18` |
|  |  | `store` | `0x20` |

These values are compile-time candidate-build-header facts, not claims about
unavailable vendor private headers.
