# Kernel output provenance audit (2026-09-05)

## Result

`OLD_OUTPUT_DIFFERS`.

The 2026-09-04 loaded candidate is reproducibly identified by:

* artifact: `candidate/20260904/artifacts/usb_f_ncm.ko`
* SHA256: `d2257ff360fa82c6f2ea639a9856ebd5db7e018b1e71c1113eb74e48ffe7e783`
* ELF `__versions`: 74 import entries, extracted directly from the ELF
  (`__versions` offset `0x5780`, size `0x1280`)

The recorded 2026-09-04 command used:

```text
O=./tmp-kernel-out.yf9KMT
```

That output directory exists. Before this audit, the following were observed
without changing them:

| file | SHA256 |
|---|---|
| `.config` | `c57353bbf7c6af04aa1f40b088dce140dea129782ad2b3dc7f44cf079b49334b` |
| `Module.symvers` | `52eab42809a1ba81b0e1b085415f055b01840bff3d209fccf19d0a43c14044fb` |
| `include/generated/utsrelease.h` | `fb9397c66b0636a3b9ef82b538e2f48e985d2d00168cd79bf6d27661150abfb2` |
| `include/generated/autoconf.h` | `002a8d13e22f74f03e38f07ac92fd4b24f7fc3dec73ecadd82acfff499ec6c84` |
| `include/config/kernel.release` | `8de0975e9b35353dfb65797709a17280961b754e3041299837c158d824bef018` |

The output's `utsrelease.h` contains `5.4.238`; `CONFIG_MODVERSIONS=y` is set.
The output `Module.symvers` is byte-identical to
`sbair6-rce/work/build/out-linux-5.4.238-air6-upstream/Module.symvers`.

## Three-way CRC comparison

The loaded candidate's ELF and the vendor-kimage map agree on all 74 imports.
The old O= `Module.symvers` disagrees with the vendor map on the common kernel
exports, including every requested USB/configfs symbol:

| symbol | old O= | loaded candidate / vendor map |
|---|---:|---:|
| `module_layout` | `0x6006b85e` | `0x3a3eb6e9` |
| `usb_put_function_instance` | `0x3d61e770` | `0x894defe7` |
| `config_group_init_type_name` | `0xcd28fc27` | `0x875b9ac1` |
| `usb_function_register` | `0x9ba95ceb` | `0x6571549d` |
| `usb_function_unregister` | `0xae216fe5` | `0x50fcff8a` |
| `usb_os_desc_prepare_interf_dir` | `0x6244cc03` | `0xfc7b3f68` |

The complete ELF import map is retained in
`candidate/20260904/static/modversions.c.txt`; the vendor map is
`candidate/20260904/abi/vendor-kimage.Module.symvers`.

## Decision

The old O= is present but is not a matching MODVERSIONS environment. Therefore
the conditional same-O= rebuild was not run. In particular, no `oldconfig`,
`prepare`, `modules_prepare`, kernel-tree rebuild, `.config` edit, or
`Module.symvers` generation/overwrite was performed by this audit.

The evidence supports the audit statement:

```text
SOURCE TREE SAME
BUT KERNEL OUTPUT O= DIFFERENT / OUTPUT MAP NOT VENDOR KIMAGE MAP
```

More precisely, the current old O= output carries the upstream-style export
map, while the successfully loaded candidate carries the vendor-kimage CRC
map. The source tree path alone is therefore insufficient provenance.
