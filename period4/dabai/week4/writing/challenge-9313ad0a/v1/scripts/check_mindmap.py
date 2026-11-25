#!/usr/bin/env python3
"""check_mindmap.py — 思维导图机读结构与溯源校验。
用法: python3 check_mindmap.py <mindmap.md> <relations.json> <extract.json> [source-index.md]
退出码 0=全过, 1=有 fail。
"""
import json, re, sys

def main():
    if len(sys.argv) < 4:
        print("usage: check_mindmap.py <mindmap.md> <relations.json> <extract.json> [source-index.md]"); sys.exit(2)
    mm = open(sys.argv[1], encoding="utf-8").read()
    rel = json.load(open(sys.argv[2], encoding="utf-8"))
    ext = json.load(open(sys.argv[3], encoding="utf-8"))
    idx = open(sys.argv[4], encoding="utf-8").read() if len(sys.argv) > 4 else ""
    checks = []
    # 1) 节点规模与深度
    lines = [l for l in mm.splitlines() if l.startswith("#") or re.match(r"^\s*[-*]\s", l)]
    depth = 0
    for l in mm.splitlines():
        if l.startswith("#"):
            depth = max(depth, len(l) - len(l.lstrip("#")))
        else:
            m = re.match(r"^(\s*)[-*]\s", l)
            if m:
                indent = len(m.group(1)) // 2 + (0 if depth else 1)
                depth = max(depth, indent + (depth or 1))
    n_nodes = len(lines)
    checks.append({"item": "node_scale", "pass": n_nodes <= 60, "n_nodes": n_nodes})
    # 2) evidence 覆盖：节点行应含 [S-n|kind]
    node_lines = [l for l in mm.splitlines() if l.startswith("##") or re.match(r"^\s*[-*]\s", l)]
    no_ev = [l.strip()[:30] for l in node_lines if not re.search(r"\[S-\d+[|\]]", l) and "根节点" not in l and not l.startswith("# ")]
    ratio = 1 - (len(no_ev) / len(node_lines)) if node_lines else 1.0
    checks.append({"item": "evidence_coverage", "pass": ratio >= 0.95,
                   "ratio": round(ratio, 3), "missing": no_ev[:5]})
    # 3) S-n 有效性
    defined = set(re.findall(r"S-\d+", idx)) | set(e.get("source", "") for e in ext) if idx else set(e.get("source", "") for e in ext)
    defined = set(str(d).split("#")[0].split("|")[0] for d in defined if d)
    used = set(re.findall(r"S-\d+", mm))
    dangling = sorted(u for u in used if u not in defined and not any(u in d for d in defined))
    checks.append({"item": "evidence_valid", "pass": not dangling, "dangling": dangling})
    # 4) relations 的 from/to 在导图文本中出现
    bad = [r for r in rel if str(r.get("from")) not in mm or str(r.get("to")) not in mm]
    checks.append({"item": "relation_endpoints", "pass": not bad, "bad_count": len(bad)})
    # 5) 每条边有 evidence
    noev = [r for r in rel if not r.get("evidence")]
    checks.append({"item": "relation_evidence", "pass": not noev, "bad_count": len(noev)})
    result = {"checks": checks, "all_pass": all(c["pass"] for c in checks)}
    with open("checks.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["item"])
    sys.exit(0 if result["all_pass"] else 1)

if __name__ == "__main__":
    main()
