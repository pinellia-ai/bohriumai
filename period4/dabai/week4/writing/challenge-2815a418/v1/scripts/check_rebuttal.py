#!/usr/bin/env python3
"""check_rebuttal.py — 回复信/修订稿/改动台账三向对账。
用法: python3 check_rebuttal.py <revised.md> <letter.md> <changes.json> [original.md]
退出码 0=全过, 1=有 fail。
"""
import json, re, sys

def main():
    if len(sys.argv) < 4:
        print("usage: check_rebuttal.py <revised.md> <letter.md> <changes.json> [original.md]"); sys.exit(2)
    revised = open(sys.argv[1], encoding="utf-8").read()
    letter = open(sys.argv[2], encoding="utf-8").read()
    changes = json.load(open(sys.argv[3], encoding="utf-8"))
    original = open(sys.argv[4], encoding="utf-8").read() if len(sys.argv) > 4 else None
    checks = []
    # 1) letter 中每个锚 ID 在修订稿中存在
    anchors = set(re.findall(r"CHG-\d+", letter))
    missing = sorted(a for a in anchors if a not in revised)
    checks.append({"item": "anchor_in_revised", "pass": not missing, "missing": missing})
    # 2) changes.json 锚在修订稿中存在，before 在原稿中可检索
    bad_before, bad_anchor = [], []
    for c in changes:
        cid = f"CHG-{c.get('n')}"
        if c.get("type") == "todo" or str(c.get("after", "")).startswith("TODO-"):
            pass  # TODO 型台账项只要求登记，不要求正文锚
        elif cid not in revised:
            bad_anchor.append(cid)
        before = c.get("before", "")
        if original and before and before not in original:
            bad_before.append(cid)
    checks.append({"item": "anchor_registered", "pass": not bad_anchor, "missing": bad_anchor})
    checks.append({"item": "before_in_original", "pass": not bad_before, "missing": bad_before})
    # 3) TODO-E 均在 changes.json 或 evidence 引用中（letter/revised 中出现则需台账登记）
    todos = set(re.findall(r"TODO-E(\d+)", revised + letter))
    registered = {str(c.get("n")) for c in changes}
    untracked = sorted(t for t in todos if t not in registered)
    checks.append({"item": "todo_evidence_tracked", "pass": not untracked, "missing": untracked})
    # 4) 语气违例粗检
    bad_tone = [w for w in ["显然你没", "完全错误", "荒谬", " guaranteed"] if w in letter]
    checks.append({"item": "tone_violations", "pass": not bad_tone, "found": bad_tone})
    result = {"checks": checks, "all_pass": all(c["pass"] for c in checks)}
    with open("checks.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["item"])
    sys.exit(0 if result["all_pass"] else 1)

if __name__ == "__main__":
    main()
