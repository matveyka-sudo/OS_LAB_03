#!/usr/bin/env python3
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'report/results'
with (OUT/'summary.csv').open() as f:
    rows = list(csv.DictReader(f))
plt.rcParams.update({'font.size':11, 'font.family':'DejaVu Sans'})
for field, name, title, ylabel in [
    ('median_seconds','time','Время решения системы','Время, с'),
    ('speedup','speedup','Ускорение метода Гаусса','S(p) = T(1) / T(p)'),
    ('efficiency','efficiency','Эффективность метода Гаусса','E(p) = S(p) / p'),
]:
    fig, ax = plt.subplots(figsize=(7.4,4.5),layout='constrained')
    for n in [100,300,600,1000]:
        subset = [r for r in rows if int(r['n'])==n]
        ax.plot([int(r['p']) for r in subset],[float(r[field]) for r in subset],
                marker='o',linewidth=1.8,label=f'n = {n}')
    if field == 'median_seconds': ax.set_yscale('log')
    if field == 'efficiency': ax.axhline(1,color='gray',linestyle='--',linewidth=0.8)
    ax.set(xlabel='Количество потоков p (включая main)',ylabel=ylabel,title=title,xticks=[1,2,4,8])
    ax.grid(True,alpha=0.25)
    ax.legend()
    fig.savefig(OUT/f'{name}.png',dpi=180)
    plt.close(fig)
print('Created time.png, speedup.png, efficiency.png')
