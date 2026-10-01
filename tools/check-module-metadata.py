#!/usr/bin/env python3
"""Offline Linux 5.4 ARM64 module metadata comparison; NEVER load authorization."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sections(path):
    data = path.read_bytes()
    if len(data) < 64 or data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('expected little-endian ELF64')
    if struct.unpack_from('<HH', data, 16) != (1, 183):
        raise ValueError('expected AArch64 relocatable module')
    start = struct.unpack_from('<Q', data, 40)[0]
    width, count, names_index = struct.unpack_from('<HHH', data, 58)
    if width != 64 or not count or names_index >= count or start + width * count > len(data):
        raise ValueError('unsupported or truncated section table')
    headers = [struct.unpack_from('<IIQQQQIIQQ', data, start + i * width) for i in range(count)]

    def payload(header):
        offset, size = header[4:6]
        if offset + size > len(data):
            raise ValueError('truncated section')
        return data[offset:offset + size]

    names = payload(headers[names_index])
    result = {}
    for header in headers:
        end = names.find(b'\0', header[0])
        if end < 0:
            raise ValueError('invalid section name')
        name = names[header[0]:end].decode('ascii')
        if name in ('__versions', '.modinfo'):
            if name in result:
                raise ValueError('duplicate section')
            result[name] = payload(header)
    return result


def compare(module, maps, vermagic):
    expected = {}
    for path in maps:
        for line in path.read_text().splitlines():
            fields = line.split()
            if not fields:
                continue
            if len(fields) < 4 or not fields[0].startswith('0x'):
                raise ValueError('expected Module.symvers rows: CRC SYMBOL OWNER EXPORT')
            crc, name = int(fields[0], 16), fields[1]
            if not 0 <= crc <= 0xffffffff:
                raise ValueError('CRC out of range')
            if name in expected and expected[name] != crc:
                raise ValueError('conflicting reference CRC: ' + name)
            expected[name] = crc
    elf = sections(module)
    versions = elf.get('__versions', b'')
    if not versions or len(versions) % 64:
        raise ValueError('expected nonempty ARM64 5.4 64-byte modversion records')
    actual = {}
    for offset in range(0, len(versions), 64):
        crc = struct.unpack_from('<Q', versions, offset)[0]
        raw = versions[offset + 8:offset + 64]
        if b'\0' not in raw or crc > 0xffffffff:
            raise ValueError('invalid modversion record')
        name = raw.split(b'\0', 1)[0].decode('ascii')
        if not name or name in actual:
            raise ValueError('empty or duplicate version symbol')
        actual[name] = crc
    output = subprocess.check_output(['readelf', '-sW', str(module.resolve())], text=True)
    undefined = set()
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[6] == 'UND':
            undefined.add(fields[7])
    missing_versions = sorted((undefined | {'module_layout'}) - actual.keys())
    rows = []
    for name, crc in sorted(actual.items()):
        reference = expected.get(name)
        rows.append({'symbol': name, 'module_crc': f'0x{crc:08x}',
                     'reference_crc': None if reference is None else f'0x{reference:08x}',
                     'status': 'UNKNOWN' if reference is None else 'MATCH' if crc == reference else 'MISMATCH'})
    magic = [x.decode('ascii') for x in elf.get('.modinfo', b'').split(b'\0') if x.startswith(b'vermagic=')]
    magic_ok = magic == ['vermagic=' + vermagic]
    ok = magic_ok and not missing_versions and all(row['status'] == 'MATCH' for row in rows)
    return {'module': module.name, 'sha256': sha(module),
            'references': [{'file': p.name, 'sha256': sha(p)} for p in maps],
            'metadata_result': 'MATCH' if ok else 'FAIL',
            'load_authorization': 'NOT_ESTABLISHED',
            'limitation': 'Does not prove target identity, reference provenance, structural ABI, behavior, or source/binary correspondence.',
            'vermagic': magic, 'vermagic_match': magic_ok,
            'undefined_without_version': missing_versions, 'symbols': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('module', type=Path)
    parser.add_argument('--symvers', type=Path, action='append', required=True,
                        help='reference Module.symvers; repeat for candidate dependencies')
    parser.add_argument('--vermagic', default='5.4.238 SMP mod_unload modversions aarch64')
    args = parser.parse_args()
    try:
        report = compare(args.module, args.symvers, args.vermagic)
    except (OSError, ValueError, struct.error, subprocess.CalledProcessError) as error:
        print(json.dumps({'metadata_result': 'ERROR', 'load_authorization': 'NOT_ESTABLISHED', 'error': str(error)}))
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report['metadata_result'] == 'MATCH' else 1


if __name__ == '__main__':
    raise SystemExit(main())
