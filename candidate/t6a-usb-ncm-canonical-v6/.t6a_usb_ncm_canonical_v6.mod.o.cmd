cmd_/home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.mod.o := aarch64-linux-gnu-gcc -Wp,-MD,/home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/.t6a_usb_ncm_canonical_v6.mod.o.d -nostdinc -isystem /usr/lib/gcc-cross/aarch64-linux-gnu/14/include -I/home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include -I./arch/arm64/include/generated -I/home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include -I./include -I/home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi -I./arch/arm64/include/generated/uapi -I/home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi -I./include/generated/uapi -include /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kconfig.h -include /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/compiler_types.h -D__KERNEL__ -mlittle-endian -DKASAN_SHADOW_SCALE_SHIFT=3 -Wall -Wundef -Werror=strict-prototypes -Wno-trigraphs -fno-strict-aliasing -fno-common -fshort-wchar -fno-PIE -Werror=implicit-function-declaration -Werror=implicit-int -Werror=return-type -Wno-format-security -std=gnu89 -mgeneral-regs-only -DCONFIG_AS_LSE=1 -DCONFIG_CC_HAS_K_CONSTRAINT=1 -fno-asynchronous-unwind-tables -Wno-psabi -mabi=lp64 -mbranch-protection=none -DKASAN_SHADOW_SCALE_SHIFT=3 -fno-delete-null-pointer-checks -Wno-frame-address -Wno-format-truncation -Wno-format-overflow -Wno-address-of-packed-member -Os -fno-allow-store-data-races -Wframe-larger-than=4096 -fstack-protector -Wimplicit-fallthrough -Wno-unused-but-set-variable -Wno-unused-const-variable -fno-omit-frame-pointer -fno-optimize-sibling-calls -fno-var-tracking-assignments -g -Wdeclaration-after-statement -Wvla -Wno-pointer-sign -Wno-stringop-truncation -Wno-zero-length-bounds -Wno-array-bounds -Wno-stringop-overflow -Wno-restrict -Wno-maybe-uninitialized -fno-strict-overflow -fno-merge-all-constants -fmerge-constants -fno-stack-check -fconserve-stack -Werror=date-time -Werror=incompatible-pointer-types -Werror=designated-init -fmacro-prefix-map=/home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/= -Wno-packed-not-aligned -mstack-protector-guard=sysreg -mstack-protector-guard-reg=sp_el0 -mstack-protector-guard-offset=1056 -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1  -DMODULE  -DKBUILD_BASENAME='"t6a_usb_ncm_canonical_v6.mod"' -DKBUILD_MODNAME='"t6a_usb_ncm_canonical_v6"' -c -o /home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.mod.o /home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.mod.c

source_/home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.mod.o := /home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.mod.c

