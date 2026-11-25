#!/usr/bin/env python3
"""qa_extract.py — Step1 抽取质检：悬空引用、空来源、数值格式。
用法: qa_extract.py entities.tsv relations.tsv datamap.tsv
entities.tsv 列: id,name,type,attrs,source_location
relations.tsv 列: id,from,to,type,evidence_text,source_location
datamap.tsv   列: item,value,unit,source_location
"""
import csv, json, re, sys

def read_tsv(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def main(ent_p, rel_p, dm_p):
    problems = []
    ents = read_tsv(ent_p)
    ids = {e["id"] for e in ents}
    if not ents: problems.append("entities.tsv 为空")
    for e in ents:
        if not e.get("source_location", "").strip():
            problems.append(f"实体 {e['id']} 缺 source_location")
    for r in read_tsv(rel_p):
        if r.get("from") not in ids: problems.append(f"边 {r['id']} from 悬空: {r.get('from')}")
        if r.get("to") not in ids: problems.append(f"边 {r['id']} to 悬空: {r.get('to')}")
        if r.get("type") not in ("activate", "inhibit", "bind", "modify", "transport", "contain", "parallel", "neutral"):
            problems.append(f"边 {r['id']} type 未定义: {r.get('type')}")
        if not r.get("source_location", "").strip() and r.get("type") != "neutral":
            problems.append(f"边 {r['id']} 缺 source_location")
    for d in read_tsv(dm_p):
        if d.get("value", "").strip() and not re.match(r"^-?[\d.,eE+]+%?$", d["value"].strip()):
            problems.append(f"数值 {d['item']} 非纯数值: {d['value']}")
        if not d.get("source_location", "").strip():
            problems.append(f"数值 {d['item']} 缺 source_location")
    out = {"pass": not problems, "n_entities": len(ents), "problems": problems}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
