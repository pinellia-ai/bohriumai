#!/usr/bin/env python3
"""数值审计: numeric_audit.py <docA.txt> <docB.txt> -> numeric_diff.csv (两文档数字集合比对)"""
import re, sys, csv
from collections import Counter
def nums(path):
    txt = open(path).read()
    return Counter(re.findall(r'\d+(?:\.\d+)?', txt))
a, b = nums(sys.argv[1]), nums(sys.argv[2])
rows = []
for k in sorted(set(a) | set(b), key=lambda x: -float(x) if x.replace('.', '', 1).isdigit() else 0):
    da, db = a.get(k, 0), b.get(k, 0)
    if da != db:
        rows.append([k, da, db, 'MATCH_FAIL' if (da and db) else 'ONE_SIDE'])
with open('numeric_diff.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['number', 'count_A', 'count_B', 'status']); w.writerows(rows)
print(f"numeric_diff.csv: {len(rows)} mismatches")
