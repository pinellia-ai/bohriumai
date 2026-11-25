#!/usr/bin/env python3
"""改动对照表校验器：校验润色 result.json 的 changes 与 polished_text 的对应性、
必填字段完整性、限定词强度漂移告警。用法：python3 polish_check.py result.json"""
import json, re, sys

TYPES = {"grammar", "punctuation", "terminology", "register", "semantics_guard", "format"}
REQUIRED = ["id", "locus", "original", "revised", "change_type", "reason"]
# 限定/强度词：改句中出现"更强"或"更弱"侧词且原句无，告警
STRONGER = {"strongly", "proves", "证明", "证实", "显著"}
WEAKER = {"may", "might", "suggest", "提示", "可能", "或许"}

def check(path):
    data = json.load(open(path, encoding="utf-8"))
    errs, warns = [], []
    for key in ("case_id", "status", "polished_text", "changes"):
        if key not in data:
            errs.append(f"result.json 缺字段: {key}")
    changes = data.get("changes", [])
    seen_ids = set()
    for i, c in enumerate(changes):
        for f in REQUIRED:
            if not c.get(f):
                errs.append(f"changes[{i}] 缺必填字段 {f}")
        if c.get("change_type") not in TYPES:
            errs.append(f"changes[{i}] change_type 非法: {c.get('change_type')}")
        if c["id"] in seen_ids:
            errs.append(f"changes[{i}] id 重复: {c['id']}")
        seen_ids.add(c["id"])
        # 限定强度漂移告警
        o, r = c.get("original", ""), c.get("revised", "")
        if not isinstance(o, str) or not isinstance(r, str):
            continue
        os_, rs = o.lower(), r.lower()
        for w in STRONGER:
            if w in rs and w not in os_:
                warns.append(f"{c['id']}: 改句引入更强限定词 '{w}'，核对是否削弱/加强了结论")
        for w in WEAKER:
            if w in rs and w not in os_:
                warns.append(f"{c['id']}: 改句引入更弱限定词 '{w}'，核对是否削弱了结论")
    by_type = {}
    for c in changes:
        by_type[c.get("change_type", "?")] = by_type.get(c.get("change_type", "?"), 0) + 1
    print(json.dumps({
        "ok": not errs, "errors": errs, "warnings": warns,
        "total_changes": len(changes), "by_type": by_type,
        "unverified_count": len(data.get("unverified", []))
    }, ensure_ascii=False, indent=2))
    return 0 if not errs else 1

if __name__ == "__main__":
    sys.exit(check(sys.argv[1]))
