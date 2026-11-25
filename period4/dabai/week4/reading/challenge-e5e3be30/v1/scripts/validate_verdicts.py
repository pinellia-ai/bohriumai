#!/usr/bin/env python3
"""validate_verdicts.py — 校验证据核验结果（e5e3be30 用）。

用法:
  python3 validate_verdicts.py --result result.json --claims claims-to-verify.json \
      [--source-dir DIR]   # 提供原文目录时做 quote 子串匹配
  python3 validate_verdicts.py --selftest

校验项:
  1) claim 100% 覆盖、无多余
  2) verdict 四级枚举合法 (supported/partially_supported/contradicted/insufficient_evidence)
  3) 有证据的子判断 quote 非空且子串匹配
  4) contradicted 必须有反方向原文引文（引用核验教训：无定位引用=低分）
  5) supported/contradicted 的子判断必须有 rationale
"""
import argparse, json, os, sys

VERDICTS = {"supported", "partially_supported", "contradicted", "insufficient_evidence"}


def source_text(source_dir):
    texts = []
    if source_dir and os.path.isdir(source_dir):
        for root, _d, files in os.walk(source_dir):
            for fn in files:
                try:
                    with open(os.path.join(root, fn), encoding="utf-8", errors="ignore") as f:
                        texts.append(f.read())
                except OSError:
                    pass
    return "\n".join(texts)


def validate(result, claims_file, blob):
    errors, warnings = [], []
    req = {c.get("claim_id") for c in claims_file}
    got = {c.get("claim_id") for c in result.get("claims", [])}
    for m in req - got:
        errors.append(f"claim 缺失: {m}")
    for extra in got - req:
        errors.append(f"claim 多余: {extra}")
    for c in result.get("claims", []):
        cid = c.get("claim_id", "?")
        verdict = c.get("verdict")
        if verdict not in VERDICTS:
            errors.append(f"{cid}: 非法汇总 verdict '{verdict}'")
        subs = c.get("subjudgments", [])
        if not subs:
            errors.append(f"{cid}: 无子判断（拆解完备性不合格）")
        for s in subs:
            sid = s.get("sub_id", "?")
            v = s.get("verdict")
            if v not in VERDICTS:
                errors.append(f"{cid}/{sid}: 非法 verdict '{v}'")
                continue
            evs = s.get("evidence", [])
            if v == "insufficient_evidence" and evs:
                warnings.append(f"{cid}/{sid}: insufficient_evidence 却带证据，请复核")
            if v in ("supported", "contradicted"):
                if not evs:
                    errors.append(f"{cid}/{sid}: {v} 但无证据引文")
                for i, ev in enumerate(evs):
                    q = ev.get("quote")
                    if not (ev.get("paragraph_id") and q):
                        errors.append(f"{cid}/{sid}/ev{i}: 缺 paragraph_id/quote")
                    elif blob and q not in blob:
                        errors.append(f"{cid}/{sid}/ev{i}: quote 子串匹配失败")
                if not s.get("rationale"):
                    errors.append(f"{cid}/{sid}: {v} 但无判定理由")
    return errors, warnings


def selftest():
    claims_file = [{"claim_id": "c1"}, {"claim_id": "c2"}]
    result = {"case_id": "demo-ver", "status": "success", "claims": [
        {"claim_id": "c1", "verdict": "partially_supported", "subjudgments": [
            {"sub_id": "c1-s1", "type": "comparison", "verdict": "supported",
             "evidence": [{"paragraph_id": "p12", "quote": "94.2% vs 87.5% conversion"}],
             "rationale": "方向与量级符合"},
            {"sub_id": "c1-s2", "type": "scope", "verdict": "insufficient_evidence",
             "evidence": [], "rationale": "原文仅覆盖 300-350 K"}],
         "limitations": ["仅实测区间内成立"], "conflicts": []},
        {"claim_id": "c2", "verdict": "contradicted", "subjudgments": [
            {"sub_id": "c2-s1", "type": "fact", "verdict": "contradicted",
             "evidence": [{"paragraph_id": "p05", "quote": "no significant difference was observed"}],
             "rationale": "原文明确相反陈述"}], "limitations": [], "conflicts": []}]}
    blob = ("p12: catalysts compared, 94.2% vs 87.5% conversion. "
            "p05: no significant difference was observed between groups.")
    errs, warns = validate(result, claims_file, blob)
    print(f"selftest: errors={errs} warnings={warns}")
    return not errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result"); ap.add_argument("--claims"); ap.add_argument("--source-dir")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not (a.result and a.claims):
        ap.error("--result 与 --claims 必填（或用 --selftest）")
    with open(a.result, encoding="utf-8") as f:
        result = json.load(f)
    with open(a.claims, encoding="utf-8") as f:
        claims_file = json.load(f)
    if isinstance(claims_file, dict):
        claims_file = claims_file.get("claims", [])
    errs, warns = validate(result, claims_file, source_text(a.source_dir))
    for e in errs:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    print(f"{len(result.get('claims', []))} 条论断, {len(errs)} 错误, {len(warns)} 警告")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
