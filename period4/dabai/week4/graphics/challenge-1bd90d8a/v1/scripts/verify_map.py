#!/usr/bin/env python3
"""verify_map.py — SVG 图元 data-value/data-row 与源 CSV 数值比对（防静默错误）。
用法: verify_map.py <figure.svg> <data.raw.csv> [--min-points 2]
"""
import csv, json, re, sys

def main(svg_p, csv_p, min_points=2):
    s = open(svg_p, encoding="utf-8").read()
    pairs = re.findall(r'data-value="([^"]+)"\s+data-row="(\d+)"', s)
    if not pairs:
        pairs = re.findall(r'data-row="(\d+)"\s+data-value="([^"]+)"', s)
        pairs = [(v, r) for r, v in pairs]
    rows = {i + 2: r for i, r in enumerate(csv.DictReader(open(csv_p, encoding="utf-8-sig")))}
    val_col = list(next(iter(rows.values())).keys())[1] if rows else "value"
    checked, bad = [], []
    for v, r in pairs:
        r = int(r)
        if r in rows:
            try:
                src = float(rows[r][val_col]); ok = abs(src - float(v)) < 1e-9
            except (ValueError, KeyError):
                ok = False
            checked.append({"row": r, "svg_value": v, "csv_value": rows[r][val_col], "match": ok})
            if not ok: bad.append(r)
    out = {"pass": len(checked) >= min_points and not bad, "n_checked": len(checked),
           "mismatch_rows": bad, "detail": checked[:10]}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)

if __name__ == "__main__":
    a = sys.argv[1:]
    mp = 2
    if "--min-points" in a:
        i = a.index("--min-points"); mp = int(a[i + 1]); del a[i:i + 2]
    main(a[0], a[1], mp)
