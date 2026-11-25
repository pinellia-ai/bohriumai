#!/usr/bin/env python3
"""qa_check.py — 装置/流程四表质检：悬空端点、空来源、断头箭头。
用法: qa_check.py parts.tsv connections.tsv steps.tsv flows.tsv
"""
import csv, json, sys

def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))

def main(parts_p, conn_p, steps_p, flows_p):
    probs = []
    parts = read(parts_p)
    pids = {p["id"] for p in parts}
    steps = read(steps_p)
    sids = {s["id"] for s in steps}
    if not parts: probs.append("parts.tsv 为空")
    if not steps: probs.append("steps.tsv 为空")
    for p in parts:
        if not p.get("source_location", "").strip(): probs.append(f"部件 {p['id']} 缺来源")
    for c in read(conn_p):
        for k in ("from", "to"):
            if c.get(k) not in pids: probs.append(f"连接 {c['id']} 端点悬空 {k}={c.get(k)}")
        if not c.get("source_location", "").strip() and "inferred" not in c.get("source_location", ""):
            probs.append(f"连接 {c['id']} 缺来源（推断连接须标 inferred）")
    for s in steps:
        if not s.get("seq", "").strip(): probs.append(f"步骤 {s['id']} 缺 seq")
        if not s.get("source_location", "").strip(): probs.append(f"步骤 {s['id']} 缺来源")
    for f_ in read(flows_p):
        for k in ("from", "to"):
            if f_.get(k) not in pids and f_.get(k) not in sids:
                probs.append(f"流向 {f_['id']} 断头箭头 {k}={f_.get(k)}")
        if not f_.get("source_location", "").strip(): probs.append(f"流向 {f_['id']} 缺来源")
    out = {"pass": not probs, "n_parts": len(parts), "n_steps": len(steps), "problems": probs}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)

if __name__ == "__main__":
    main(*sys.argv[1:5])
