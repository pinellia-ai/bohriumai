#!/usr/bin/env python3
"""validate_answers.py — 校验文献问答结果（15c85674 用）。

用法:
  python3 validate_answers.py --result result.json --case case.json
  python3 validate_answers.py --selftest     # 内置合成示例自测

校验项:
  1) case_id/paper_id/material_version 与 case.json 一致
  2) question_id 100% 覆盖、无多余
  3) status 枚举合法 (answered/partial/insufficient_evidence/input_error)
  4) answered 至少 1 条 claim；每条 claim 至少 1 条 evidence
  5) evidence 的 quote 在对应段落文本中子串匹配；kind 枚举合法
"""
import argparse, json, sys

STATUSES = {"answered", "partial", "insufficient_evidence", "input_error"}
KINDS = {"reported", "inferred"}


def paragraph_map(case):
    """从 case.json 提取 paragraph_id -> text 映射，兼容常见结构。"""
    pmap = {}
    for key in ("paragraphs", "paper_paragraphs", "sections", "material"):
        items = case.get(key)
        if isinstance(items, list):
            for it in items:
                if isinstance(it, dict):
                    pid = it.get("paragraph_id") or it.get("id")
                    txt = it.get("text") or it.get("content") or it.get("body")
                    if pid and txt:
                        pmap[pid] = txt
                elif isinstance(it, str) and " " in it:
                    pid, _, txt = it.partition(" ")
                    pmap[pid] = txt
    return pmap


def validate(result, case, pmap):
    errors, warnings = [], []
    for k in ("case_id", "paper_id", "material_version"):
        if case.get(k) and result.get(k) != case.get(k):
            errors.append(f"{k} 与输入不一致: {result.get(k)!r} != {case.get(k)!r}")
    req_qs, got_qs = set(), set()
    for q in case.get("questions", []):
        if isinstance(q, dict):
            req_qs.add(q.get("question_id"))
    got = {a.get("question_id") for a in result.get("answers", [])}
    if req_qs:
        for miss in req_qs - got:
            errors.append(f"问题缺失: {miss}")
        for extra in got - req_qs:
            errors.append(f"多余问题: {extra}")
    for a in result.get("answers", []):
        qid = a.get("question_id", "?")
        st = a.get("status")
        if st not in STATUSES:
            errors.append(f"{qid}: 非法 status '{st}'")
        claims = a.get("claims", [])
        if st == "answered" and not claims:
            errors.append(f"{qid}: answered 但 claims 为空")
        for c in claims:
            cid = c.get("claim_id", "?")
            if c.get("kind") not in KINDS:
                errors.append(f"{qid}/{cid}: 非法 kind '{c.get('kind')}'")
            evs = c.get("evidence", [])
            if not evs:
                errors.append(f"{qid}/{cid}: 无 evidence")
            for i, ev in enumerate(evs):
                pid, q = ev.get("paragraph_id"), ev.get("quote")
                if not pid or not q:
                    errors.append(f"{qid}/{cid}/ev{i}: paragraph_id/quote 缺失")
                elif pid in pmap and q not in pmap[pid]:
                    errors.append(f"{qid}/{cid}/ev{i}: quote 在 {pid} 中子串匹配失败")
        if st == "partial" and not a.get("unanswered_parts"):
            warnings.append(f"{qid}: partial 但 unanswered_parts 为空，应列明缺口")
    return errors, warnings


def selftest():
    case = {"case_id": "demo-qa-001", "paper_id": "paperX", "material_version": "v3",
            "questions": [{"question_id": "Q1"}],
            "paragraphs": [
                {"paragraph_id": "p07", "text": "sample A exhibited a BET surface area of 128 m2/g"},
                {"paragraph_id": "p08", "text": "the surface area of sample B was 95 m2/g"}]}
    result = {"case_id": "demo-qa-001", "paper_id": "paperX", "material_version": "v3",
              "answers": [{"question_id": "Q1",
                           "answer": "样品 A 为 128 m2/g，高于样品 B 的 95 m2/g。",
                           "conditions": ["BET 法"], "status": "answered",
                           "claims": [
                               {"claim_id": "Q1-c1", "text": "A 为 128 m2/g", "kind": "reported",
                                "evidence": [{"paragraph_id": "p07",
                                              "quote": "BET surface area of 128 m2/g"}]},
                               {"claim_id": "Q1-c2", "text": "A 高于 B", "kind": "inferred",
                                "evidence": [{"paragraph_id": "p07", "quote": "128 m2/g"},
                                             {"paragraph_id": "p08", "quote": "95 m2/g"}]}],
                           "unanswered_parts": []}],
              "coverage": {"read_sections": ["all"], "unread_sections": []}}
    errs, warns = validate(result, case, paragraph_map(case))
    print(f"selftest: errors={errs} warnings={warns}")
    return not errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result"); ap.add_argument("--case")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not (a.result and a.case):
        ap.error("--result 与 --case 必填（或用 --selftest）")
    with open(a.result, encoding="utf-8") as f:
        result = json.load(f)
    with open(a.case, encoding="utf-8") as f:
        case = json.load(f)
    errs, warns = validate(result, case, paragraph_map(case))
    for e in errs:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    print(f"{len(result.get('answers', []))} 个问题, {len(errs)} 错误, {len(warns)} 警告")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
