#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quality_check — 文献研究质量评价的维度对账与证据定位校验（真实可运行，仅标准库）。

用法：
  python3 quality_check.py --eval /app/work/evaluations.jsonl --workdir /app/work

evaluations.jsonl 由 Agent 逐条填写（每行=一篇文献的一个维度判定）：
  {"record_id":"R0001","dimension":"sample","verdict":"present|absent|unclear|not_evaluable",
   "quote":"原文逐字摘录","locator":{"file":"...","field":"P003"},"bias_risk":"low|moderate|high|insufficient",
   "reason":"..."}

输出 quality.json：维度覆盖矩阵、逐条证据回查（quote 是否真出现在语料对应文件）——
quote 对不上原文的判定自动降级为 not_evaluable+待复核；汇总分级与复核入口。
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

DIMENSIONS = ["design", "sample", "measurement", "statistics", "reporting_completeness"]
BIAS_DOMAINS = ["selection", "performance", "detection", "attrition", "reporting"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", required=True)
    ap.add_argument("--workdir", default="/app/work")
    args = ap.parse_args()
    evals = SL.load_jsonl(args.eval)
    if not evals:
        print("no evaluations", file=sys.stderr)
        return 2

    records = []
    rp = os.path.join(args.workdir, "records.jsonl")
    if os.path.exists(rp):
        records = SL.load_jsonl(rp)
    text_by_file = {}
    for r in records:
        f = r["source"]["file"]
        text_by_file.setdefault(f, []).append(r.get("text", ""))

    checked, downgraded = [], []
    for e in evals:
        quote = e.get("quote", "").strip()
        loc = e.get("locator", {}) or {}
        verify = {"quote_verified": False, "method": "quote_in_corpus_text"}
        src_text = " ".join(text_by_file.get(loc.get("file", ""), [])) or \
                   " ".join(t for ts in text_by_file.values() for t in ts)
        if quote and SL.norm_text(quote)[:120] in SL.norm_text(src_text):
            verify["quote_verified"] = True
        elif quote:
            verify["method"] = "quote_not_found_in_corpus"
            downgraded.append({"record_id": e.get("record_id"), "dimension": e.get("dimension"),
                               "note": "quote 未能在语料中逐字回查：判定降级为 not_evaluable+待复核，不得保留原等级"})
            e = dict(e)
            e["verdict"] = "not_evaluable"
            e["bias_risk"] = "insufficient"
        if e.get("verdict") == "not_evaluable" and not e.get("reason", "").strip():
            downgraded.append({"record_id": e.get("record_id"), "dimension": e.get("dimension"),
                               "note": "not_evaluable 未写明缺什么证据"})
        checked.append(dict(e, verify=verify))

    # 覆盖矩阵：文献×维度
    matrix = {}
    for e in checked:
        matrix.setdefault(e.get("record_id"), {})[e.get("dimension")] = e.get("verdict")
    missing_dims = [{"record_id": rid, "missing_dimensions": [d for d in DIMENSIONS if d not in dims]}
                    for rid, dims in matrix.items()
                    if len([d for d in DIMENSIONS if d in dims]) < len(DIMENSIONS)]

    risk_counts = {}
    for e in checked:
        br = e.get("bias_risk")
        if br:
            risk_counts[br] = risk_counts.get(br, 0) + 1
    # 分级阈值（显式）：无 insufficient 且无 high → low；无 insufficient → moderate；否则 graded_uncertain
    ins = risk_counts.get("insufficient", 0)
    grade = ("low" if ins == 0 and risk_counts.get("high", 0) == 0
             else "moderate" if ins == 0 else "graded_uncertain")

    out = {"evaluations": checked,
           "dimension_matrix": matrix,
           "missing_dimensions": missing_dims,
           "bias_risk_counts": risk_counts,
           "overall_grade": grade,
           "grade_thresholds": "high条目=0且insufficient=0→low；insufficient=0→moderate；否则 graded_uncertain（明示证据不足）",
           "downgraded": downgraded,
           "human_review_entry": "每条 verdict=unclear/not_evaluable 的判定进入人工复核清单；人工改动沉淀回判据配置",
           "boundary_note": "不替代同行评审/事实核验/临床决策；判定只到证据可回查的位置为止",
           "dimensions_expected": DIMENSIONS, "bias_domains_expected": BIAS_DOMAINS}
    SL.write_json(os.path.join(args.workdir, "quality.json"), out)
    print("evals=%d verified=%d downgraded=%d grade=%s" %
          (len(checked), sum(1 for c in checked if c["verify"]["quote_verified"]),
           len(downgraded), grade))
    return 0

if __name__ == "__main__":
    sys.exit(main())
