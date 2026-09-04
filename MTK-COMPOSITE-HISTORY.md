# MediaTek downstream composite ABI history

## Public evidence

The public MediaTek Android 3.18 `include/linux/usb/composite.h` contains:

```c
struct usb_function_instance {
    struct config_group group;
    struct list_head cfs_list;
    struct usb_function_driver *fd;
    struct usb_function *f;
    int (*set_inst_name)(struct usb_function_instance *inst,
                         const char *name);
    void (*free_func_inst)(struct usb_function_instance *inst);
};
```

Source: <https://android.googlesource.com/kernel/mediatek/+/android-mtk-3.18/include/linux/usb/composite.h>

The public MediaTek 6.0.1 functions implementation is at:
<https://android.googlesource.com/kernel/mediatek/+/android-6.0.1_r0.16/drivers/usb/gadget/functions.c>

## Comparison with generic 5.4

The Linux 5.4.238 header used for the candidate has no `f` member:

```c
struct usb_function_instance {
    struct config_group group;
    struct list_head cfs_list;
    struct usb_function_driver *fd;
    int (*set_inst_name)(struct usb_function_instance *inst,
                         const char *name);
    void (*free_func_inst)(struct usb_function_instance *inst);
};
```

The local generic ConfigFS implementation calls `fi->set_inst_name()` in
`drivers/usb/gadget/configfs.c:function_make()` after
`config_item_set_name()`. The dereference changes from `+0xa0` to `+0xa8`
between the two layouts.

## Offset consequence

| field | generic 5.4 candidate | MediaTek-family variant |
|---|---:|---:|
| `fd` | `0x98` | `0x98` |
| `f` | absent | `0xa0` |
| `set_inst_name` | `0xa0` | `0xa8` |
| `free_func_inst` | `0xa8` | `0xb0` |
| struct size | `0xb0` | `0xb8` |

This public history independently supports the vendor ELF observation. It
does not by itself prove that this exact downstream header was used by T6A;
that conclusion comes from matching vendor offsets and the pstore failure.

## Current conclusion

ABI mismatch and wrong-callback are now the leading explanation for the
reproduced ConfigFS failure. A callback-named pstore trace is still missing,
so root cause is recorded as **high-confidence candidate**, not irreversible
proof. `S30usb.init start` and `reboot_reason=3` remain post-boot evidence,
not proof that the init script caused the reboot.
