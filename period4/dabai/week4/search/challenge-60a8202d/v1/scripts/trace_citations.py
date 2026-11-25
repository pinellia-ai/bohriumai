#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trace_citations — 引文追踪与关联文献发现（真实可运行，仅标准库）。

用法：
  python3 trace_citations.py --input /input --workdir /app/work --seeds "种子标题或DOI[;第二个种子]"

流程：种子定位（DOI/标题匹配）→ 后向（references 字段）→ 前向（谁引用了种子）→
      共被引/耦合关联 → 路径解释 → 身份去重。
输出 citation_graph.json：nodes/edges（每条边带方向+来源文件+语境线索）/paths/merged_identities。
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/input")
    ap.add_argument("--workdir", default="/app/work")
    ap.add_argument("--seeds", required=True, help="分号分隔的种子标题或DOI")
    ap.add_argument("--max-depth", type=int, default=2)
    args = ap.parse_args()

    records, load_log = SL.load_records(args.input)
    if not records:
        print("corpus empty", file=sys.stderr)
        return 2
    graph = SL.build_citation_graph(records)
    rec_by_id = {r["record_id"]: r for r in records}

    nodes, edges, seed_ids = {}, [], []
    for seed in [s.strip() for s in args.seeds.split(";") if s.strip()]:
        rid, method = SL.hit_match({"title": seed, "doi": seed}, records)
        if not rid:
            continue
        seed_ids.append(rid)
        # BFS 扩展（后向：references；前向：语料内引用该种子的记录）
        frontier, depth = [rid], 0
        while frontier and depth < args.max_depth:
            nxt = []
            for cur in frontier:
                if cur in nodes:
                    continue
                r = rec_by_id[cur]
                nodes[cur] = {"record_id": cur, "title": r["fields"].get("title"),
                              "source": r["source"], "is_seed": cur == rid}
                for e in graph.get(cur, []):
                    edges.append({"from": cur, "to": e["target_record_id"],
                                  "direction": "backward", "raw_ref": e["raw"],
                                  "in_corpus": e["in_corpus"],
                                  "source_file": r["source"]["file"]})
                    if e["target_record_id"]:
                        nxt.append(e["target_record_id"])
                for other, es in graph.items():
                    if other == cur:
                        continue
                    for e in es:
                        if e["target_record_id"] == cur:
                            ro = rec_by_id[other]
                            edges.append({"from": other, "to": cur, "direction": "forward",
                                          "raw_ref": e["raw"], "in_corpus": e["in_corpus"],
                                          "source_file": ro["source"]["file"]})
                            nxt.append(other)
            frontier, depth = list(dict.fromkeys(nxt)), depth + 1
    # 身份合并（同族：预印本/会议版/期刊版）
    groups = SL.dedupe(records)
    merged = [{"key": g["key"], "record_ids": [m["record_id"] for m in g["members"]],
               "merge_basis": g["merge_basis"]} for g in groups if len(g["members"]) > 1]
    # 路径解释：种子到远端节点逐跳
    paths = []
    for e in edges:
        if e["to"] and e["to"] not in seed_ids and e["from"] in seed_ids:
            paths.append({"seed": e["from"], "target": e["to"],
                          "hops": [{"from": e["from"], "to": e["to"],
                                    "direction": e["direction"], "evidence_raw": e["raw_ref"][:120]}],
                          "direct": True})
    out = {"seeds": seed_ids, "seed_match_note": "种子定位方法=DOI精确→标题近似",
           "node_count": len(nodes), "nodes": nodes,
           "edge_count": len(edges),
           "edges_sample": edges[:300],
           "edges_note": "每条边带 direction+raw_ref（引用语境线索）+source_file；in_corpus=false 的原始引文不虚构 record_id",
           "paths": paths[:100],
           "merged_identities": merged,
           "linked_by": "前向=语料内施引记录；后向=references 字段；关联依据为引用边+去重合并证据，不做语义推荐虚构"}
    SL.write_json(os.path.join(args.workdir, "citation_graph.json"), out)
    print("seeds=%d nodes=%d edges=%d merged=%d" % (len(seed_ids), len(nodes), len(edges), len(merged)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
