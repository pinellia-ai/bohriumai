#!/usr/bin/env python3
"""numbering_check.py — 步骤编号与 spec 对照断言。
用法: numbering_check.py steps.tsv diagram_spec.json
断言:
 1 spec 步骤节点标签编号集合 == steps.tsv seq 集合（防编号错位/遗漏）
 2 spec 边方向允许拓扑序与 seq 数值顺序不冲突
 3 每个步骤节点有非空 source
"""
import csv, json, re, sys

def main(steps_p, spec_p):
    steps = {r["id"]: r for r in csv.DictReader(open(steps_p, encoding="utf-8"), delimiter="\t")}
    spec = json.load(open(spec_p, encoding="utf-8"))
    probs = []
    step_ids = set(steps)
    spec_steps = [n for n in spec.get("nodes", []) if n["id"] in step_ids]
    seq_set = {s["seq"].strip() for s in steps.values()}
    # 从 spec 节点 label 里提取编号
    label_seqs = set()
    for n in spec_steps:
        m = re.search(r"(\d+)", n.get("label", ""))
        if m: label_seqs.add(m.group(1))
        if not n.get("source"): probs.append(f"spec 节点 {n['id']} 缺 source")
    if seq_set and label_seqs != seq_set:
        probs.append(f"编号集合不一致: spec图={sorted(label_seqs)} 正文清单={sorted(seq_set)}")
    # 拓扑序检查：边 from->to 沿主序列应使 seq 递增（有并行/回流时允许例外，回流边标 dash）
    edges = [e for e in spec.get("edges", []) if e["from"] in step_ids and e["to"] in step_ids]
    def seq_of(nid): 
        try: return float(steps[nid]["seq"])
        except (ValueError, KeyError): return None
    for e in edges:
        a, b = seq_of(e["from"]), seq_of(e["to"])
        if a is not None and b is not None and a > b and not e.get("dash"):
            probs.append(f"边 {e['id']} 方向使编号倒退 {a}->{b}（若为回流请标 dash）")
    out = {"pass": not probs, "n_steps": len(step_ids), "spec_step_nodes": len(spec_steps), "problems": probs}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)

if __name__ == "__main__":
    main(*sys.argv[1:3])
