#!/usr/bin/env python3
"""snapshot.py — 源数据快照：原样副本 + sha256 + 缺失计数。
用法: snapshot.py <data.csv> <workdir>
"""
import csv, hashlib, json, shutil, sys, os

def main(src, workdir):
    os.makedirs(workdir, exist_ok=True)
    dst = os.path.join(workdir, "data.raw.csv")
    shutil.copyfile(src, dst)
    raw = open(dst, "rb").read()
    with open(dst, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys()) if rows else []
    missing = {c: sum(1 for r in rows if r[c] is None or str(r[c]).strip() == "") for c in cols}
    snap = {"source": os.path.abspath(src), "rows": len(rows), "columns": cols,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "file_sha256": hashlib.sha256(open(src, "rb").read()).hexdigest(),
            "missing_cells": {k: v for k, v in missing.items() if v},
            "total_missing": sum(missing.values())}
    out = os.path.join(workdir, "snapshot.json")
    json.dump(snap, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(snap, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
