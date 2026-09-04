import struct, sys, collections, statistics

path = sys.argv[1]
f = open(path, 'rb')
gh = f.read(24)
magic, = struct.unpack('<I', gh[:4])
if magic != 0xa1b2c3d4:
    raise SystemExit(f'unsupported pcap magic {magic:x}')
bulk = collections.Counter(); submits = collections.Counter(); completes = collections.Counter()
times = []; ntb = collections.Counter(); ndp = collections.Counter(); outstanding = 0; max_out = 0
records = 0; bulk_records = 0; data_records = 0
while True:
    h = f.read(16)
    if not h: break
    ts_sec, ts_usec, incl, orig = struct.unpack('<IIII', h)
    p = f.read(incl); records += 1
    if len(p) < 64: continue
    typ, xfer, ep, dev, bus = p[8], p[9], p[10], p[11], struct.unpack_from('<H', p, 12)[0]
    if bus != 2 or dev != 9 or xfer != 3 or ep != 0x88: continue
    bulk_records += 1
    length, cap = struct.unpack_from('<II', p, 32)
    payload = p[64:64+cap]
    if typ == ord('S'):
        submits[length] += 1; outstanding += 1; max_out = max(max_out, outstanding)
    elif typ == ord('C'):
        completes[length] += 1; outstanding = max(0, outstanding-1); times.append(ts_sec + ts_usec/1e6)
        if len(payload) >= 12 and payload[:4] == b'NCMH':
            blen, = struct.unpack_from('<I', payload, 8)
            ntb[blen] += 1
            # NDP starts at wNdpIndex offset 10, then count 16-byte entries until 0,0.
            ndpidx, = struct.unpack_from('<I', payload, 12)
            if 0 < ndpidx + 8 <= len(payload):
                sig = payload[ndpidx:ndpidx+4]
                if sig in (b'NDP6', b'NCM0', b'NCM1'):
                    n = 0
                    for off in range(ndpidx+8, len(payload)-3, 4):
                        a,b = struct.unpack_from('<HH', payload, off)
                        if a == 0 and b == 0: break
                        if a and b: n += 1
                    ndp[n] += 1
            data_records += 1
print('records', records)
print('bulk_in_8_records', bulk_records)
print('submit_lengths', submits)
print('complete_lengths', completes)
print('max_outstanding_estimate', max_out)
if len(times) > 1:
    ds = [b-a for a,b in zip(times,times[1:]) if b>=a]
    print('completion_interval_us_median', statistics.median(ds)*1e6)
    print('completion_interval_us_p95', sorted(ds)[int(.95*(len(ds)-1))]*1e6)
print('ncm_ntb_block_lengths', ntb)
print('ndp_datagram_counts', ndp)
print('ncm_data_completions', data_records)
