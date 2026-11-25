#!/usr/bin/env python3
"""check_structure.py — 论文结构机械检查（重复/衔接/超长段/锚文本真实性）。
用法: python3 check_structure.py <manuscript.md> [edit_plan.json]
  无 edit_plan 时输出重复/衔接候选；
  有 edit_plan 时额外校验每条动作的 target_anchor 在原文可检索。
退出码 0=全过, 1=有 fail（候选类不计入 fail）。
"""
import json, re, sys

def sentences(text):
    return [s.strip() for s in re.split(r"[。！？\n]", text) if len(s.strip()) >= 12]

def main():
    if len(sys.argv) < 2:
        print("usage: check_structure.py <manuscript.md> [edit_plan.json]"); sys.exit(2)
    text = open(sys.argv[1], encoding="utf-8").read()
    findings, checks = [], []
    # 1) 跨章节重复候选：8-gram 完全重复
    seen, dups = {}, []
    for s in sentences(text):
        key = re.sub(r"\s", "", s)[:40]
        if len(key) >= 16:
            if key in seen and seen[key] != s:
                dups.append(s[:30])
            seen[key] = seen.get(key) or s
        # 简化：同 key 出现≥2次计重复
    from collections import Counter
    cnt = Counter(re.sub(r"\s", "", s)[:40] for s in sentences(text) if len(s) >= 10)
    dups = [k[:30] for k, v in cnt.items() if v >= 2]
    findings.append({"type": "duplication_candidates", "items": dups})
    # 2) 超长段落
    longs = [p[:30] for p in text.split("\n\n") if len(re.sub(r"\s", "", p)) > 400]
    findings.append({"type": "long_paragraphs", "items": longs})
    # 3) 相邻节零词汇交集（线索）
    secs = re.split(r"\n#{1,3}\s+", text)
    weak_links = []
    for a, b in zip(secs, secs[1:]):
        sa = set(re.findall(r"[\u4e00-\u9fa5a-zA-Z]{2,}", a.splitlines()[-1] if a.splitlines() else ""))
        sb = set(re.findall(r"[\u4e00-\u9fa5a-zA-Z]{2,}", b.splitlines()[0] if b.splitlines() else ""))
        if sa and sb and not (sa & sb):
            weak_links.append([a.strip()[:12], b.strip()[:12]])
    findings.append({"type": "weak_transition_clues", "items": weak_links})
    # 4) edit_plan 锚文本真实性（硬校验）
    if len(sys.argv) > 2:
        plan = json.load(open(sys.argv[2], encoding="utf-8"))
        actions = plan if isinstance(plan, list) else plan.get("actions", [])
        bad_type, bad_anchor = [], []
        valid_types = {"move", "merge", "split", "narrow", "add-transition"}
        for a in actions:
            if a.get("type") not in valid_types:
                bad_type.append(a.get("id"))
            anc = a.get("target_anchor") or a.get("anchor") or ""
            anc = anc if isinstance(anc, str) else str(anc)
            core = anc[:20] if len(anc) > 20 else anc
            if core and core not in text:
                bad_anchor.append(a.get("id"))
        checks.append({"item": "edit_action_types", "pass": not bad_type, "bad": bad_type})
        checks.append({"item": "anchors_in_manuscript", "pass": not bad_anchor, "bad": bad_anchor})
    result = {"checks": checks, "findings": findings,
              "all_pass": all(c["pass"] for c in checks)}
    out = "structure-findings.json" if len(sys.argv) <= 2 else "checks.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    for fnd in findings:
        print(f"CAND {fnd['type']}: {len(fnd['items'])}")
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["item"])
    sys.exit(0 if result["all_pass"] else 1)

if __name__ == "__main__":
    main()
