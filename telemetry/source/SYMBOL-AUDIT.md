# T6A telemetry symbol audit

Date: 2026-09-04

## Existing vendor object

The prior read-only audit of `usb_net.ko` established:

- `gether_connect` is a retained local symbol at `.text+0x3394`.
- `rx_fill` is retained at `.text+0x2f78`.
- The request allocator is anonymous at `.text.unlikely+0x25c`.
- The allocator and relevant TX/RX helpers are not a stable exported module
  interface; the anonymous helper has no callable source prototype.
- `qmult=30` is visible in configfs, but its exact relation to live vendor
  request counts is unresolved.
- mtu3 QMU state is visible through debugfs, but endpoint identity and the
  gadget request-list layer are not uniquely mapped.

## Probe decision

No kprobe/kretprobe/ftrace module was built or loaded. A probe at a raw local
address would depend on the exact loaded object, kernel configuration,
optimization, register ABI, and function prologue. It would also risk running
in IRQ/atomic context with an incorrect prototype and would be difficult to
unload safely while USB callbacks are active. ftrace availability and
`CONFIG_KPROBES` do not make a private function prototype safe.

## ABI and context checks required before source integration

The vendor source patch must record the exact prototypes, compiler/kernel
configuration, `CONFIG_MODVERSIONS`, preemption model, lock ownership, and
whether each call site is IRQ, softirq, task, or timer context. Telemetry calls
must not allocate, sleep, take a new lock, dereference retained pointers, or
emit printk. Unload is safe only after all callers are removed; the standalone
module's debugfs removal is recursive and its API stores no external state.

## Available symbols in the built sink

The sink imports only normal kernel facilities (`debugfs`, `seq_file`, per-CPU
and time helpers) and exports its eight telemetry entry points with
`EXPORT_SYMBOL_GPL`. It contains no USB, UDC, configfs, role-switch, or
netdev symbols. The exports are an integration interface, not proof that the
current `usb_net.ko` calls them.
