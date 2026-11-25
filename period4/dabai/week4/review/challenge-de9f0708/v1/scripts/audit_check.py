#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_check.py — 学术规范与合规检查 result.json / findings / declarations 验收器。

用法: python3 audit_check.py /app/output/result.json [--workdir /app/output]
验收（全过退出码 0；任一失败退出码 1）:
  1. result.json 顶层字段齐全; status 合法; partial/failed 有界限; case_id 非空
  2. findings 每条九件齐全（含 basis_ref）; location.quote 非空
  3. needs_review 条目必须写明缺什么依据; 无 basis_ref 的非 pending 判定 = 失败
  4. category ∈ 六风险面; declarations_check.csv 存在且 ≥1 行
  5. basis_registry.json 存在且每条有 source_locator
  6. coverage 六风险面 + 六通用类键齐全
"""
import argparse, csv, json, os, sys

RISK_FACES = ["academic_integrity", "citation_norm", "privacy_data",
              "copyright_license", "ethics_review", "submission_requirements"]
GENERIC_CATEGORIES = ["fact_verification", "citation_support", "method_design",
                      "statistical_reporting", "argument_chain", "academic_norm"]
ISSUE_TYPES = {"fact_error", "insufficient_evidence", "norm_issue", "suggestion", "pending_review"}
REQUIRED_TOP = ["case_id", "status", "deliverables", "review_report",
                "evidence_and_boundary", "coverage", "sources", "uncertainty_notes"]
FINDING_FIELDS = ["id", "category", "location", "issue_type", "severity",
                  "basis_ref", "needs_review", "evidence", "recommendation"]

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

    br_path = os.path.join(w, "basis_registry.json")
    basis_ids = set()
    if os.path.exists(br_path):
        try:
            br = json.load(open(br_path, encoding="utf-8"))
            items = br if isinstance(br, list) else br.get("items", [])
            for it in items:
                if not (it.get("source_locator") or it.get("source")):
                    fails.append(f"basis_registry {it.get('basis_id','?')} 缺 source_locator")
                if it.get("basis_id"):
                    basis_ids.add(it["basis_id"])
            if not items and res.get("status") == "success":
                fails.append("basis_registry 为空但 status=success（应说明无依据面）")
        except Exception as e:
            fails.append(f"basis_registry.json 无法解析: {e}")
    else:
        fails.append("basis_registry.json 缺失")

    findings = []
    fp = os.path.join(w, "findings.json")
    if os.path.exists(fp):
        try: findings = json.load(open(fp, encoding="utf-8"))
        except Exception as e: fails.append(f"findings.json 无法解析: {e}")
    for f_ in findings:
        fid = f_.get("id", "?")
        for k in FINDING_FIELDS:
            if k not in f_ or f_[k] in (None, ""):
                fails.append(f"finding {fid} 缺字段 {k}")
        if f_.get("category") not in RISK_FACES:
            fails.append(f"finding {fid} category 非法: {f_.get('category')!r}")
        if f_.get("issue_type") not in ISSUE_TYPES:
            fails.append(f"finding {fid} issue_type 非法: {f_.get('issue_type')!r}")
        loc = f_.get("location") or {}
        for k in ("file", "locator", "quote"):
            if not loc.get(k): fails.append(f"finding {fid} location 缺 {k}")
        nr = f_.get("needs_review")
        if not nr and f_.get("issue_type") != "pending_review":
            ref = str(f_.get("basis_ref") or "")
            ref_id = ref.split(":")[-1] if ref else ""
            if not ref_id or ref_id not in basis_ids:
                fails.append(f"finding {fid} 判定无绑定依据（basis_ref 未登记于 registry）: {ref!r}")
        else:
            if not (f_.get("evidence") or "").strip():
                fails.append(f"finding {fid} needs_review 未写缺什么依据")

    dc_path = os.path.join(w, "declarations_check.csv")
    if os.path.exists(dc_path):
        with open(dc_path, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            fails.append("declarations_check.csv 为空")
    else:
        fails.append("declarations_check.csv 缺失")

    cov = res.get("coverage") or {}
    for c in RISK_FACES + GENERIC_CATEGORIES:
        if c not in cov: fails.append(f"result.coverage 缺 {c}")
    cj_path = os.path.join(w, "coverage.json")
    if os.path.exists(cj_path):
        try:
            cj = json.load(open(cj_path, encoding="utf-8"))
            for c in RISK_FACES + GENERIC_CATEGORIES:
                it = cj.get(c)
                if not it: fails.append(f"coverage.json 缺 {c}")
                elif not (it.get("checked") or it.get("na")):
                    fails.append(f"coverage.json {c} 未 checked 且未标 na")
        except Exception as e:
            fails.append(f"coverage.json 无法解析: {e}")

    rr = res.get("review_report") or {}
    if rr.get("findings_total") not in (None, len(findings)):
        fails.append("review_report.findings_total 与 findings.json 不一致")

    if fails:
        print("\n".join("FAIL " + x for x in fails))
        print(f"SUMMARY findings={len(findings)} basis={len(basis_ids)} -> NOT PASS")
        sys.exit(1)
    print(f"SUMMARY findings={len(findings)} basis={len(basis_ids)} -> ALL PASS")

if __name__ == "__main__":
    main()
