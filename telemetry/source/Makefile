# Set this to the saved vendor Linux 5.4.238 source tree when building.
KDIR ?= /path/to/linux-5.4.238
KBUILD_OUTPUT ?=
ARCH ?= arm64
CROSS_COMPILE ?= aarch64-linux-gnu-
obj-m += sbat6_ncm_telemetry.o
all:
	$(MAKE) -C $(KDIR) $(if $(KBUILD_OUTPUT),O=$(KBUILD_OUTPUT),) M=$(CURDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) modules
clean:
	$(MAKE) -C $(KDIR) $(if $(KBUILD_OUTPUT),O=$(KBUILD_OUTPUT),) M=$(CURDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) clean
