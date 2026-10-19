#!/usr/bin/env python3
"""Run in an otherwise idle session; never run benchmarks under a sanitizer."""
import csv
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'report/results'
BIN = ROOT / 'build/OS_Lab3_Variant10'
SIZES = [100, 300, 600, 1000]
THREADS = [1, 2, 4, 8]

def execute(n, p):
    proc = subprocess.run([str(BIN), '--size', str(n), '--threads', str(p)],
                          text=True, capture_output=True, check=True, timeout=60)
    fields = dict(s.split('=', 1) for s in proc.stdout.splitlines() if '=' in s)
    assert fields['verification'] == 'PASS'
    return fields

metadata = {
    'date_moscow': datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),
    'os': subprocess.check_output(['sw_vers'], text=True),
    'uname': platform.uname()._asdict(),
    'hardware': subprocess.check_output(['sysctl', 'machdep.cpu.brand_string', 'hw.memsize',
                                        'hw.physicalcpu', 'hw.logicalcpu'], text=True),
    'compiler': subprocess.check_output(['cc', '--version'], text=True),
    'build': 'CMake Release, -O2 -DNDEBUG; no sanitizer',
    'timer': 'CLOCK_MONOTONIC; entire gauss(), excludes pool creation/destruction, input and verification',
    'runs_per_pair': 7, 'warmups_per_pair': 1,
    'main_c_sha256': hashlib.sha256((ROOT/'main.c').read_bytes()).hexdigest(),
}
(OUT/'environment.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
for n in SIZES:
    for p in THREADS:
        execute(n, p)
rows = []
rng = random.Random(10)
with (OUT/'raw.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['n', 'p', 'repeat', 'time_seconds', 'relative_residual', 'max_solution_error'])
    writer.writeheader()
    for repeat in range(1, 8):
        pairs = [(n,p) for n in SIZES for p in THREADS]
        rng.shuffle(pairs)
        for n,p in pairs:
            result = execute(n,p)
            row = {'n':n,'p':p,'repeat':repeat,**{k:result[k] for k in
                   ['time_seconds','relative_residual','max_solution_error']}}
            writer.writerow(row)
            f.flush()
            rows.append(row)
        print(f'Finished repeat {repeat}/7', flush=True)
summary = []
for n in SIZES:
    times = {p: [float(r['time_seconds']) for r in rows if r['n']==n and r['p']==p] for p in THREADS}
    baseline = statistics.median(times[1])
    for p in THREADS:
        median = statistics.median(times[p])
        summary.append({'n':n,'p':p,'median_seconds':median,'min_seconds':min(times[p]),
                        'max_seconds':max(times[p]),'speedup':baseline/median,
                        'efficiency':baseline/median/p})
with (OUT/'summary.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(summary[0]))
    writer.writeheader()
    writer.writerows(summary)
print(json.dumps(summary, indent=2))
