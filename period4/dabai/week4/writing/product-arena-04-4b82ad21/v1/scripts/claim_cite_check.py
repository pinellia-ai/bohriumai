#!/usr/bin/env python3
"""引言成稿对账检查：校验 result.json 中引用绑定、空白推导链、贡献-证据对应是否闭合。
用法: python3 claim_cite_check.py result.json  （问题存在时退出码 1）"""
import json, sys

def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    errs = []
    for key in ("case_id", "status", "draft_text"):
        if key not in data:
            errs.append(f"缺字段: {key}")
    # 引用绑定：每条须有 locus 与 claim_snippet
    for i, b in enumerate(data.get("citation_binding", [])):
        if not b.get("locus") or not b.get("claim_snippet"):
            errs.append(f"citation_binding[{i}] 缺 locus/claim_snippet（引用空挂）")
        if b.get("metadata_verified") is not True:
            errs.append(f"citation_binding[{i}] 元数据未核对通过")
    # 空白链：每条 supports 非空且带位置痕迹（包含 @ 或 § 或 行/页 等线索）
    for i, g in enumerate(data.get("gap_chain", [])):
        sup = g.get("supports", [])
        if not sup:
            errs.append(f"gap_chain[{i}] 空白无文献支撑")
        elif not any(("@" in s) or ("§" in s) or any(ch.isdigit() for ch in s) for s in sup):
            errs.append(f"gap_chain[{i}] supports 缺原文位置")
    # 贡献对应：每条贡献须有 evidence
    weak = {w.get("item") for w in data.get("weak_claims", []) if isinstance(w, dict)}
    for i, c in enumerate(data.get("contributions", [])):
        if not c.get("evidence") and c.get("item") not in weak:
            errs.append(f"contributions[{i}] 无证据且未列入 weak_claims")
    print(json.dumps({"ok": not errs, "errors": errs,
                      "citations": len(data.get("citation_binding", [])),
                      "gaps": len(data.get("gap_chain", [])),
                      "contributions": len(data.get("contributions", []))},
                     ensure_ascii=False, indent=2))
    sys.exit(0 if not errs else 1)

if __name__ == "__main__":
    main()