deps_/home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.mod.o := \
    $(wildcard include/config/module/unload.h) \
    $(wildcard include/config/retpoline.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kconfig.h \
    $(wildcard include/config/cpu/big/endian.h) \
    $(wildcard include/config/booger.h) \
    $(wildcard include/config/foo.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/compiler_types.h \
    $(wildcard include/config/have/arch/compiler/h.h) \
    $(wildcard include/config/enable/must/check.h) \
    $(wildcard include/config/optimize/inlining.h) \
    $(wildcard include/config/cc/has/asm/inline.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/compiler_attributes.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/compiler-gcc.h \
    $(wildcard include/config/arm64.h) \
    $(wildcard include/config/arch/use/builtin/bswap.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/build-salt.h \
    $(wildcard include/config/build/salt.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/elfnote.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/elf.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/elf.h \
    $(wildcard include/config/arm64/force/52bit.h) \
    $(wildcard include/config/compat.h) \
    $(wildcard include/config/compat/vdso.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/hwcap.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/hwcap.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/cpufeature.h \
    $(wildcard include/config/arm64/sw/ttbr0/pan.h) \
    $(wildcard include/config/arm64/sve.h) \
    $(wildcard include/config/arm64/cnp.h) \
    $(wildcard include/config/arm64/ptr/auth.h) \
    $(wildcard include/config/arm64/pseudo/nmi.h) \
    $(wildcard include/config/arm64/debug/priority/masking.h) \
    $(wildcard include/config/arm64/ssbd.h) \
    $(wildcard include/config/arm64/pa/bits.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/cpucaps.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/cputype.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/sysreg.h \
    $(wildcard include/config/broken/gas/inst.h) \
    $(wildcard include/config/arm64/pa/bits/52.h) \
    $(wildcard include/config/arm64/4k/pages.h) \
    $(wildcard include/config/arm64/16k/pages.h) \
    $(wildcard include/config/arm64/64k/pages.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/bits.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/const.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/const.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/bitsperlong.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitsperlong.h \
    $(wildcard include/config/64bit.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/bitsperlong.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/stringify.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/build_bug.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/compiler.h \
    $(wildcard include/config/trace/branch/profiling.h) \
    $(wildcard include/config/profile/all/branches.h) \
    $(wildcard include/config/stack/validation.h) \
    $(wildcard include/config/debug/entry.h) \
    $(wildcard include/config/kasan.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/compiler_types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/types.h \
  arch/arm64/include/generated/uapi/asm/types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/int-ll64.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/int-ll64.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/posix_types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/stddef.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/stddef.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/posix_types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/posix_types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/barrier.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kasan-checks.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/types.h \
    $(wildcard include/config/have/uid16.h) \
    $(wildcard include/config/uid16.h) \
    $(wildcard include/config/arch/dma/addr/t/64bit.h) \
    $(wildcard include/config/phys/addr/t/64bit.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/barrier.h \
    $(wildcard include/config/smp.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/bug.h \
    $(wildcard include/config/generic/bug.h) \
    $(wildcard include/config/bug/on/data/corruption.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/bug.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/asm-bug.h \
    $(wildcard include/config/debug/bugverbose.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/brk-imm.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bug.h \
    $(wildcard include/config/bug.h) \
    $(wildcard include/config/generic/bug/relative/pointers.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kernel.h \
    $(wildcard include/config/preempt/voluntary.h) \
    $(wildcard include/config/debug/atomic/sleep.h) \
    $(wildcard include/config/mmu.h) \
    $(wildcard include/config/prove/locking.h) \
    $(wildcard include/config/arch/has/refcount.h) \
    $(wildcard include/config/panic/timeout.h) \
    $(wildcard include/config/tracing.h) \
    $(wildcard include/config/ftrace/mcount/record.h) \
  /usr/lib/gcc-cross/aarch64-linux-gnu/14/include/stdarg.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/limits.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/limits.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/linkage.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/export.h \
    $(wildcard include/config/modversions.h) \
    $(wildcard include/config/module/rel/crcs.h) \
    $(wildcard include/config/have/arch/prel32/relocations.h) \
    $(wildcard include/config/modules.h) \
    $(wildcard include/config/trim/unused/ksyms.h) \
    $(wildcard include/config/unused/symbols.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/linkage.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/bitops.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/bitops.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/builtin-__ffs.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/builtin-ffs.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/builtin-__fls.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/builtin-fls.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/ffz.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/fls64.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/find.h \
    $(wildcard include/config/generic/find/first/bit.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/sched.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/hweight.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/arch_hweight.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/const_hweight.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/atomic.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/atomic.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/atomic.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/cmpxchg.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/lse.h \
    $(wildcard include/config/as/lse.h) \
    $(wildcard include/config/arm64/lse/atomics.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/atomic_ll_sc.h \
    $(wildcard include/config/cc/has/k/constraint.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/jump_label.h \
    $(wildcard include/config/jump/label.h) \
    $(wildcard include/config/have/arch/jump/label/relative.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/jump_label.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/insn.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/alternative.h \
    $(wildcard include/config/arm64/uao.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/init.h \
    $(wildcard include/config/strict/kernel/rwx.h) \
    $(wildcard include/config/strict/module/rwx.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/atomic_lse.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/atomic-instrumented.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/atomic-fallback.h \
    $(wildcard include/config/generic/atomic64.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/atomic-long.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/lock.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/non-atomic.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/le.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/byteorder.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/byteorder/little_endian.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/byteorder/little_endian.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/swab.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/swab.h \
  arch/arm64/include/generated/uapi/asm/swab.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/swab.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/byteorder/generic.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/bitops/ext2-atomic-setbit.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/log2.h \
    $(wildcard include/config/arch/has/ilog2/u32.h) \
    $(wildcard include/config/arch/has/ilog2/u64.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/typecheck.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/printk.h \
    $(wildcard include/config/message/loglevel/default.h) \
    $(wildcard include/config/console/loglevel/default.h) \
    $(wildcard include/config/console/loglevel/quiet.h) \
    $(wildcard include/config/early/printk.h) \
    $(wildcard include/config/printk/nmi.h) \
    $(wildcard include/config/printk.h) \
    $(wildcard include/config/dynamic/debug.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kern_levels.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/cache.h \
    $(wildcard include/config/arch/has/cache/line/size.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/kernel.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/sysinfo.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/cache.h \
    $(wildcard include/config/kasan/sw/tags.h) \
  arch/arm64/include/generated/asm/div64.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/div64.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/ptrace.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/ptrace.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/sve_context.h \
  arch/arm64/include/generated/asm/user.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/user.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/processor.h \
    $(wildcard include/config/kuser/helpers.h) \
    $(wildcard include/config/have/hw/breakpoint.h) \
    $(wildcard include/config/arm64/tagged/addr/abi.h) \
    $(wildcard include/config/gcc/plugin/stackleak.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/string.h \
    $(wildcard include/config/binary/printf.h) \
    $(wildcard include/config/fortify/source.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/string.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/string.h \
    $(wildcard include/config/arch/has/uaccess/flushcache.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/hw_breakpoint.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/virt.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/sections.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/sections.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/pgtable-hwdef.h \
    $(wildcard include/config/pgtable/levels.h) \
    $(wildcard include/config/arm64/va/bits/52.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/memory.h \
    $(wildcard include/config/arm64/va/bits.h) \
    $(wildcard include/config/kasan/shadow/offset.h) \
    $(wildcard include/config/vmap/stack.h) \
    $(wildcard include/config/debug/align/rodata.h) \
    $(wildcard include/config/debug/virtual.h) \
    $(wildcard include/config/sparsemem/vmemmap.h) \
    $(wildcard include/config/efi.h) \
    $(wildcard include/config/arm/gic/v3/its.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/sizes.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/page-def.h \
    $(wildcard include/config/arm64/page/shift.h) \
    $(wildcard include/config/arm64/cont/shift.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/mmdebug.h \
    $(wildcard include/config/debug/vm.h) \
    $(wildcard include/config/debug/vm/pgflags.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/memory_model.h \
    $(wildcard include/config/flatmem.h) \
    $(wildcard include/config/discontigmem.h) \
    $(wildcard include/config/sparsemem.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/pfn.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/pointer_auth.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/random.h \
    $(wildcard include/config/arch/random.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/list.h \
    $(wildcard include/config/debug/list.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/poison.h \
    $(wildcard include/config/illegal/pointer/value.h) \
    $(wildcard include/config/page/poisoning/zero.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/once.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/random.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/ioctl.h \
  arch/arm64/include/generated/uapi/asm/ioctl.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/ioctl.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/ioctl.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/irqnr.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/irqnr.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/prandom.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/percpu.h \
    $(wildcard include/config/need/per/cpu/embed/first/chunk.h) \
    $(wildcard include/config/need/per/cpu/page/first/chunk.h) \
    $(wildcard include/config/have/setup/per/cpu/area.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/preempt.h \
    $(wildcard include/config/preempt/count.h) \
    $(wildcard include/config/debug/preempt.h) \
    $(wildcard include/config/trace/preempt/toggle.h) \
    $(wildcard include/config/preemption.h) \
    $(wildcard include/config/preempt/notifiers.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/preempt.h \
    $(wildcard include/config/preempt.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/thread_info.h \
    $(wildcard include/config/thread/info/in/task.h) \
    $(wildcard include/config/have/arch/within/stack/frames.h) \
    $(wildcard include/config/hardened/usercopy.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/restart_block.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/time64.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/math64.h \
    $(wildcard include/config/arch/supports/int128.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/time.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/time_types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/errno.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/errno.h \
  arch/arm64/include/generated/uapi/asm/errno.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/errno.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/errno-base.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/current.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/thread_info.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/stack_pointer.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/smp.h \
    $(wildcard include/config/up/late/init.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/cpumask.h \
    $(wildcard include/config/cpumask/offstack.h) \
    $(wildcard include/config/hotplug/cpu.h) \
    $(wildcard include/config/debug/per/cpu/maps.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/threads.h \
    $(wildcard include/config/nr/cpus.h) \
    $(wildcard include/config/base/small.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/bitmap.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/llist.h \
    $(wildcard include/config/arch/have/nmi/safe/cmpxchg.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/smp.h \
    $(wildcard include/config/arm64/acpi/parking/protocol.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/percpu.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/percpu.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/percpu-defs.h \
    $(wildcard include/config/debug/force/weak/per/cpu.h) \
    $(wildcard include/config/amd/mem/encrypt.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/siphash.h \
    $(wildcard include/config/have/efficient/unaligned/access.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/fpsimd.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/sigcontext.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/elf.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/elf-em.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/module.h \
    $(wildcard include/config/sysfs.h) \
    $(wildcard include/config/modules/tree/lookup.h) \
    $(wildcard include/config/livepatch.h) \
    $(wildcard include/config/module/sig.h) \
    $(wildcard include/config/kallsyms.h) \
    $(wildcard include/config/tracepoints.h) \
    $(wildcard include/config/tree/srcu.h) \
    $(wildcard include/config/bpf/events.h) \
    $(wildcard include/config/event/tracing.h) \
    $(wildcard include/config/constructors.h) \
    $(wildcard include/config/function/error/injection.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/stat.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/stat.h \
  arch/arm64/include/generated/uapi/asm/stat.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/stat.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/time.h \
    $(wildcard include/config/arch/uses/gettimeoffset.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/seqlock.h \
    $(wildcard include/config/debug/lock/alloc.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/spinlock.h \
    $(wildcard include/config/debug/spinlock.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/irqflags.h \
    $(wildcard include/config/trace/irqflags.h) \
    $(wildcard include/config/irqsoff/tracer.h) \
    $(wildcard include/config/preempt/tracer.h) \
    $(wildcard include/config/trace/irqflags/support.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/irqflags.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/bottom_half.h \
  arch/arm64/include/generated/asm/mmiowb.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/mmiowb.h \
    $(wildcard include/config/mmiowb.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/spinlock_types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/spinlock_types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/qspinlock_types.h \
    $(wildcard include/config/paravirt.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/qrwlock_types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/lockdep.h \
    $(wildcard include/config/lockdep.h) \
    $(wildcard include/config/lock/stat.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rwlock_types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/spinlock.h \
  arch/arm64/include/generated/asm/qrwlock.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/qrwlock.h \
  arch/arm64/include/generated/asm/qspinlock.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/qspinlock.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rwlock.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/spinlock_api_smp.h \
    $(wildcard include/config/inline/spin/lock.h) \
    $(wildcard include/config/inline/spin/lock/bh.h) \
    $(wildcard include/config/inline/spin/lock/irq.h) \
    $(wildcard include/config/inline/spin/lock/irqsave.h) \
    $(wildcard include/config/inline/spin/trylock.h) \
    $(wildcard include/config/inline/spin/trylock/bh.h) \
    $(wildcard include/config/uninline/spin/unlock.h) \
    $(wildcard include/config/inline/spin/unlock/bh.h) \
    $(wildcard include/config/inline/spin/unlock/irq.h) \
    $(wildcard include/config/inline/spin/unlock/irqrestore.h) \
    $(wildcard include/config/generic/lockbreak.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rwlock_api_smp.h \
    $(wildcard include/config/inline/read/lock.h) \
    $(wildcard include/config/inline/write/lock.h) \
    $(wildcard include/config/inline/read/lock/bh.h) \
    $(wildcard include/config/inline/write/lock/bh.h) \
    $(wildcard include/config/inline/read/lock/irq.h) \
    $(wildcard include/config/inline/write/lock/irq.h) \
    $(wildcard include/config/inline/read/lock/irqsave.h) \
    $(wildcard include/config/inline/write/lock/irqsave.h) \
    $(wildcard include/config/inline/read/trylock.h) \
    $(wildcard include/config/inline/write/trylock.h) \
    $(wildcard include/config/inline/read/unlock.h) \
    $(wildcard include/config/inline/write/unlock.h) \
    $(wildcard include/config/inline/read/unlock/bh.h) \
    $(wildcard include/config/inline/write/unlock/bh.h) \
    $(wildcard include/config/inline/read/unlock/irq.h) \
    $(wildcard include/config/inline/write/unlock/irq.h) \
    $(wildcard include/config/inline/read/unlock/irqrestore.h) \
    $(wildcard include/config/inline/write/unlock/irqrestore.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/time32.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/timex.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/timex.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/param.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/param.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/param.h \
    $(wildcard include/config/hz.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/param.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/timex.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/arch_timer.h \
    $(wildcard include/config/arm/arch/timer/ool/workaround.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/clocksource/arm_arch_timer.h \
    $(wildcard include/config/arm/arch/timer.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/timecounter.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/timex.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/compat.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/compat.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/sched.h \
    $(wildcard include/config/virt/cpu/accounting/native.h) \
    $(wildcard include/config/sched/info.h) \
    $(wildcard include/config/schedstats.h) \
    $(wildcard include/config/fair/group/sched.h) \
    $(wildcard include/config/rt/group/sched.h) \
    $(wildcard include/config/rt/mutexes.h) \
    $(wildcard include/config/uclamp/task.h) \
    $(wildcard include/config/uclamp/buckets/count.h) \
    $(wildcard include/config/cgroup/sched.h) \
    $(wildcard include/config/blk/dev/io/trace.h) \
    $(wildcard include/config/preempt/rcu.h) \
    $(wildcard include/config/tasks/rcu.h) \
    $(wildcard include/config/psi.h) \
    $(wildcard include/config/memcg.h) \
    $(wildcard include/config/compat/brk.h) \
    $(wildcard include/config/cgroups.h) \
    $(wildcard include/config/blk/cgroup.h) \
    $(wildcard include/config/stackprotector.h) \
    $(wildcard include/config/arch/has/scaled/cputime.h) \
    $(wildcard include/config/virt/cpu/accounting/gen.h) \
    $(wildcard include/config/no/hz/full.h) \
    $(wildcard include/config/posix/cputimers.h) \
    $(wildcard include/config/keys.h) \
    $(wildcard include/config/sysvipc.h) \
    $(wildcard include/config/detect/hung/task.h) \
    $(wildcard include/config/audit.h) \
    $(wildcard include/config/auditsyscall.h) \
    $(wildcard include/config/debug/mutexes.h) \
    $(wildcard include/config/ubsan.h) \
    $(wildcard include/config/block.h) \
    $(wildcard include/config/compaction.h) \
    $(wildcard include/config/task/xacct.h) \
    $(wildcard include/config/cpusets.h) \
    $(wildcard include/config/x86/cpu/resctrl.h) \
    $(wildcard include/config/futex.h) \
    $(wildcard include/config/perf/events.h) \
    $(wildcard include/config/numa.h) \
    $(wildcard include/config/numa/balancing.h) \
    $(wildcard include/config/rseq.h) \
    $(wildcard include/config/task/delay/acct.h) \
    $(wildcard include/config/fault/injection.h) \
    $(wildcard include/config/latencytop.h) \
    $(wildcard include/config/function/graph/tracer.h) \
    $(wildcard include/config/kcov.h) \
    $(wildcard include/config/uprobes.h) \
    $(wildcard include/config/bcache.h) \
    $(wildcard include/config/security.h) \
    $(wildcard include/config/arch/task/struct/on/stack.h) \
    $(wildcard include/config/debug/rseq.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/sched.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/pid.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rculist.h \
    $(wildcard include/config/prove/rcu/list.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rcupdate.h \
    $(wildcard include/config/rcu/stall/common.h) \
    $(wildcard include/config/rcu/nocb/cpu.h) \
    $(wildcard include/config/tree/rcu.h) \
    $(wildcard include/config/tiny/rcu.h) \
    $(wildcard include/config/debug/objects/rcu/head.h) \
    $(wildcard include/config/prove/rcu.h) \
    $(wildcard include/config/rcu/boost.h) \
    $(wildcard include/config/arch/weak/release/acquire.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rcutree.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/wait.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/wait.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/refcount.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/sem.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/sem.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/ipc.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/uidgid.h \
    $(wildcard include/config/multiuser.h) \
    $(wildcard include/config/user/ns.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/highuid.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rhashtable-types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/mutex.h \
    $(wildcard include/config/mutex/spin/on/owner.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/osq_lock.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/debug_locks.h \
    $(wildcard include/config/debug/locking/api/selftests.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/workqueue.h \
    $(wildcard include/config/debug/objects/work.h) \
    $(wildcard include/config/freezer.h) \
    $(wildcard include/config/wq/watchdog.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/timer.h \
    $(wildcard include/config/debug/objects/timers.h) \
    $(wildcard include/config/preempt/rt.h) \
    $(wildcard include/config/no/hz/common.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/ktime.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/jiffies.h \
  include/generated/timeconst.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/timekeeping.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/timekeeping32.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/debugobjects.h \
    $(wildcard include/config/debug/objects.h) \
    $(wildcard include/config/debug/objects/free.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/ipc.h \
  arch/arm64/include/generated/uapi/asm/ipcbuf.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/ipcbuf.h \
  arch/arm64/include/generated/uapi/asm/sembuf.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/sembuf.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/shm.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/page.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/personality.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/personality.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/pgtable-types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/pgtable-nopud.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/pgtable-nop4d-hack.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/5level-fixup.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/getorder.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/shm.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/hugetlb_encode.h \
  arch/arm64/include/generated/uapi/asm/shmbuf.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/shmbuf.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/shmparam.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/shmparam.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kcov.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/kcov.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/plist.h \
    $(wildcard include/config/debug/plist.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/hrtimer.h \
    $(wildcard include/config/high/res/timers.h) \
    $(wildcard include/config/time/low/res.h) \
    $(wildcard include/config/timerfd.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/hrtimer_defs.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rbtree.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/timerqueue.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/seccomp.h \
    $(wildcard include/config/seccomp.h) \
    $(wildcard include/config/have/arch/seccomp/filter.h) \
    $(wildcard include/config/seccomp/filter.h) \
    $(wildcard include/config/checkpoint/restore.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/seccomp.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/seccomp.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/unistd.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/unistd.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/unistd.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/seccomp.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/unistd.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/nodemask.h \
    $(wildcard include/config/highmem.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/numa.h \
    $(wildcard include/config/nodes/shift.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/resource.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/resource.h \
  arch/arm64/include/generated/uapi/asm/resource.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/resource.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/resource.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/latencytop.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/sched/prio.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/sched/types.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/signal_types.h \
    $(wildcard include/config/old/sigaction.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/signal.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/signal.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/signal.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/signal.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/signal-defs.h \
  arch/arm64/include/generated/uapi/asm/siginfo.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/asm-generic/siginfo.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/mm_types_task.h \
    $(wildcard include/config/arch/want/batched/unmap/tlb/flush.h) \
    $(wildcard include/config/split/ptlock/cpus.h) \
    $(wildcard include/config/arch/enable/split/pmd/ptlock.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/task_io_accounting.h \
    $(wildcard include/config/task/io/accounting.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/posix-timers.h \
    $(wildcard include/config/posix/timers.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/alarmtimer.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/rseq.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/sched/task_stack.h \
    $(wildcard include/config/stack/growsup.h) \
    $(wildcard include/config/debug/stack/usage.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/magic.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/stat.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kmod.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/umh.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/gfp.h \
    $(wildcard include/config/zone/dma.h) \
    $(wildcard include/config/zone/dma32.h) \
    $(wildcard include/config/zone/device.h) \
    $(wildcard include/config/pm/sleep.h) \
    $(wildcard include/config/contig/alloc.h) \
    $(wildcard include/config/cma.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/mmzone.h \
    $(wildcard include/config/force/max/zoneorder.h) \
    $(wildcard include/config/memory/isolation.h) \
    $(wildcard include/config/shuffle/page/allocator.h) \
    $(wildcard include/config/zsmalloc.h) \
    $(wildcard include/config/memory/hotplug.h) \
    $(wildcard include/config/transparent/hugepage.h) \
    $(wildcard include/config/flat/node/mem/map.h) \
    $(wildcard include/config/page/extension.h) \
    $(wildcard include/config/deferred/struct/page/init.h) \
    $(wildcard include/config/have/memory/present.h) \
    $(wildcard include/config/have/memoryless/nodes.h) \
    $(wildcard include/config/have/memblock/node/map.h) \
    $(wildcard include/config/need/multiple/nodes.h) \
    $(wildcard include/config/have/arch/early/pfn/to/nid.h) \
    $(wildcard include/config/sparsemem/extreme.h) \
    $(wildcard include/config/memory/hotremove.h) \
    $(wildcard include/config/have/arch/pfn/valid.h) \
    $(wildcard include/config/holes/in/zone.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/pageblock-flags.h \
    $(wildcard include/config/hugetlb/page.h) \
    $(wildcard include/config/hugetlb/page/size/variable.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/page-flags-layout.h \
  include/generated/bounds.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/sparsemem.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/mm_types.h \
    $(wildcard include/config/have/aligned/struct/page.h) \
    $(wildcard include/config/userfaultfd.h) \
    $(wildcard include/config/swap.h) \
    $(wildcard include/config/have/arch/compat/mmap/bases.h) \
    $(wildcard include/config/membarrier.h) \
    $(wildcard include/config/aio.h) \
    $(wildcard include/config/mmu/notifier.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/auxvec.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/auxvec.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/uapi/asm/auxvec.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rwsem.h \
    $(wildcard include/config/rwsem/spin/on/owner.h) \
    $(wildcard include/config/debug/rwsems.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/err.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/completion.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/uprobes.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/mmu.h \
    $(wildcard include/config/unmap/kernel/at/el0.h) \
    $(wildcard include/config/randomize/base.h) \
    $(wildcard include/config/cavium/erratum/27456.h) \
    $(wildcard include/config/harden/branch/predictor.h) \
    $(wildcard include/config/harden/el2/vectors.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/page-flags.h \
    $(wildcard include/config/arch/uses/pg/uncached.h) \
    $(wildcard include/config/memory/failure.h) \
    $(wildcard include/config/idle/page/tracking.h) \
    $(wildcard include/config/thp/swap.h) \
    $(wildcard include/config/ksm.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/memory_hotplug.h \
    $(wildcard include/config/arch/has/add/pages.h) \
    $(wildcard include/config/have/arch/nodedata/extension.h) \
    $(wildcard include/config/have/bootmem/info/node.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/notifier.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/srcu.h \
    $(wildcard include/config/tiny/srcu.h) \
    $(wildcard include/config/srcu.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rcu_segcblist.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/srcutree.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rcu_node_tree.h \
    $(wildcard include/config/rcu/fanout.h) \
    $(wildcard include/config/rcu/fanout/leaf.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/topology.h \
    $(wildcard include/config/use/percpu/numa/node/id.h) \
    $(wildcard include/config/sched/smt.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/arch_topology.h \
    $(wildcard include/config/generic/arch/topology.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/topology.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/topology.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/sysctl.h \
    $(wildcard include/config/sysctl.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/uapi/linux/sysctl.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kobject.h \
    $(wildcard include/config/uevent/helper.h) \
    $(wildcard include/config/debug/kobject/release.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/sysfs.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kernfs.h \
    $(wildcard include/config/kernfs.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/idr.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/radix-tree.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/xarray.h \
    $(wildcard include/config/xarray/multi.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kconfig.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kobject_ns.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/kref.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/moduleparam.h \
    $(wildcard include/config/alpha.h) \
    $(wildcard include/config/ia64.h) \
    $(wildcard include/config/ppc64.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/rbtree_latch.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/error-injection.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/error-injection.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/tracepoint-defs.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/static_key.h \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/arch/arm64/include/asm/module.h \
    $(wildcard include/config/arm64/module/plts.h) \
    $(wildcard include/config/dynamic/ftrace.h) \
    $(wildcard include/config/arm64/erratum/843419.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/asm-generic/module.h \
    $(wildcard include/config/have/mod/arch/specific.h) \
    $(wildcard include/config/modules/use/elf/rel.h) \
    $(wildcard include/config/modules/use/elf/rela.h) \
  /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179/include/linux/vermagic.h \
  include/generated/utsrelease.h \

/home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.mod.o: $(deps_/home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.mod.o)

$(deps_/home/masataka/projects/butlerx/candidate/t6a-usb-ncm-canonical-v6/t6a_usb_ncm_canonical_v6.mod.o):
