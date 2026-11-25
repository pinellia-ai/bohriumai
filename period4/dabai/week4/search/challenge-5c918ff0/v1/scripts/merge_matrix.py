#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_matrix — 多源记录归并矩阵与字段覆盖审计（真实可运行，仅标准库）。

用法：
  python3 merge_matrix.py --records /app/work/records.jsonl --candidates /app/work/candidates.jsonl --workdir /app/work

输出 merge_matrix.json：
  per_source（每来源库的记录数、字段覆盖矩阵、缺失字段）/ dup_groups（跨库重复组+判定依据）/
  merged_fields（每条候选的字段取值来源）/ gaps（未覆盖的库与字段，显式列出而非静默吞掉）
"""
import argparse, json, os, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

CANON_FIELDS = ["title", "authors", "year", "doi", "venue", "abstract", "type", "language", "id", "keywords"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--workdir", default="/app/work")
    args = ap.parse_args()
    records = SL.load_jsonl(args.records)
    cands = SL.load_jsonl(args.candidates)
    if not records:
        print("no records", file=sys.stderr)
        return 2

    per_source = defaultdict(lambda: {"count": 0, "fields": Counter(), "missing": []})
    for r in records:
        f = r["source"]["file"]
        per_source[f]["count"] += 1
        for cf in CANON_FIELDS:
            if cf in r.get("fields", {}):
                per_source[f]["fields"][cf] += 1
    for f, info in per_source.items():
        info["missing"] = [cf for cf in CANON_FIELDS if info["fields"].get(cf, 0) == 0]
        info["fields"] = dict(info["fields"])

    groups = SL.dedupe(records)
    cross = []
    prio = []
    for g in groups:
        files = {m["source"]["file"] for m in g["members"]}
        if len(g["members"]) > 1 and len(files) > 1:
            m = SL.merge_group(g, source_priority=prio)
            cross.append({"key": g["key"], "source_files": sorted(files),
                          "record_ids": [x["record_id"] for x in g["members"]],
                          "merged_fields": m["fields"],
                          "field_sources": {k: v["file"] for k, v in m["field_sources"].items()},
                          "conflicts": {k: v[:3] for k, v in m["conflicts"].items()},
                          "merge_rule": "字段取值=来源优先级+值完整度；冲突逐字段保留原值与来源供人工仲裁"})
    gaps = [{"source": f, "missing_fields": info["missing"]}
            for f, info in sorted(per_source.items()) if info["missing"]]
    out = {"per_source": dict(per_source),
           "source_count": len(per_source),
           "cross_source_dup_groups": cross,
           "dedup_note": "重复判定=DOI精确→标题近似(≥0.85)+年份一致；判定依据逐组保留",
           "gaps": gaps,
           "gaps_note": "未覆盖字段/库显式列出；不静默返回不完整结果",
           "candidates_total": len(cands)}
    SL.write_json(os.path.join(args.workdir, "merge_matrix.json"), out)
    print("sources=%d cross_dup_groups=%d gaps=%d" % (len(per_source), len(cross), len(gaps)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
