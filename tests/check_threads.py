#!/usr/bin/env python3
"""macOS ps snapshots of real processes during the separate demo pause."""
from pathlib import Path
import subprocess
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'report/results'
rows = []
for requested, n in [(1,100),(2,100),(4,100),(8,100),(8,3)]:
    proc = subprocess.Popen([str(ROOT/'build/OS_Lab3_Variant10'), '--size',str(n),
                             '--threads',str(requested),'--demo','2'],
                            text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    prefix = ''
    while 'demo_seconds=' not in prefix:
        line = proc.stdout.readline()
        assert line, 'Process exited before the demo pause'
        prefix += line
    result = subprocess.run(['ps','-M','-p',str(proc.pid)],text=True,capture_output=True,check=True)
    lines = [line for line in result.stdout.splitlines()[1:] if line.strip()]
    actual = min(requested,n)
    assert len(lines)==actual, result.stdout
    suffix, stderr = proc.communicate(timeout=10)
    assert proc.returncode == 0, stderr
    name = f'threads-p{requested}-n{n}.txt'
    (OUT/name).write_text(f'$ ps -M -p {proc.pid}\n'+result.stdout+'\nProgram output:\n'+prefix+suffix+stderr)
    rows.append({'n':n,'requested':requested,'observed':len(lines),'pid':proc.pid,'status':'PASS'})
(OUT/'thread-counts.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
