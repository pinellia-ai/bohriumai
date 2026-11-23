#!/usr/bin/env python3
"""统计检验: stat_tests.py <data.csv> <group_col> <value_col> (两组比较: 正态性/Welch t/Mann-Whitney + 效应量CI)"""
import csv, sys
try:
    from scipy import stats
    import numpy as np
except ImportError:
    print("scipy/numpy 不可用"); sys.exit(1)
rows = list(csv.DictReader(open(sys.argv[1])))
g, v = sys.argv[2], sys.argv[3]
groups = {}
for r in rows:
    groups.setdefault(r[g], []).append(float(r[v]))
keys = sorted(groups)
if len(keys) != 2:
    print(f"需要恰好两组, 实际: {keys}"); sys.exit(1)
a = np.array(groups[keys[0]]); b = np.array(groups[keys[1]])
na = stats.shapiro(a).pvalue; nb = stats.shapiro(b).pvalue
levene_p = stats.levene(a, b).pvalue
if na > 0.05 and nb > 0.05 and levene_p > 0.05:
    t, p = stats.ttest_ind(a, b, equal_var=False); name = 'Welch t-test'
else:
    t, p = stats.mannwhitneyu(a, b); name = 'Mann-Whitney U'
diff = b.mean() - a.mean()
se = (a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)) ** 0.5
ci = (diff - 1.96 * se, diff + 1.96 * se)
cohen = (diff) / ((a.std(ddof=1) ** 2 + b.std(ddof=1) ** 2) / 2) ** 0.5 if se else 0
print(f"前提: Shapiro p={na:.3f}/{nb:.3f}, Levene p={levene_p:.3f}")
print(f"检验: {name}, stat={t:.3f}, p={p:.4f}")
print(f"效应: 差值={diff:.3f}, 95%CI=({ci[0]:.3f},{ci[1]:.3f}), Cohen d={cohen:.2f}")
print(f"n: {len(a)}/{len(b)}")
