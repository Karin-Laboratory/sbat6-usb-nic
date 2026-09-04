# USB Gadget CDC-NCM activation

## Confirmed T6A sequence

The first successful DEVICE sequence observed on the same T6A is:

```text
USB Host未接続
↓
/sys/devices/platform/11201000.usb/mode = 3
↓
xHCI ABSENT
↓
GPIO322 LOW
↓
USB-A VBUS 0V
↓
f5 -> ncm.gs8
↓
UDC unbind/rebind
↓
Host接続
↓
current_speed=super-speed
```

`mode=3` is a T6A vendor sysfs value confirmed by live behavior and logs as the DEVICE operating state. It is not inferred from a generic Linux enum. Older notes that treated `mode=2` as a DEVICE success state are deprecated; the retained observation identifies `mode=2` as the host operating state.

The essential ConfigFS state is `g1/functions/ncm.gs8`, linked as `g1/configs/b.1/f5`, with UDC `11201000.usb` bound. On the BusyBox build, use newline-terminated `echo > "$UDC"` for unbind; `echo -n >` did not clear the field in the recorded recovery.

See `evidence/experiments/t6a-ncm-primary-sequence-20260904-2126.md` and `scripts/recover/` for the bounded procedure.
