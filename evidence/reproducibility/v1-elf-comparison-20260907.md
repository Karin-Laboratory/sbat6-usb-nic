# v1 published ELF versus clean-build ELF

Date: 2026-09-07 (Asia/Tokyo)

## Inputs

| item | value |
|---|---|
| published asset | `t6a_usb_ncm_65532_candidate_v1.ko` |
| published SHA256 | `7f0e5f3ec197a5f80f23195a3945a2d700bca9d97b8c04eadbacb02c247523c1` |
| clean source | `origin/main` public source bundle |
| clean-build SHA256 | `a9477d52e129f78c2dc0ec93ed01c9ec29a9ffb5e2b3cf50aae7d3474d410cfd` |
| kernel/toolchain | Linux 5.4.238 ARM64, `aarch64-linux-gnu-`, GCC 14.2.0 |

The clean build was staged outside the repository from `git archive
origin/main`, with the matching configured kernel output tree and the public
`t6a-vendor-Module.symvers`. The published asset was downloaded from the v1
release and independently hashed.

## Section-level comparison

The following are SHA256 values of section contents, in the order published / clean.

| section | published | clean | classification |
|---|---|---|---|
| `.text` | `11646a5bcb182dc5eac6e758ee74c0bcea81820790b587e71e2d8084082134e4` | `499db820ff022fc82697df4306399cd9cba70f070506faf34cf5ec8182d33ef8` | **different executable code** |
| `.init.text` | `7f1f5bcda1b776d0694be9f54f5b3cb1729dbb146260bdedeb72fb3865e9b120` | same | equal |
| `.exit.text` | `7f1f5bcda1b776d0694be9f54f5b3cb1729dbb146260bdedeb72fb3865e9b120` | same | equal |
| `__jump_table` | `f5a5fd42d16a20302798ef6ed309979b43003d2320d9f0e8ea9831a92759fb4b` | same | equal |
| `.data` | `ed489ee1cdf32a8e97b7c3779197be0231715a9249d86f1afd7bfb4aafb34e10` | same | equal |
| `__bug_table` | `a9bbb003998fac47818d77cbbebb8ba1241673abbb7cc75ec859dc0d70e4e82d` | same | equal |
| `.gnu.linkonce.this_module` | `1273362e76c174a5ed9eaa8aec34e429a25c415cb873bbcf9d6074d4bbc070d2` | same | equal |
| `.rodata` | `7b4255759d8edb5e1b42ec7ba77564b072090d69b83c87ff0def2180266a2be7` | same | equal |
| `.rodata.str1.1` | `5ff0e534be95b99d7d412d171617a689769431da752639d4fed2eeb7511c56b7` | same | equal |
| `.rodata.str` | `6770c2abfe6cd6eb6b34873225c57de004283842345fdf3ba7667c59e5dff173` | `6972943be88ca6ba0032172acca2fe984497a8d2e11e534fa7c64b401d65eb98` | different non-executable data |
| `.modinfo` | `65e86e8e8b8a5edd123f7bf173ea3d567712144f0e118d3a7815dd5e777dbe0c` | same | equal |
| `__versions` | `77aa4e8e23269f0074c1be631c19ea81a9027599a5522c252b93bb9b761cbcc2` | same | equal |
| `.comment` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | same | equal |

The section table has the same 49 section names and flags. The `.text` size is
`0x31d4` published versus `0x31d8` clean; `.rodata.str` is `0xf5` versus
`0x7a`. Debug sections were present in both ELFs; their offsets and sizes
shift with the preceding section layout, so they are not treated as the cause
of the executable mismatch.

## Metadata and ABI fields

- Build ID: published `18a0a56426d10e19219d0b8eff75a38524db1e87`; clean
  `f36e5f65d29091383acd56be040239f149979a06` — different.
- `modinfo` module name: `t6a_usb_ncm_65532_candidate_v1` — equal.
- vermagic: `5.4.238 SMP mod_unload modversions aarch64` — equal.
- `srcversion`: absent from both — equal.
- normalized `__versions` contents — equal.
- `.comment`: GCC 14.2.0 entries — equal.
- embedded build paths/debug and section offsets differ as expected from the
  clean staging path; they cannot explain the changed `.text` instructions.
- relocation and symbol tables were present in both. Their file offsets move;
  relocations attached to the changed `.text` are therefore not a
  metadata-only difference.

## Normalized disassembly

`aarch64-linux-gnu-objdump -drwC` was normalized for absolute addresses and
compared. The normalized outputs differ. The first semantic divergence is in
`ncm_alloc_inst`: the published code contains the `t6a_gether_setup_name_default`
and `usb_os_desc_prepare_interf_dir` setup sequence, while the clean output
takes a shorter path and reaches different branch targets. This is a runtime
code/data behavior difference, not a timestamp, path, Build ID, or debug-only
difference.

## Decision

**B2 — executable code differs.** v1 is removed from recommendation. The
published binary remains downloadable and marked as a live-validated asset,
but the public source is not claimed as its corresponding source.
