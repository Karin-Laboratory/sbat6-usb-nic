# sbat6_ncm_fast

This is the first artifact of the new route.  The generated module is a
build/ABI and parameter-safety preflight only.  It intentionally cannot bind
to a UDC and cannot affect the existing `ncm0` gadget.

The eventual data-plane implementation will be a 5.4.238 tree backport of
`f_ncm` plus the required `u_ether` changes, or a vendor-tree in-tree patch.
An ordinary external consumer module cannot replace private `f_ncm`/`u_ether`
state safely; the current kernel's exported `gether_*` API is not sufficient
for a second independent NCM function with custom aggregation.

The parameters are read-only (`0444`) and validated only during init.  There
is no `module_param_cb`, no USB registration, no configfs operation, no UDC
lookup, no role switch, and no network-device operation.
