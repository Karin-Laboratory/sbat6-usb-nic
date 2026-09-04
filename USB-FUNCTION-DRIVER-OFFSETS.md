# USB gadget function shared layouts

| type | sizeof | member | offset |
|---|---:|---|---:|
| `struct usb_function_instance` | `0xb0` | `group` | `0x00` |
|  |  | `free_func_inst` | `0xa8` |
| `struct usb_function_driver` | `0x30` | `name` | `0x00` |
|  |  | `mod` | `0x08` |
|  |  | `alloc_inst` | `0x20` |
|  |  | `alloc_func` | `0x28` |

Candidate helper output comes from `audit/configfs-abi-layout.o`. Candidate
`usb_function_driver` is not exported as a named symbol, but its registration
table is represented by the standard four relocations in the module's data.
Vendor `.data+0x928` has the same four placements: name, module, allocation
function at `+0x20` (`.text.unlikely+0x1c7c`), and allocation function at
`+0x28` (`.text.unlikely+0x1fe8`).

The vendor `usb_function_instance` internal layout cannot be independently
reconstructed from this ELF with confidence; candidate `group=0` and
`free_func_inst=0xa8` are compile-time facts.
