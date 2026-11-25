#!/usr/bin/env python3
"""选题评估校验器：novelty 逐条对照/可行性前提三分/矩阵来源率/禁语检查。
用法: python3 novelty_check.py --work /app/work --out /tmp/ncheck.json
"""
import argparse, csv, json, os, re, sys

BANNED = re.compile(r'(尚无人研究|首次提出|没有人做过|无人涉足|前无古人)')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    errors = []

    # problem_definition
    pd_p = os.path.join(a.work, 'problem_definition.json')
    pd = json.load(open(pd_p, encoding='utf-8')) if os.path.exists(pd_p) else {}
    for k in ('statement', 'variables', 'baseline', 'falsifier'):
        if not pd.get(k):
            errors.append(f"problem_definition 缺 {k}")
    # comparison_matrix
    cm_p = os.path.join(a.work, 'comparison_matrix.csv')
    rows = list(csv.DictReader(open(cm_p, encoding='utf-8'))) if os.path.exists(cm_p) else []
    no_loc = [r.get('ref') for r in rows if not r.get('locator')]
    if no_loc:
        errors.append(f"比较矩阵缺 locator: {no_loc}")
    for r in rows:
        if r.get('closeness') == 'not_comparable' and not r.get('not_comparable_reason'):
            errors.append(f"not_comparable 未给原因: {r.get('ref')}")
    # novelty
    nv_p = os.path.join(a.work, 'novelty_check.json')
    nv = json.load(open(nv_p, encoding='utf-8')) if os.path.exists(nv_p) else []
    types_ok = {'method', 'data', 'scenario_transfer', 'conclusion_revision'}
    for n in nv:
        if n.get('type') not in types_ok:
            errors.append(f"创新类型非法: {n.get('claim', '?')[:20]} -> {n.get('type')}")
        if n.get('verdict') == 'novel' and not n.get('checked_dims'):
            errors.append(f"novel 判定缺 checked_dims（查了什么）: {n.get('claim', '?')[:20]}")
        for blob in [json.dumps(n, ensure_ascii=False)]:
            if BANNED.search(blob):
                errors.append(f"出现禁语(尚无人研究类): {n.get('claim', '?')[:20]}")
    # feasibility
    fs_p = os.path.join(a.work, 'feasibility.json')
    fs = json.load(open(fs_p, encoding='utf-8')) if os.path.exists(fs_p) else {}
    for p in fs.get('premises', []):
        if p.get('status') not in ('verified', 'assumption', 'unverifiable'):
            errors.append(f"前提状态非法: {p.get('premise', '?')[:20]}")
        if p.get('status') == 'verified' and not p.get('source'):
            errors.append(f"verified 前提缺 source: {p.get('premise', '?')[:20]}")
        if p.get('status') == 'assumption' and p.get('source'):
            errors.append(f"assumption 不应有 source: {p.get('premise', '?')[:20]}")
    if fs and not fs.get('failure_risks'):
        errors.append("可行性缺 failure_risks")

    report = {"n_matrix": len(rows), "n_novelty": len(nv), "n_premises": len(fs.get('premises', [])),
              "errors": errors, "verdict": "pass" if not errors else "fail"}
    json.dump(report, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": report['verdict'], "n_errors": len(errors)}, ensure_ascii=False))
    for e in errors:
        print(" -", e)

if __name__ == "__main__":
    main()
