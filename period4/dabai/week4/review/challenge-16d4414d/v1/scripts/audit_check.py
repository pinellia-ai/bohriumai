#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_check.py — 论文逻辑与论证审查 result.json / claims / alignment / findings 验收器。

用法: python3 audit_check.py /app/output/result.json [--workdir /app/output]
验收（全过退出码 0；任一失败退出码 1）:
  1. result.json 顶层字段齐全; status 合法; partial/failed 有界限; case_id 非空
  2. claims.json 每条有 claim_id/locator/quote/claim_source; claim_source 枚举合法
  3. author_claim 全部出现在 alignment.csv（对齐全覆盖）
  4. alignment verdict ∈ {supported, overclaimed, no_evidence, undeterminable}
  5. findings 每条八件齐全且 location.quote 非空; recommendation 非空话
  6. major/minor 的 evidence 含影响主结论说明
  7. coverage 六类键齐全
"""
import argparse, csv, json, os, sys

CATEGORIES = ["claim_evidence_alignment", "reasoning_chain", "cross_section_consistency",
              "fact_verification", "citation_support", "academic_norm"]
CLAIM_SOURCES = {"author_claim", "cited_view", "hypothetical", "ambiguous"}
VERDICTS = {"supported", "overclaimed", "no_evidence", "undeterminable"}
ISSUE_TYPES = {"fact_error", "insufficient_evidence", "norm_issue", "suggestion", "pending_review"}
SEVERITIES = {"major", "minor", "suggestion", "pending_review"}
REQUIRED_TOP = ["case_id", "status", "deliverables", "review_report",
                "evidence_and_boundary", "coverage", "sources", "uncertainty_notes"]
FINDING_FIELDS = ["id", "category", "location", "issue_type", "severity", "evidence", "recommendation"]
VAGUE_RE = ("建议加强逻辑", "建议补充论证", "逻辑较清晰", "论证较充分")

def read_rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_json")
    ap.add_argument("--workdir", default=None)
    a = ap.parse_args()
    w = a.workdir or os.path.dirname(os.path.abspath(a.result_json))
    fails = []

    try:
        res = json.load(open(a.result_json, encoding="utf-8"))
    except Exception as e:
        print(f"FAIL result.json 无法解析: {e}"); sys.exit(1)
    for k in REQUIRED_TOP:
        if k not in res: fails.append(f"result.json 缺顶层字段 {k}")
    if res.get("status") not in ("success", "partial", "failed"):
        fails.append(f"status 非法: {res.get('status')!r}")
    if res.get("status") in ("partial", "failed"):
        b = res.get("evidence_and_boundary", {})
        if not (b.get("unchecked") or b.get("pending_review") or res.get("failure_reason")):
            fails.append("partial/failed 未说明界限")
    if not res.get("case_id"): fails.append("case_id 为空")

    claims = []
    cp = os.path.join(w, "claims.json")
    if os.path.exists(cp):
        try: claims = json.load(open(cp, encoding="utf-8"))
        except Exception as e: fails.append(f"claims.json 无法解析: {e}")
    else:
        fails.append("claims.json 缺失")
    for c in claims:
        cid = c.get("claim_id", "?")
        for k in ("claim_id", "locator", "quote", "claim_source"):
            if not c.get(k): fails.append(f"claim {cid} 缺 {k}")
        if c.get("claim_source") not in CLAIM_SOURCES:
            fails.append(f"claim {cid} claim_source 非法: {c.get('claim_source')!r}")

    alignment = []
    ap_ = os.path.join(w, "alignment.csv")
    if os.path.exists(ap_):
        alignment = read_rows(ap_)
    else:
        fails.append("alignment.csv 缺失")
    author_ids = [c["claim_id"] for c in claims if c.get("claim_source") == "author_claim"]
    aligned_ids = [r.get("claim_id") for r in alignment]
    missing = [x for x in author_ids if x not in aligned_ids]
    if missing:
        fails.append(f"author_claim 未对齐: {','.join(missing)}")
    for r in alignment:
        if r.get("verdict") not in VERDICTS:
            fails.append(f"alignment {r.get('claim_id')} verdict 非法: {r.get('verdict')!r}")
        if r.get("verdict") == "undeterminable" and not (r.get("basis") or "").strip():
            fails.append(f"alignment {r.get('claim_id')} undeterminable 未写缺什么")

    findings = []
    fp = os.path.join(w, "findings.json")
    if os.path.exists(fp):
        try: findings = json.load(open(fp, encoding="utf-8"))
        except Exception as e: fails.append(f"findings.json 无法解析: {e}")
    for f_ in findings:
        fid = f_.get("id", "?")
        for k in FINDING_FIELDS:
            if not f_.get(k): fails.append(f"finding {fid} 缺字段 {k}")
        if f_.get("issue_type") not in ISSUE_TYPES:
            fails.append(f"finding {fid} issue_type 非法: {f_.get('issue_type')!r}")
        if f_.get("severity") not in SEVERITIES:
            fails.append(f"finding {fid} severity 非法: {f_.get('severity')!r}")
        loc = f_.get("location") or {}
        for k in ("file", "locator", "quote"):
            if not loc.get(k): fails.append(f"finding {fid} location 缺 {k}")
        if f_.get("severity") in ("major", "minor"):
            ev = f_.get("evidence") or ""
            if not any(kw in ev for kw in ("主结论", "复现", "可修正")):
                fails.append(f"finding {fid} severity={f_['severity']} 的 evidence 未回答三问（主结论/可修正/复现）")
        rec = f_.get("recommendation") or ""
        if any(v in rec for v in VAGUE_RE):
            fails.append(f"finding {fid} recommendation 是空话: {rec!r}")

    cov = res.get("coverage") or {}
    for c in CATEGORIES:
        if c not in cov: fails.append(f"result.coverage 缺 {c}")
    cj_path = os.path.join(w, "coverage.json")
    if os.path.exists(cj_path):
        try:
            cj = json.load(open(cj_path, encoding="utf-8"))
            for c in CATEGORIES:
                it = cj.get(c)
                if not it: fails.append(f"coverage.json 缺 {c}")
                elif not (it.get("checked") or it.get("na")):
                    fails.append(f"coverage.json {c} 未 checked 且未标 na")
        except Exception as e:
            fails.append(f"coverage.json 无法解析: {e}")

    rr = res.get("review_report") or {}
    if rr.get("findings_total") not in (None, len(findings)):
        fails.append("review_report.findings_total 与 findings.json 不一致")
    if rr.get("claims_total") not in (None, len(claims)):
        fails.append("review_report.claims_total 与 claims.json 不一致")

    if fails:
        print("\n".join("FAIL " + x for x in fails))
        print(f"SUMMARY claims={len(claims)} alignment={len(alignment)} findings={len(findings)} -> NOT PASS")
        sys.exit(1)
    print(f"SUMMARY claims={len(claims)} alignment={len(alignment)} findings={len(findings)} -> ALL PASS")

if __name__ == "__main__":
    main()
