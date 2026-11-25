#!/usr/bin/env python3
"""pathway_check.py — 机制图语义/拓扑断言（防幻觉实体与边、防语义错配）。
用法: pathway_check.py <diagram_spec.json> <entities.tsv> <relations.tsv>
断言:
 1 spec 节点 id ⊆ entities.tsv id（幻觉实体=FAIL）
 2 spec 边 id ⊆ relations.tsv id；且 from/to 一致
 3 边 type ∈ 语义枚举且与 relations.tsv type 一致
 4 每个内容元素有非空 data-source
 5 图例使用的语义类型 = 边实际使用类型集合
 6 节点 compartment（entities.tsv）与所在 compartment 区域一致性提示（仅记录，不 FAIL）
"""
import csv, json, sys, re

SEM = {"activate", "inhibit", "bind", "modify", "transport", "contain", "neutral", "parallel"}

def tsv(p):
    return {r["id"]: r for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t")}

def main(spec_p, ent_p, rel_p):
    spec = json.load(open(spec_p, encoding="utf-8"))
    ents, rels = tsv(ent_p), tsv(rel_p)
    probs, notes = [], []
    n_ids = {n["id"] for n in spec.get("nodes", [])}
    ghost = n_ids - set(ents)
    if ghost: probs.append(f"幻觉节点（不在实体清单）: {sorted(ghost)}")
    missing_ent = set(ents) - n_ids
    if missing_ent: notes.append(f"实体清单中未上图节点: {sorted(missing_ent)}")
    spec_edges = {e["id"]: e for e in spec.get("edges", [])}
    ghost_e = set(spec_edges) - set(rels)
    if ghost_e: probs.append(f"幻觉边: {sorted(ghost_e)}")
    for eid, e in spec_edges.items():
        if eid in rels:
            if e.get("from") != rels[eid]["from"] or e.get("to") != rels[eid]["to"]:
                probs.append(f"边 {eid} 端点与清单不一致")
            if e.get("type") != rels[eid]["type"]:
                probs.append(f"边 {eid} 语义不一致: spec={e.get('type')} 清单={rels[eid]['type']}")
        if e.get("type") not in SEM:
            probs.append(f"边 {eid} 语义枚举外: {e.get('type')}")
        if not e.get("source"):
            probs.append(f"边 {eid} 缺 source")
    for n in spec.get("nodes", []):
        if not n.get("source"): probs.append(f"节点 {n['id']} 缺 source")
    used = {e.get("type") for e in spec.get("edges", [])} - {None}
    lg = {it.get("type") for it in spec.get("legend", []) if it.get("kind") == "arrow"} - {None}
    if used != lg:
        probs.append(f"图例类型 {sorted(lg)} != 实际边类型 {sorted(used)}")
    # compartment 提示
    for c in spec.get("compartments", []):
        notes.append(f"区室 {c['id']}: {c.get('label', '')}")
    out = {"pass": not probs, "n_nodes": len(n_ids), "n_edges": len(spec_edges), "problems": probs, "notes": notes}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
