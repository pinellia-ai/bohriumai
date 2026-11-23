#!/usr/bin/env python3
"""CSV 画像: csv_profile.py <data.csv> [key_column] -> profile.json (行列/空值/重复键/数值列统计)"""
import csv, json, sys
from collections import Counter
rows = list(csv.DictReader(open(sys.argv[1])))
key = sys.argv[2] if len(sys.argv) > 2 else None
cols = list(rows[0].keys()) if rows else []
nulls = {c: sum(1 for r in rows if not (r.get(c) or '').strip()) for c in cols}
num_stats = {}
for c in cols:
    vals = []
    for r in rows:
        try: vals.append(float(r[c]))
        except: pass
    if len(vals) > len(rows) * 0.5:
        vals.sort()
        num_stats[c] = {"n": len(vals), "min": vals[0], "max": vals[-1],
                        "mean": round(sum(vals) / len(vals), 4)}
dup = Counter(r.get(key, '') for r in rows if key) if key else None
prof = {"file": sys.argv[1], "rows": len(rows), "cols": cols, "null_counts": nulls,
        "numeric_stats": num_stats,
        "duplicate_keys": {k: v for k, v in (dup or {}).items() if v > 1} if dup else None}
json.dump(prof, open('profile.json', 'w'), ensure_ascii=False, indent=1)
print(f"profile.json: {len(rows)} rows, {len(cols)} cols, dups={len(prof['duplicate_keys'] or {})}")
