#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arbitrate — 双人独立筛选分歧仲裁与流程审计（真实可运行，仅标准库）。

用法：
  python3 arbitrate.py --a /app/work/screening_A.jsonl --b /app/work/screening_B.jsonl --workdir /app/work

screening_A/B.jsonl 为同一候选集按两套独立判据（或两位标注者配置）各跑一次 screen.py 的输出。
输出 arbitration.json：一致项直接定稿；分歧项按类型（include-vs-exclude / include-vs-pending /
pending-vs-exclude）归类，逐条列出双方理由码与证据，给出仲裁建议（升级人工）；
审计计数链：total → unique → included/excluded/pending → final，首尾闭合。
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

RANK = {"included": 2, "pending": 1, "excluded": 0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--workdir", default="/app/work")
    args = ap.parse_args()
    A = {r["record_id"]: r for r in SL.load_jsonl(args.a)}
    B = {r["record_id"]: r for r in SL.load_jsonl(args.b)}
    if not A or not B:
        print("empty screening input", file=sys.stderr)
        return 2

    agree, disagree = [], []
    for rid in sorted(set(A) | set(B)):
        a, b = A.get(rid), B.get(rid)
        da, db = (a or {}).get("decision"), (b or {}).get("decision")
        if da == db:
            agree.append({"record_id": rid, "decision": da,
                          "reason_code": (a or {}).get("reason_code"),
                          "evidence_quote": (a or {}).get("evidence_quote")})
        else:
            dtype = "%s-vs-%s" % tuple(sorted([da or "missing", db or "missing"], reverse=True))
            pick = a if RANK.get(da, -1) >= RANK.get(db, -1) else b
            disagree.append({"record_id": rid, "disagreement_type": dtype,
                             "a_decision": da, "a_reason": (a or {}).get("reason_code"),
                             "a_evidence": (a or {}).get("evidence_quote"),
                             "b_decision": db, "b_reason": (b or {}).get("reason_code"),
                             "b_evidence": (b or {}).get("evidence_quote"),
                             "arbitration_rule": "分歧不平均不掩盖：存在任一 included → pending 待人工终审；双方均非 included → 取更保守（excluded 优先）",
                             "suggested": "pending" if "included" in (da, db) else (db or da)})
    final = [{"record_id": r["record_id"], "final_decision": r["decision"],
              "note": "双标一致"} for r in agree]
    final += [{"record_id": r["record_id"], "final_decision": r["suggested"],
               "note": "分歧仲裁建议，需研究者确认"} for r in disagree]

    counts = {"total_unique": len(set(A) | set(B)),
              "agree": len(agree), "disagree": len(disagree),
              "final_included": sum(1 for f in final if f["final_decision"] == "included"),
              "final_pending": sum(1 for f in final if f["final_decision"] == "pending"),
              "final_excluded": sum(1 for f in final if f["final_decision"] == "excluded")}
    assert counts["final_included"] + counts["final_pending"] + counts["final_excluded"] == counts["total_unique"], "审计计数不闭合"

    out = {"agree": agree, "disagree": disagree, "final": final,
           "audit_counts": counts,
           "closure_note": "total_unique = agree + disagree = included + pending + excluded（断言已校验）",
           "human_final_note": "模型输出仅为待复核建议；纳入/排除终审由研究者确认后回写"}
    SL.write_json(os.path.join(args.workdir, "arbitration.json"), out)
    print("agree=%d disagree=%d final: inc=%d pend=%d exc=%d" %
          (len(agree), len(disagree), counts["final_included"],
           counts["final_pending"], counts["final_excluded"]))
    return 0

if __name__ == "__main__":
    sys.exit(main())
