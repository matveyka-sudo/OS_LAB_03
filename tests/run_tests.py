#!/usr/bin/env python3
"""Independent known solutions, error cases and repeatability; no third-party packages."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BIN = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / 'build/OS_Lab3_Variant10'
records = []

def run(name, args, expected=0, solution=None):
    p = subprocess.run([str(BIN), *map(str, args)], text=True, capture_output=True, timeout=60)
    assert p.returncode == expected, (name, p.returncode, p.stdout, p.stderr)
    values = dict(line.split('=', 1) for line in p.stdout.splitlines() if '=' in line)
    if expected == 0 and '--help' not in args:
        assert values.get('verification') == 'PASS', (name, p.stdout)
        assert float(values['relative_residual']) <= 1e-10
        if solution is not None:
            for i, value in enumerate(solution, 1):
                assert math.isclose(float(values[f'x[{i}]']), value, rel_tol=1e-9, abs_tol=1e-9)
    records.append({'test': name, 'status': 'PASS', 'returncode': p.returncode,
                    'stdout': p.stdout, 'stderr': p.stderr})
    return values

cases = {
    'two': ('2\n2 1 5\n1 -1 1\n', [2, 1]),
    'three': ('3\n2 1 -1 8\n-3 -1 2 -11\n-2 1 2 -3\n', [2, 3, -1]),
    'pivot': ('3\n0 2 1 3\n1 -1 0 -1\n2 1 1 3\n', [1, 2, -1]),
    'one': ('1\n2 8\n', [4]),
    'scaled': ('2\n2e-100 1e-100 5e-100\n1e-100 -1e-100 1e-100\n', [2, 1]),
    'zero_rhs': ('2\n2 1 0\n1 3 0\n', [0, 0]),
}
for name, (data, solution) in cases.items():
    path = ROOT / 'tests' / f'{name}.txt'
    path.write_text(data)
    results = [run(f'{name}/p={p}', ['--file', path, '--threads', p], solution=solution)
               for p in (1, 2, 4, 8)]
    assert all([r[f'x[{i}]'] for i in range(1,len(solution)+1)] ==
               [results[0][f'x[{i}]'] for i in range(1,len(solution)+1)] for r in results)

with tempfile.TemporaryDirectory() as tmp:
    for name, data, code in [
        ('singular', '2\n1 2 3\n2 4 6\n', 2),
        ('inconsistent', '2\n1 2 3\n2 4 7\n', 2),
        ('zero', '2\n0 0 0\n0 0 0\n', 2),
        ('near_singular', '2\n1 1 2\n1 1.0000000000000002 2\n', 2),
        ('incomplete', '2\n1 2 3\n', 1),
        ('nan', '1\nnan 3\n', 1),
        ('inf', '1\n1 inf\n', 1),
        ('extra', '1\n1 2 extra\n', 1),
        ('bad_size', '99999999999999999999999\n', 1),
    ]:
        path = Path(tmp) / f'{name}.txt'
        path.write_text(data)
        for p in (1, 4):
            run(f'{name}/p={p}', ['--file', path, '--threads', p], code)
        if name in ('singular', 'inconsistent', 'near_singular'):
            (ROOT / 'tests' / path.name).write_text(data)
for n in (1, 2, 3, 7, 10, 31, 100, 300, 600, 1000):
    for p in (1, 2, 4, 8):
        run(f'generated/n={n}/p={p}', ['--size', n, '--threads', p])
for i, args in enumerate([
    [], ['--size', 10], ['--threads', 2], ['--size', 0, '--threads', 2],
    ['--size', -1, '--threads', 2], ['--size', '3x', '--threads', 2],
    ['--size', 10001, '--threads', 2], ['--size', 3, '--threads', 0],
    ['--size', 3, '--threads', 257], ['--size', 3, '--threads', 2, '--threads', 2],
    ['--size', 3, '--file', 'x', '--threads', 2], ['--file', '/nonexistent/lab3', '--threads', 1],
    ['--size', 3, '--threads', 2, '--demo', 0], ['--size', 3, '--threads', 2, '--unknown', 1],
    ['--size', 3, '--threads'], ['--help', '--size', 3],
]):
    run(f'bad_args/{i}', args, 1)
run('help', ['--help'])
for i in range(25):
    run(f'synchronization_stress/{i}', ['--size', 31, '--threads', 8])
output = ROOT / 'report/results' / (BIN.parent.name + '-tests.json')
output.write_text(json.dumps({'binary': str(BIN), 'passed': len(records), 'tests': records},
                             ensure_ascii=False, indent=2))
print(f'PASS: {len(records)} checks; {output}')
