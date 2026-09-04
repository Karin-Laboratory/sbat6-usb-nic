#!/bin/sh
set -eu

# Offline gate for the candidate actually loaded on 2026-09-04.
# This script never contacts a target and never loads a module.
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
SRC=${SRC:-$ROOT/candidate/20260904/source}
KO=${KO:-$ROOT/candidate/20260904/artifacts/usb_f_ncm.ko}
VENDOR_MAP=${VENDOR_MAP:-$ROOT/candidate/20260904/abi/vendor-kimage.Module.symvers}
fail=0
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1"; fail=1; }
has() { grep -R -q -- "$2" "$1" && pass "$3" || fail "$3"; }

[ -f "$KO" ] && pass 'candidate artifact exists' || fail 'candidate artifact exists'
[ -f "$SRC/f_ncm.c" ] && pass 'candidate exact f_ncm.c exists' || fail 'candidate exact f_ncm.c exists'
[ -f "$SRC/u_ether.c" ] && pass 'candidate exact u_ether.c exists' || fail 'candidate exact u_ether.c exists'

has "$SRC/f_ncm.c" 'DECLARE_USB_FUNCTION_INIT(ncm, ncm_alloc_inst, ncm_alloc)' 'usbfunc:ncm registration'
has "$SRC/f_ncm.c" 'ncm_alloc_inst' 'ncm_alloc_inst present'
has "$SRC/f_ncm.c" 'ncm_func_type' 'ncm_func_type present'
has "$SRC/f_ncm.c" 'ct_attrs.*ncm_attrs' 'ncm_func_type.ct_attrs present'
has "$SRC/f_ncm.c" 'dev_addr' 'dev_addr attribute present'
has "$SRC/f_ncm.c" 'host_addr' 'host_addr attribute present'
has "$SRC/f_ncm.c" 'qmult' 'qmult attribute present'
has "$SRC/f_ncm.c" 'ifname' 'ifname attribute present'
has "$SRC/f_ncm.c" 'gether_setup_default' 'gether setup path present'
has "$SRC/f_ncm.c" 'free_func_inst.*=.*ncm_free_inst' 'free_func_inst present'
has "$SRC/f_ncm.c" 'static struct configfs_attribute \*ncm_attrs' 'attribute table present'
has "$SRC/f_ncm.c" 'config_group_init_type_name' 'config_group initialization present'
has "$SRC/f_ncm.c" 'usb_os_desc_prepare_interf_dir' 'OS descriptor path present'
has "$SRC/f_ncm.c" 'gether_register_netdev' 'netdev registration path present'

if command -v readelf >/dev/null 2>&1; then
  readelf -p .modinfo "$KO" | grep -q 'vermagic=5.4.238 SMP mod_unload modversions aarch64' && pass 'vermagic exact' || fail 'vermagic exact'
  readelf -p .modinfo "$KO" | grep -q 'depends=sbat6_ncm_telemetry' && pass 'telemetry-only dependency' || fail 'telemetry-only dependency'
  readelf -sW "$KO" | grep -q ' ncm_alloc_inst$' && pass 'ncm_alloc_inst in ELF' || fail 'ncm_alloc_inst in ELF'
  readelf -sW "$KO" | grep -q ' ncm_alloc$' && pass 'ncm_alloc in ELF' || fail 'ncm_alloc in ELF'
  readelf -sW "$KO" | grep -q ' ncm_func_type$' && pass 'ncm_func_type in ELF' || fail 'ncm_func_type in ELF'
  readelf -sW "$KO" | grep -q ' ncm_attrs$' && pass 'ncm_attrs in ELF' || fail 'ncm_attrs in ELF'
  readelf -sW "$KO" | grep -q ' ncm_free_inst$' && pass 'ncm_free_inst in ELF' || fail 'ncm_free_inst in ELF'
fi

if grep -R -n -E 'bMaxBurst[[:space:]]*=[[:space:]]*15|NTB_DEFAULT_IN_SIZE[[:space:]]+32768|NTB_OUT_SIZE[[:space:]]+32768|DEFAULT_QLEN[[:space:]]+[3-9]' "$SRC" >/dev/null 2>&1; then
  fail 'performance changes absent'
else
  pass 'performance changes absent'
fi

if [ -f "$VENDOR_MAP" ]; then pass 'vendor ABI map present'; else fail 'vendor ABI map present'; fi
printf 'RESULT=%s\n' "$([ "$fail" -eq 0 ] && echo PASS || echo FAIL)"
exit "$fail"
