#!/usr/bin/env python3
"""Receive Zen3's read-only status datagrams and feed chrony SHM."""
import ctypes, json, socket, time

LISTEN = ("0.0.0.0", 40123)
SHM_KEY = 0x4e545030
MAX_AGE = 10.0
MAX_OFFSET = 5.0
MARKER = "zen3-gnss-v1-7f3c9a"

class ShmTime(ctypes.Structure):
    _fields_=[("mode",ctypes.c_int),("count",ctypes.c_int),
      # raspi2 runs a 32-bit Python, while chrony uses 64-bit time_t.
      ("clock_sec",ctypes.c_int64),("clock_usec",ctypes.c_int),
      ("receive_sec",ctypes.c_int64),("receive_usec",ctypes.c_int),
      ("leap",ctypes.c_int),("precision",ctypes.c_int),
      ("nsamples",ctypes.c_int),("valid",ctypes.c_int)]

def open_shm():
    libc=ctypes.CDLL(None, use_errno=True)
    libc.shmget.argtypes=[ctypes.c_int,ctypes.c_size_t,ctypes.c_int]
    libc.shmat.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_int]
    shmid=libc.shmget(SHM_KEY, ctypes.sizeof(ShmTime), 0o666)
    if shmid < 0: raise OSError(ctypes.get_errno(), "shmget")
    addr=libc.shmat(shmid,None,0)
    if addr == -1: raise OSError(ctypes.get_errno(), "shmat")
    return ShmTime.from_address(addr)

def main():
    shm=open_shm()
    # A restarted feeder must not resurrect the previous process's sample.
    shm.valid = 0
    rx=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
    rx.settimeout(1.0)
    rx.bind(LISTEN)
    last_valid = 0.0
    invalidated = False
    while True:
        try:
            data, peer = rx.recvfrom(4096)
        except socket.timeout:
            # Do not let a trusted but stale SHM sample keep chrony selected.
            if last_valid and time.time() - last_valid > MAX_AGE and not invalidated:
                shm.valid = 0
                invalidated = True
                print("invalidate reason=packet-timeout age=%.1f" % (time.time() - last_valid), flush=True)
            continue
        received=time.time()
        try:
            m=json.loads(data.decode("ascii"))
            if m.get("marker") != MARKER or m.get("v") != 1: continue
            age=float(m["fix_age_s"]); gnss=float(m["utc_unix_s"])
            offset=gnss-received
            valid=bool(m["valid"]) and age <= MAX_AGE and int(m["satellites"]) >= 4
            valid=valid and abs(offset) <= MAX_OFFSET
        except (ValueError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not valid:
            print("reject peer=%s age=%.1f offset=%.3f" % (peer[0], age, offset), flush=True)
            continue
        try:
            sec=int(gnss); usec=int((gnss-sec)*1_000_000)
            shm.valid=0; shm.count += 1
            shm.clock_sec=sec; shm.clock_usec=usec
            shm.receive_sec=int(received); shm.receive_usec=int((received-int(received))*1_000_000)
            shm.leap=0; shm.precision=-20; shm.nsamples=1; shm.valid=1
            last_valid = received
            invalidated = False
            print("accept peer=%s offset=%.4f age=%.2f sat=%s cn0=%s" %
                  (peer[0], offset, age, m.get("satellites"), m.get("mean_cn0")), flush=True)
        except OSError as e:
            print("chrony SHM unavailable: %s" % e, flush=True)

if __name__ == "__main__": main()
