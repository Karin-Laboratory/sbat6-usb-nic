# GPL corresponding-source request dossier — T6A

Status: draft only; do not send without approval.

## Product and identification

- Product family: SoftBank Air Terminal 6
- Suspected device: DASAN A775
- Modem/platform candidates: Quectel RG620T-SBK; MediaTek T830 / MT6990
- Candidate board/build lineage: `evb6990_cpe_mt7990_emmc`
- Observed kernel: `Linux T6A 5.4.238 #0 SMP Mon Apr 17 13:15:36 2023 aarch64 GNU/Linux`
- Relevant public source label to investigate: `quectel-kernel5.4`

## Requested corresponding source contents

Please provide the complete corresponding GPL source for the shipped kernel
build, including the exact commit or source archive, vendor patches, `.config`
and generated configuration inputs, build scripts/toolchain requirements, and
the relevant USB gadget/network changes (`u_ether`, `f_ncm`, `usb_net`). This
request concerns the GPL-covered kernel and module portions; a proprietary
modem SDK is not requested as a prerequisite.

## Evidence needed to identify the exact correspondence

- exact kernel release/build date and vendor release tag
- vendor/device identification and board configuration
- source/config used for the shipped `Image` and `usb_net.ko`
- relevant GPL notices and download location
- clarification of which public repositories or archives do not match this
  shipped build

## Recipient drafts

### SoftBank

Subject: Request for corresponding GPL source — Air Terminal 6 kernel 5.4.238

Dear SoftBank GPL compliance team, we request the complete corresponding source
for the GPL-covered Linux kernel and modules shipped in SoftBank Air Terminal 6,
observed as kernel 5.4.238. Please include the exact source revision, vendor
patches, configuration, and build information needed to reproduce the shipped
USB gadget/network modules. This request is limited to GPL-covered components;
no proprietary modem SDK is requested.

### DASAN

Subject: Request for corresponding GPL source — DASAN A775 kernel build

Dear DASAN GPL compliance team, please provide the complete corresponding GPL
source and build materials for the A775 firmware kernel identified as Linux
5.4.238, including vendor patches, configuration, and USB/network module
sources. Please identify the exact public source revision and any known
non-matching archives.

### Quectel

Subject: Request for corresponding GPL source — RG620T-SBK / kernel 5.4.238

Dear Quectel GPL compliance team, please provide the complete corresponding GPL
source for the RG620T-SBK-related Linux 5.4.238 build, including vendor patches,
`.config`, build scripts, and the relevant `u_ether`/`f_ncm`/`usb_net` changes.
Please distinguish this exact source from the public `quectel-kernel5.4` trees
if they do not correspond to the shipped image.
