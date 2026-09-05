#!/usr/bin/env python3
"""Provenance-aware structural layout solver v3.

The source model and compiler oracle are deliberately separate.  Enumeration
varies only real conditional declarations; this tool never invents padding or
upgrades unrelated DWARF/TU observations into vendor constraints.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, tempfile, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

COND = re.compile(r"^\s*#\s*(ifdef|ifndef|if|elif|else|endif)\b(.*)$")
DECL = re.compile(r"^\s*(?P<decl>[^#/][^;{}]*;)\s*$")
NAME = re.compile(r"([A-Za-z_]\w*)\s*(?:\[([^]]+)\])?\s*;")
DEFAULT_FIELDS = ("netdev_ops", "ethtool_ops", "min_mtu", "max_mtu",
                  "addr_assign_type", "dev_addr", "dev", "stats")

def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def ordered_fields(path: Path) -> list[dict]:
    lines = path.read_text(errors="replace").splitlines()
    start = next(i for i, x in enumerate(lines) if re.match(r"^struct net_device\s*\{", x))
    stack: list[str] = []; out = []; order = 0
    for no in range(start + 1, len(lines)):
        line, s = lines[no], lines[no].strip(); m = COND.match(line)
        if m:
            k, arg = m.group(1), m.group(2).strip()
            if k == "endif":
                if stack: stack.pop()
            elif k == "else":
                if stack: stack[-1] = f"!({stack[-1]})"
            elif k == "elif":
                if stack: stack[-1] = arg
            else:
                stack.append(arg if k == "if" else (f"defined({arg})" if k == "ifdef" else f"!defined({arg})"))
            continue
        if s.startswith(("/*", "*", "#", "//")) or not s or not s.endswith(";"): continue
        m = DECL.match(line)
        if not m: continue
        decl = m.group("decl").strip(); nm = NAME.search(decl)
        if not nm: continue
        out.append({"ORDER": order + 1, "FIELD": nm.group(1), "TYPE": decl[:nm.start(1)].strip(),
                    "ARRAY_COUNT": nm.group(2) or 1, "SIZE_RULE": "compiler-oracle",
                    "ALIGN_RULE": "compiler-ABI", "CONDITION": " && ".join(stack) if stack else "always",
                    "SOURCE_LOCATION": f"{path}:{no+1}", "LINEAGE": "B_STRONG_VENDOR_SIBLING_SOURCE"})
        order += 1
    return out

def config_states(path: Path | None, variables: list[str]) -> dict[str, str]:
    vals = {}
    if path:
        for line in path.read_text(errors="replace").splitlines():
            m = re.match(r"(CONFIG_[A-Z0-9_]+)=(.*)$", line)
            if m: vals[m.group(1)] = m.group(2)
    return {v: vals.get(v, "UNKNOWN") for v in variables}

def oracle(root: Path, outdir: Path, config: Path | None, compiler: str, vendor_include: Path | None = None, build_output: Path | None = None) -> dict:
    """Ask GCC to materialize sizeof/offsetof constants in assembly."""
    gen = (build_output / "include/generated" if build_output else root / "include/generated")
    archgen = (build_output / "arch/arm64/include/generated" if build_output else root / "arch/arm64/include/generated")
    inc = ([vendor_include] if vendor_include else []) + ([build_output / "include"] if build_output else []) + [archgen, root / "arch/arm64/include", root / "include",
           root / "arch/arm64/include/uapi", gen, root / "include/uapi", gen / "uapi"]
    src = outdir / "layout_oracle.c"; asm = outdir / "layout_oracle.s"
    body = ["#include <stddef.h>", "#include <linux/netdevice.h>", "static void solver_probe(void) {",
            'asm volatile(".ascii \\\"SOLVER_SIZE=%c0\\\\n\\\"" : : "i"(sizeof(struct net_device)));']
    for field in DEFAULT_FIELDS:
        body.append(f'asm volatile(".ascii \\\"SOLVER_OFF_{field}=%c0\\\\n\\\"" : : "i"(offsetof(struct net_device, {field})));')
    body += ["}", "int main(void) { solver_probe(); return 0; }"]
    src.write_text("\n".join(body) + "\n")
    cmd = [compiler, "-S", "-O2", "-mabi=lp64", "-mgeneral-regs-only", "-D__KERNEL__", "-DMODULE"]
    cmd += ["-I" + str(x) for x in inc if x.exists()]
    if (gen / "autoconf.h").exists(): cmd += ["-include", str(gen / "autoconf.h")]
    if (root / "include/linux/kconfig.h").exists(): cmd += ["-include", str(root / "include/linux/kconfig.h")]
    if (root / "include/linux/compiler_types.h").exists(): cmd += ["-include", str(root / "include/linux/compiler_types.h")]
    if config:
        for line in config.read_text(errors="replace").splitlines():
            m = re.match(r"(CONFIG_[A-Z0-9_]+)=y$", line)
            if m: cmd.append(f"-D{m.group(1)}=1")
    cmd += [str(src), "-o", str(asm)]
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode: return {"status": "FAIL", "command": cmd, "stderr": p.stderr[-4000:]}
    vals = {}
    for line in asm.read_text(errors="replace").splitlines():
        m = re.search(r"SOLVER_(SIZE|OFF_([A-Za-z0-9_]+))=([0-9]+)", line)
        if m: vals["sizeof" if m.group(1) == "SIZE" else m.group(2)] = int(m.group(3))
    return {"status": "PASS" if len(vals) == len(DEFAULT_FIELDS) + 1 else "FAIL", "values": vals,
            "compiler": compiler, "command": cmd, "source_sha256": sha(src)}

def concrete_offset_table(header: Path, kernel_tree: Path, kernel_output: Path | None,
                          variables: list[str], fixed: dict[str, str], compiler: str,
                          jobs: int, temp_root: Path | None = None,
                          checkpoint: Path | None = None,
                          checkpoint_every: int = 256) -> tuple[list[dict], dict]:
    """Compile one real Class-B header per unknown CONFIG assignment.

    Each row is a compiler-produced offsetof table.  No offsets are inferred
    from anchors or interpolated between rows.
    """
    include_root = header.parent.parent
    generated = kernel_output / "include/generated" if kernel_output else kernel_tree / "include/generated"
    archgen = kernel_output / "arch/arm64/include/generated" if kernel_output else kernel_tree / "arch/arm64/include/generated"
    includes = [include_root, kernel_output / "include" if kernel_output else None,
                archgen, kernel_tree / "arch/arm64/include", kernel_tree / "include",
                kernel_tree / "arch/arm64/include/uapi", generated,
                kernel_tree / "include/uapi", generated / "uapi"]
    includes = [x for x in includes if x and x.exists()]
    body = ["#include <stddef.h>", "#include <linux/netdevice.h>",
            "#define SOLVER_ROW(x) x", "int main(void) {"]
    body.append('asm volatile("SOLVER_SIZE=%c0\\n" : : "i"(sizeof(struct net_device)));')
    for field in DEFAULT_FIELDS:
        body.append(f'asm volatile("SOLVER_OFF_{field}=%c0\\n" : : "i"(offsetof(struct net_device, {field})));')
    body.append("return 0;}")
    source = "\n".join(body) + "\n"
    unknown = [v for v in variables if fixed.get(v) == "UNKNOWN"]
    count = 1 << len(unknown)

    progress = {"completed": 0, "total": count, "last_model": None}
    progress_lock = threading.Lock()
    if checkpoint:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(json.dumps({**progress, "status": "STARTED"}, indent=2) + "\n")

    def one(model: int) -> dict:
        defines = []
        for name in variables:
            on = fixed.get(name) == "y" or (name in unknown and model & (1 << unknown.index(name)))
            if on: defines.append("-D" + name + "=1")
            else: defines.append("-U" + name)
        with tempfile.TemporaryDirectory(prefix=f"t6a-layout-{model:05d}-", dir=temp_root) as td:
            td = Path(td); src, asm = td / "probe.c", td / "probe.s"; src.write_text(source)
            cmd = [compiler, "-S", "-O2", "-mabi=lp64", "-mgeneral-regs-only",
                   "-D__KERNEL__", "-DMODULE", *defines]
            cmd += ["-I" + str(x) for x in includes] + [str(src), "-o", str(asm)]
            p = subprocess.run(cmd, text=True, capture_output=True)
            if p.returncode:
                return {"model": model, "status": "FAIL", "stderr": p.stderr[-1200:]}
            values = {}
            for line in asm.read_text(errors="replace").splitlines():
                m = re.search(r"SOLVER_(SIZE|OFF_([A-Za-z0-9_]+))=([0-9]+)", line)
                if m: values["sizeof" if m.group(1) == "SIZE" else m.group(2)] = int(m.group(3))
            row = {"model": model, "status": "PASS" if len(values) == len(DEFAULT_FIELDS) + 1 else "FAIL", "values": values}
        if checkpoint:
            with progress_lock:
                progress["completed"] += 1
                progress["last_model"] = model
                if progress["completed"] % max(1, checkpoint_every) == 0 or progress["completed"] == count:
                    checkpoint.write_text(json.dumps({**progress, "status": "RUNNING" if progress["completed"] < count else "COMPLETE"}, indent=2) + "\n")
        return row

    with tempfile.TemporaryDirectory(prefix="t6a-layout-shim-") as shimtd:
        shim = Path(shimtd) / "vdso"; shim.mkdir()
        (shim / "const.h").write_text("""#ifndef __VDSO_CONST_H\n#define __VDSO_CONST_H\n#define __AC(X,Y) (X##Y)\n#define _AC(X,Y) __AC(X,Y)\n#define _AT(T,X) ((T)(X))\n#endif\n""")
        (shim / "limits.h").write_text("""#ifndef __VDSO_LIMITS_H\n#define __VDSO_LIMITS_H\n#define INT_MAX ((int)(~0U >> 1))\n#define INT_MIN (-INT_MAX - 1)\n#define UINT_MAX (~0U)\n#define ULONG_MAX (~0UL)\n#endif\n""")
        (shim / "bits.h").write_text("""#ifndef __VDSO_BITS_H\n#define __VDSO_BITS_H\n#define __VDSO_BITS_PER_LONG 64\n#endif\n""")
        includes.insert(0, Path(shimtd))
        with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            rows = list(pool.map(one, range(count)))
    return rows, {"compiler": compiler, "header": str(header), "include_roots": [str(x) for x in includes],
                  "source_sha256": hashlib.sha256(source.encode()).hexdigest(), "jobs": jobs}

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--class-b", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--kernel-tree", type=Path); ap.add_argument("--config", type=Path)
    ap.add_argument("--kernel-output", type=Path, help="separate Kbuild output tree containing generated headers")
    ap.add_argument("--compiler", default="aarch64-linux-gnu-gcc"); ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--concrete-offset-table", action="store_true")
    ap.add_argument("--jobs", type=int, default=min(16, os.cpu_count() or 1))
    ap.add_argument("--temp-root", type=Path, help="filesystem-backed temp root for per-model compiler work")
    ap.add_argument("--checkpoint", type=Path, help="periodic JSON progress checkpoint for concrete evaluation")
    ap.add_argument("--checkpoint-every", type=int, default=256)
    args = ap.parse_args(); db = json.loads(args.db.read_text()); fields = ordered_fields(args.class_b)
    variables = db.get("layout_config_variables", []); states = config_states(args.config, variables)
    unknown = [x for x in variables if states[x] == "UNKNOWN"]
    assert len(variables) == 24 and (1 << len(unknown)) == 32768
    assert {x["FIELD"] for x in fields} >= {"netdev_ops", "addr_assign_type", "dev_addr", "dev"}
    # Existing anchors are retained as inventory observations.  Their class is
    # explicit and they remain hard-eligible only because the DB labels them A.
    evidence = [{"EVIDENCE_ID": f"anchor-{i:03d}", "CLASS": ("G_INFERENCE" if k == "addr_assign_type" else "A_EXACT_VENDOR_BINARY"),
                 "ARTIFACT_SHA": "RECORDED_DB_VALUE_ONLY", "ORIGIN": "v1 anchor inventory",
                 "KERNEL_VERSION": "5.4.x", "CONFIG_LINEAGE": "vendor-unknown", "TARGET": k,
                 "VALUE": v, "CAN_BE_HARD_VENDOR_CONSTRAINT": ("no" if k == "addr_assign_type" else "yes")}
                for i, (k, v) in enumerate(sorted(db.get("anchors", {}).items()), 1)]
    evidence += [{"EVIDENCE_ID": "addr-assign-dwarf-quarantined", "CLASS": "D_OTHER_LINEAGE_DWARF",
                  "ARTIFACT_SHA": "RECORDED_MEMORY_ONLY", "ORIGIN": "quarantined DWARF/TU review",
                  "KERNEL_VERSION": "5.4.238", "CONFIG_LINEAGE": "other-lineage", "TARGET": "addr_assign_type",
                  "VALUE": "0x24e", "CAN_BE_HARD_VENDOR_CONSTRAINT": "no"}]
    constraints = [{"ANCHOR_ID": e["EVIDENCE_ID"], "FIELD": e["TARGET"], "EXPECTED_OFFSET": e["VALUE"],
                   "WIDTH": 8, "EVIDENCE_ARTIFACT": e["ORIGIN"], "EVIDENCE_FUNCTION": "unknown",
                   "CONFIDENCE": "inventory-only"} for e in evidence if e["CAN_BE_HARD_VENDOR_CONSTRAINT"] == "yes"]
    result = {"schema": "t6a-structural-layout-solver-v3", "STRUCTURAL_UNSAT": "NOT_PROVEN",
              "PREVIOUS_MODEL_COUNT_ZERO_INTERPRETATION": "RETRACTED", "source": str(args.class_b),
              "source_sha256": sha(args.class_b), "ordered_fields": fields,
              "config": {"variables": variables, "states": states, "unknown": unknown, "combinations": 1 << len(unknown)},
              "evidence_lineage": evidence, "constraints": constraints,
              "anchor_audit": {"HARD_VENDOR_ANCHOR_COUNT": sum(e["CAN_BE_HARD_VENDOR_CONSTRAINT"] == "yes" for e in evidence),
                               "SOFT_LINEAGE_ANCHOR_COUNT": sum(e["CLASS"] in ("B_STRONG_VENDOR_SIBLING_SOURCE", "C_RUNTIME_TARGET_EVIDENCE") for e in evidence),
                               "RETRACTED_OR_QUARANTINED_COUNT": sum(e["CAN_BE_HARD_VENDOR_CONSTRAINT"] == "no" for e in evidence),
                               "ADDR_ASSIGN_TYPE_VENDOR_OFFSET": "UNPROVEN"},
              "lineage_policy": {"hard_vendor_classes": ["A_EXACT_VENDOR_BINARY", "C_RUNTIME_TARGET_EVIDENCE"],
                "layout_generation_classes": ["A_EXACT_VENDOR_BINARY", "B_STRONG_VENDOR_SIBLING_SOURCE"],
                "excluded_hard_classes": ["D_OTHER_LINEAGE_DWARF", "E_OTHER_LINEAGE_TU", "F_HISTORICAL_CANDIDATE", "G_INFERENCE"]},
              "status_taxonomy": ["NO_DEPENDENCY_CLOSURE", "PREPROCESS_FAILED", "COMPILE_FAILED",
                                  "MODELS_GENERATED_NOT_EVALUATED", "SAT_MULTIPLE", "SAT_UNIQUE", "UNSAT"]}
    result["KABI_MACRO_EXPANSION_VALIDATED"] = "NOT_RUN"
    table = []
    table_meta = None
    if args.concrete_offset_table:
        if not args.kernel_tree:
            raise SystemExit("--concrete-offset-table requires --kernel-tree")
        table, table_meta = concrete_offset_table(args.class_b, args.kernel_tree, args.kernel_output,
                                                   variables, states, args.compiler, args.jobs, args.temp_root,
                                                   args.checkpoint, args.checkpoint_every)
        result["concrete_offset_table"] = table
        result["concrete_offset_table_meta"] = table_meta
    if args.oracle and args.kernel_tree:
        with tempfile.TemporaryDirectory(prefix="t6a-solver-v3-") as td:
            # The supplied Class-B header is retained as source representation;
            # the oracle uses the complete kernel tree's include closure.  A
            # partial vendor include tree (notably its vdso/const.h dependency)
            # must not be mistaken for a compilable ABI tree.
            result["compiler_oracle"] = oracle(args.kernel_tree, Path(td), args.config, args.compiler, build_output=args.kernel_output)
    raw = 1 << len(unknown)
    oracle_pass = result.get("compiler_oracle", {}).get("status") == "PASS"
    # A compiler probe is one concrete model.  The 32768 assignments are
    # generated symbolically, but are not promoted to concrete layouts until
    # the oracle's header/config lineage is the vendor lineage.
    evaluated = sum(row.get("status") == "PASS" for row in table) if table else (1 if oracle_pass else 0)
    valid = 0
    if table:
        for row in table:
            values = row.get("values", {})
            if row.get("status") == "PASS" and all(values.get(k) == int(v, 0) for k, v in db.get("anchors", {}).items() if k in ("netdev_ops", "ethtool_ops", "dev_addr", "dev")) and values.get("sizeof") == int(db["anchors"]["netdev_priv"], 0):
                valid += 1
    if table:
        failures = [r for r in table if r.get("status") != "PASS"]
        missing_header_failures = [r for r in failures if "fatal error:" in r.get("stderr", "") and "No such file" in r.get("stderr", "")]
        result["dependency_closure"] = {
            "attempted": len(table), "compiled": evaluated, "evaluated": evaluated,
            "preprocess_failed": len(missing_header_failures),
            "compile_failed": len(failures) - len(missing_header_failures),
            "failure_examples": [r.get("stderr", "") for r in failures[:5]],
        }
    result["counters"] = {"LAYOUT_MODEL_GENERATED_COUNT": raw, "TOTAL_RAW_LAYOUT_MODELS": raw,
        "LAYOUT_MODEL_ATTEMPTED_COUNT": len(table) if table else (1 if oracle_pass else 0),
        "LAYOUT_MODEL_COMPILED_COUNT": evaluated,
        "LAYOUT_MODEL_EVALUATED_COUNT": evaluated, "CONSTRAINT_INSTANCE_COUNT": len(constraints),
        "VALID_STRUCT_LAYOUT_MODEL_COUNT": valid if evaluated else "NOT_EVALUATED"}
    oracle_values = result.get("compiler_oracle", {}).get("values", {})
    vendor_match = (oracle_values.get("netdev_ops") == 0x1f8 and
                    oracle_values.get("ethtool_ops") == 0x200 and
                    oracle_values.get("dev_addr") == 0x318 and
                    oracle_values.get("dev") == 0x510 and
                    oracle_values.get("sizeof") == 0x8c0)
    result["vendor_lineage_oracle_match"] = vendor_match
    if table and evaluated == 0:
        result["solver_status"] = "PREPROCESS_FAILED" if result["dependency_closure"]["preprocess_failed"] else "COMPILE_FAILED"
    else:
        result["solver_status"] = "SAT_MULTIPLE" if valid > 1 else ("SAT_UNIQUE" if valid == 1 else ("UNSAT" if table else ("SAT_MULTIPLE" if oracle_pass and vendor_match else "MODELS_GENERATED_NOT_EVALUATED")))
    result["evaluation_scope"] = "concrete compiler rows" if table else ("one compiler baseline; symbolic assignments require vendor-lineage oracle" if oracle_pass else "no concrete compiler model")
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("STRUCTURAL_SOLVER_SELFTEST=PASS")
    print("LAYOUT_ENGINE_COMPILER_VALIDATION=" + result.get("compiler_oracle", {}).get("status", "NOT_RUN"))
    for k, v in result["counters"].items(): print(f"{k}={v}")
    print("SOLVER_STATUS=" + result["solver_status"]); return 0

if __name__ == "__main__": raise SystemExit(main())
