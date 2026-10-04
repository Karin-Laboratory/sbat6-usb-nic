#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
: "${KERNEL_GIT:?Set KERNEL_GIT to a Linux v5.4.238 checkout}"
: "${OUTPUT:?Set OUTPUT to a new absolute build directory}"
CROSS_COMPILE=${CROSS_COMPILE:-aarch64-linux-gnu-}
export CROSS_COMPILE
REV=6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6
case "$OUTPUT" in /*) ;; *) echo 'OUTPUT must be absolute' >&2; exit 2;; esac
[ ! -e "$OUTPUT" ] || { echo 'OUTPUT already exists' >&2; exit 2; }

(cd "$HERE" && sha256sum -c INPUTS.sha256)
git -C "$KERNEL_GIT" cat-file -e "$REV^{commit}"
mkdir -p "$OUTPUT/kernel" "$OUTPUT/module"
if [ -n "${KERNEL_SRC:-}" ]; then
	if git -C "$KERNEL_SRC" rev-parse --git-dir >/dev/null 2>&1; then
		git -C "$KERNEL_SRC" diff --quiet
		git -C "$KERNEL_SRC" diff --cached --quiet
		git -C "$KERNEL_SRC" cat-file -e "$REV^{commit}"
	fi
	ln -s "$KERNEL_SRC" "$OUTPUT/source"
	mkdir -p "$OUTPUT/source-backup"
	for item in .config include/config arch/arm64/include/generated; do
		if [ -e "$KERNEL_SRC/$item" ]; then
			mkdir -p "$OUTPUT/source-backup/$(dirname "$item")"
			mv "$KERNEL_SRC/$item" "$OUTPUT/source-backup/$item"
		fi
	done
	if ! grep -q 't6_vendor_private\[32\]' "$KERNEL_SRC/include/linux/netdevice.h"; then
		patch -d "$KERNEL_SRC" -p1 < "$HERE/netdevice.patch"
	fi
	restore_source() {
		if [ -e "$OUTPUT/source-backup/include/linux/netdevice.h" ]; then
			patch -d "$KERNEL_SRC" -p1 -R < "$HERE/netdevice.patch" || true
		fi
		for item in arch/arm64/include/generated include/config .config; do
			if [ -e "$OUTPUT/source-backup/$item" ]; then
				mkdir -p "$KERNEL_SRC/$(dirname "$item")"
				mv "$OUTPUT/source-backup/$item" "$KERNEL_SRC/$item"
			fi
		done
	}
	trap restore_source EXIT
else
	mkdir -p "$OUTPUT/source"
	git -C "$KERNEL_GIT" archive --format=tar --output="$OUTPUT/source.tar" "$REV"
	tar -xf "$OUTPUT/source.tar" -C "$OUTPUT/source"
	find "$OUTPUT/source" -type f -path '*/.git/*' -delete 2>/dev/null || true
	patch -d "$OUTPUT/source" -p1 < "$HERE/netdevice.patch"
fi
cp "$HERE/kernel.config" "$OUTPUT/kernel/.config"
make -C "$OUTPUT/source" O="$OUTPUT/kernel" ARCH=arm64 LOCALVERSION= olddefconfig modules_prepare
cp "$HERE/vendor-image.symvers" "$OUTPUT/kernel/Module.symvers"
cp "$HERE/Makefile" "$HERE/abi_assert.h" "$OUTPUT/module/"
cp "$HERE/compatibility.h" "$OUTPUT/module/"
cp "$OUTPUT/source/drivers/net/mii.c" "$OUTPUT/module/"
cp "$HERE/r8152.c" "$OUTPUT/module/"

# This is deliberately KCFLAGS: it reaches the generated *.mod.c TU too.
KCFLAGS="-DCONFIG_USB_RTL8152_MODULE=1 -DCONFIG_WIRELESS_EXT=1 -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1 -include $OUTPUT/module/abi_assert.h"
export KCFLAGS
make -C "$OUTPUT/source" O="$OUTPUT/kernel" M="$OUTPUT/module" ARCH=arm64 LOCALVERSION= -j"${JOBS:-4}" modules > "$OUTPUT/build.log" 2>&1

for name in mii r8152; do
	python3 "$HERE/check-module-metadata.py" "$OUTPUT/module/$name.ko" \
		--symvers "$HERE/vendor-image.symvers" --symvers "$OUTPUT/module/Module.symvers" > "$OUTPUT/$name-metadata.json"
	"${CROSS_COMPILE}objdump" -dr "$OUTPUT/module/$name.ko" > "$OUTPUT/$name.asm"
	"${CROSS_COMPILE}readelf" -SW -rW "$OUTPUT/module/$name.ko" > "$OUTPUT/$name-elf.txt"
	done
(cd "$OUTPUT/module" && sha256sum mii.ko r8152.ko > SHA256SUMS)
"${CROSS_COMPILE}gcc" --version > "$OUTPUT/compiler.txt"
