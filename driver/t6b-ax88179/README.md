# T6B AX88179: source rebuild and device recognition

2026-10-01: the recipe below was built in a fresh output directory and those
exact modules were loaded on the test T6B. AX88179 (0b95:1790) registered as
`eth2` at USB 5000 Mbps. Normal removal of the preceding compatibility build
and reloading the fresh recipe outputs both succeeded. No Oops was seen in
the captured interval. **Subsequent Ethernet testing passed: 1 Gbps link, reserved DHCP lease, and ICMP reachability. Throughput and long-term stability remain untested.**

This is a tested compatibility recipe for this target and this driver chain,
not a guarantee for arbitrary drivers or other firmware. It does not require
an unpublished vendor source tree to build. The retained target Image is
needed only to independently regenerate the supplied CRC reference.

## Build in three steps

Tested toolchain: Debian AArch64 GCC 14.2.0, binutils 2.44. Requirements:
Git, Python 3, make, tar, patch, sha256sum, gcc, flex, bison, bc, libssl-dev,
libelf-dev, gcc-aarch64-linux-gnu, binutils-aarch64-linux-gnu. Other compiler
versions have not been validated with this recipe.

1. Clone this repository and upstream stable Linux:

   ```sh
   git clone --branch docs/driver-reproduction-audit https://github.com/Karin-Laboratory/sbat6-usb-nic.git
   git clone --depth 1 --branch v5.4.238 https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git linux-5.4.238
   ```

   This recipe is currently published in PR #9's branch. Once merged, use
   main at a commit containing this directory instead.

2. Build from the fixed upstream commit and bundled inputs:

   ```sh
   cd sbat6-usb-nic
   KERNEL_GIT="$(realpath ../linux-5.4.238)" \
     OUTPUT="$PWD/build/t6b-ax88179" sh driver/t6b-ax88179/build.sh
   ```

   `OUTPUT` must not exist. The script archives commit
   `6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6` into a new tree, applies the
   header patch, prepares the bundled config, and builds all three modules.
   Existing kernel worktrees are not modified. `INPUTS.sha256` checks the
   bundled build inputs before work begins.

3. Inspect `build/t6b-ax88179/*-metadata.json`, `*-elf.txt`, `*.asm` and
   `module/SHA256SUMS`. Expected version record counts: mii 6, usbnet 92,
   ax88179_178a 48; all match the Image/dependency references. Confirm
   `.gnu.linkonce.this_module` size `0x340` and, where present, cleanup
   relocation `0x328`. CRC success alone is not a load-safety certificate.

Modules are in `build/t6b-ax88179/module/`. Full ELF hashes may differ across
build paths because debug information is retained. The first compatibility
build and the independent recipe build had equal `.text`, `.init.text`,
`.exit.text`, `.data`, `.rodata`, `__versions`, and module-management section
bytes wherever present. Both builds were tested on the target; the second
build's exact hashes are retained in the experiment report.

## Compatibility corrections

The existing NCM records supplied the netdev model and final-ELF methodology.
The later runtime-config oracle supplied the working module layout. Two
details missing from an easy public recipe were decisive:

- Preserve `CONFIG_WIRELESS_EXT` and the recovered 32-byte opaque region
  immediately before `dev_addr`. Do not insert it before `netdev_ops`.
  Assertions require size/private base `0x8c0`, ops `0x1f8`, ethtool ops
  `0x200`, dev_addr `0x318`, embedded device `0x510`, TX pointer `0x3c0`,
  queue stride `0x140`, and queue state `0x90`.
- Preserve `TRACEPOINTS`, `TRACING`, `EVENT_TRACING`, and
  `MODULES_TREE_LOOKUP` in compilation, even though upstream Kconfig
  normalization removed them from the recovered vendor configuration.
  **Use KCFLAGS for all compilation, including generated `.mod.c`.**
  `ccflags-y` alone left the module cleanup at `0x258`; the final recipe
  verifies size `0x340`, init `0x150`, and cleanup `0x328` in actual TUs.

The source header patch changes compiler layout; module CRCs are supplied
to modpost from the target reference. No finished ELF CRC records are patched.
`LOCALVERSION_AUTO` is disabled and `LOCALVERSION` is empty to avoid an
unintended `-dirty` vermagic suffix.

The opaque region is a compatibility model, not recovered vendor field
names. This does not reconstruct every USB/network/SKB ABI field. Passing
the assertions establishes the listed anchors; actual recognition supplies
the bounded runtime result. Basic DHCP/ICMP datapath testing has subsequently passed; sustained traffic testing remains necessary.

## Reference provenance

`kernel.config` is the normalized build config derived from the saved T6B
configuration, with driver selections and localversion controls. It is not
claimed to be an unmodified `/proc/config.gz` or a complete vendor kernel.

The 10,205-row `vendor-image.symvers` comes from retained T6B boot_b Image:

```text
Image SHA256: 92fb3e623cf620c4f4169a73e50bc7ba90aa3f86dc3b0d9da1d467de1dfad0fb
PREL32 export entries: [0xcdcbf0, 0xcfaa4c), stride 12
CRC entries: start 0xcfaa4c, stride 4
```

Regeneration from that exact uncompressed Image is optional for building:

```sh
python3 driver/t6b-ax88179/extract-reference.py /path/to/Image /tmp/regenerated.symvers
cmp driver/t6b-ax88179/vendor-image.symvers /tmp/regenerated.symvers
```

This byte comparison passed. The extractor rejects other Image hashes.
Export categories are normalized to EXPORT_SYMBOL for these GPL modules;
the file is not a reconstruction of export-license or namespace policy.
The Image is not redistributed. The installed target's active Image hash
was not freshly re-read in this experiment, so the retained boot_b identity
must not be silently generalized to any other target or update.

T6B Image `dev_addr_init` at file offset `0x6db344` stores a pointer to
`net + 0x318` (`str x1, [x19,#792]` at `0x6db3a4`). This independently
confirms the pointer semantics, not just a numerical offset. Do not copy
an NCM helper's field treatment blindly into a host driver.

## Staged target test

Keep an independent management path and start off-device kernel log capture
before loading. BusyBox on this target lacks `dmesg -w`; stream `/dev/kmsg`
over a separate management session. Verify target-side hashes against the
new build, and confirm old versions are absent before insertion.

On the test target, load one at a time, observing each result and logs:

```sh
insmod /tmp/mii.ko
insmod /tmp/usbnet.ko
insmod /tmp/ax88179_178a.ko
```

Stop on an error/Oops or loss of management. Do not force unload. The successful
test used normal `rmmod ax88179_178a`, `rmmod usbnet`, `rmmod mii` before the
second load. A failed initialization is not a reason to execute those commands
blindly. No boot-time persistence or network-route configuration is installed.

Check the actual USB interface's `net/` directory, driver symlink, device
speed, and new netdev. The interface name and USB topology are not fixed.
In this experiment they were `2-1.4:1.0`, `eth2`, and 5000 Mbps. The initial recognition test left the netdev down. A subsequent cable test
enabled it, obtained the reserved DHCP address, and verified ICMP reachability.
See [the cable-test report](../../evidence/reproducibility/t6b-compat-20261001/ethernet-test.md).

Source/patch/script licensing follows the repository GPL-2.0-only policy.
The upstream kernel sources are obtainable at the fixed commit above.
