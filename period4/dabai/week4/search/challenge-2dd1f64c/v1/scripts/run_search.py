#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_search — 离线语料多轮检索执行器（真实可运行，仅标准库）。

用法：
  python3 run_search.py --input /input --workdir /app/work --query-plan /app/work/query_plan.json

query_plan.json 结构（由 Agent 在 Step 2 依据科研问题拆解生成）：
{
  "research_question": "...",
  "rounds": [
    {"round_id": "R1", "subquestion": "子问题1", "queries": ["查询式1", "查询式2"],
     "fields": ["title", "abstract", "keywords"], "topk": 20}
  ],
  "source_priority": ["crossref.json", "europepmc.json"]   // 可选，合并字段优先级
}

输出（全部落在 workdir）：
  records.jsonl      语料抽取的全部记录（source=file+field）
  search_log.jsonl   每轮 {round_id, query, fields, hit_count, hit_ids, hit_scores}
  candidates.jsonl   去重合并后的候选集（source + relevance_basis + 得分 + 命中轮次）
  load_log.json      材料装载日志
退出码：0 正常；2 无可用记录（语料为空）。
"""
import argparse, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/input")
    ap.add_argument("--workdir", default="/app/work")
    ap.add_argument("--query-plan", required=True)
    ap.add_argument("--glossary", default=None, help="可选：术语表 JSON {term:[变体]}")
    args = ap.parse_args()

    if not os.path.isdir(args.input):
        SL.write_json(os.path.join(args.workdir, "load_log.json"),
                      {"error": "input_dir_missing", "input": args.input})
        print("input dir missing", file=sys.stderr)
        return 2

    records, load_log = SL.load_records(args.input)
    SL.write_jsonl(os.path.join(args.workdir, "records.jsonl"), records)
    SL.write_json(os.path.join(args.workdir, "load_log.json"),
                  {"files": load_log, "record_count": len(records), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
    if not records:
        print("corpus empty: no records extracted", file=sys.stderr)
        return 2

    with open(args.query_plan, encoding="utf-8") as fh:
        plan = json.load(fh)
    glossary = None
    if args.glossary and os.path.exists(args.glossary):
        with open(args.glossary, encoding="utf-8") as fh:
            glossary = json.load(fh)

    idx = SL.Index(records)
    search_log, best = [], {}
    for rnd in plan.get("rounds", []):
        for q in rnd.get("queries", []):
            expanded = SL.expand_terms(q, glossary)
            qtext = " ".join(t for g in expanded for t in g)
            ranked, matched = idx.search(qtext, topk=int(rnd.get("topk", 20)))
            hit_ids = []
            for score, i in ranked:
                r = records[i]
                hit_ids.append(r["record_id"])
                entry = best.setdefault(r["record_id"], {
                    "record_id": r["record_id"], "fields": r.get("fields", {}),
                    "source": r.get("source"), "best_score": 0.0,
                    "hit_rounds": [], "matched_terms": set(), "matched_fields": [],
                    "relevance_basis": []})
                entry["best_score"] = round(max(entry["best_score"], float(score)), 3)
                if rnd["round_id"] not in entry["hit_rounds"]:
                    entry["hit_rounds"].append(rnd["round_id"])
                entry["matched_terms"] |= set(matched.get(i, []))
                if rnd.get("subquestion") and rnd["subquestion"] not in entry.get("subquestions", []):
                    entry.setdefault("subquestions", []).append(rnd["subquestion"])
            search_log.append({
                "round_id": rnd.get("round_id"), "subquestion": rnd.get("subquestion"),
                "query": q, "expanded_query": qtext, "fields": rnd.get("fields", []),
                "hit_count": len(ranked), "hit_ids": hit_ids, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})

    # 去重合并
    cands = sorted(best.values(), key=lambda x: -x["best_score"])
    for c in cands:
        c["matched_terms"] = sorted(c["matched_terms"])
        rb = []
        for r in records:
            if r["record_id"] == c["record_id"]:
                rb = SL.relevance_basis(r, c["matched_terms"])
                break
        c["relevance_basis"] = rb
    groups = SL.dedupe(records)
    dup_map = {}
    for g in groups:
        if len(g["members"]) > 1:
            ids = [m["record_id"] for m in g["members"]]
            keep = max(ids, key=lambda rid: best.get(rid, {}).get("best_score", 0))
            dup_map[keep] = {"merged": [i for i in ids if i != keep], "merge_basis": g["merge_basis"]}
    out = []
    for c in cands:
        c2 = dict(c)
        c2["dedupe"] = dup_map.get(c["record_id"], {"merged": [], "merge_basis": []})
        c2["duplicate_of"] = None
        out.append(c2)
    dup_ids = set()
    for keep, info in dup_map.items():
        dup_ids |= set(info["merged"])
    out = [c for c in out if c["record_id"] not in dup_ids]
    for i, c in enumerate(out):
        c["rank"] = i + 1

    SL.write_jsonl(os.path.join(args.workdir, "search_log.jsonl"), search_log)
    SL.write_jsonl(os.path.join(args.workdir, "candidates.jsonl"), out)
    print("rounds=%d queries=%d corpus=%d candidates=%d" %
          (len(plan.get("rounds", [])), len(search_log), len(records), len(out)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
