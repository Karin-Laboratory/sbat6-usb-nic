obj-m += t6a_usb_ncm_canonical_v4.o
t6a_usb_ncm_canonical_v4-objs := u_ether.o f_ncm.o
ccflags-y += -I$(src)/source -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1 -include /home/masataka/projects/sbair6-rce/work/vendor-source/mediatek-aiot-android11-5.4/include/linux/usb/composite.h
KBUILD_CFLAGS += -DCONFIG_TRACEPOINTS=1 -DCONFIG_TRACING=1 -DCONFIG_EVENT_TRACING=1 -DCONFIG_MODULES_TREE_LOOKUP=1

KDIR ?= /home/masataka/projects/sbair6-rce/work/src/linux-5.4.238-ax88179
KBUILD_OUTPUT ?= /home/masataka/projects/butlerx/work/t6a-runtime-kernel-out
KBUILD_EXTRA_SYMBOLS ?= /home/masataka/projects/butlerx/compat/t6a-vendor-Module.symvers

all:
	$(MAKE) -C $(KDIR) O=$(KBUILD_OUTPUT) M=$(CURDIR) ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- KBUILD_EXTRA_SYMBOLS=$(KBUILD_EXTRA_SYMBOLS) modules

clean:
	$(MAKE) -C $(KDIR) O=$(KBUILD_OUTPUT) M=$(CURDIR) clean
