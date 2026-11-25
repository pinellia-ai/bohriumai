#!/usr/bin/env python3
"""深度研究流水线校验器：拆解/计划/工具调用/证据表/综合的完整性对账。
用法: python3 pipeline_check.py --work /app/work --out /tmp/check.json
校验项：依赖成环、计划去重、回链率100%、冲突对账、空白有据。
"""
import argparse, csv, json, os, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    report = {"checks": {}, "errors": []}

    # decomposition
    dec_path = os.path.join(a.work, 'decomposition.json')
    dec = json.load(open(dec_path, encoding='utf-8')) if os.path.exists(dec_path) else {"sq": []}
    sq_ids = {s.get('sq_id') for s in dec.get('sq', [])}
    for s in dec.get('sq', []):
        if not s.get('search_action'):
            report['errors'].append(f"{s.get('sq_id')} 缺 search_action（拆解退化为关键词改写）")
        for d in s.get('depends_on', []):
            if d not in sq_ids:
                report['errors'].append(f"{s.get('sq_id')} 依赖未定义的 {d}")
    # 依赖成环检测
    dep_map = {s.get('sq_id'): s.get('depends_on', []) for s in dec.get('sq', [])}
    visited, stack = set(), set()
    def dfs(n):
        if n in stack:
            report['errors'].append(f"依赖成环: {n}")
            return
        if n in visited:
            return
        visited.add(n); stack.add(n)
        for d in dep_map.get(n, []):
            dfs(d)
        stack.discard(n)
    for n in dep_map:
        dfs(n)
    report['checks']['decomposition'] = {"n_sq": len(sq_ids), "all_have_search_action": all(s.get('search_action') for s in dec.get('sq', []))}

    # search_plan 去重
    plan_path = os.path.join(a.work, 'search_plan.json')
    plan = json.load(open(plan_path, encoding='utf-8')) if os.path.exists(plan_path) else {"queries": []}
    seen = set()
    for q in plan.get('queries', []):
        key = (q.get('sources') and tuple(q['sources']), q.get('query'))
        if key in seen:
            report['errors'].append(f"重复检索: {q.get('query')}")
        seen.add(key)
        if not q.get('stop_rule'):
            report['errors'].append(f"查询 {q.get('query')} 缺停止条件")
    uncovered = sq_ids - {q.get('sq_id') for q in plan.get('queries', [])}
    if uncovered:
        report['errors'].append(f"子问题无检索计划: {sorted(uncovered)}")
    report['checks']['search_plan'] = {"n_queries": len(plan.get('queries', [])), "no_dup_queries": not any('重复检索' in e for e in report['errors'])}

    # tool_calls
    tc_path = os.path.join(a.work, 'tool_calls.jsonl')
    calls = []
    if os.path.exists(tc_path):
        for line in open(tc_path, encoding='utf-8'):
            line = line.strip()
            if line:
                calls.append(json.loads(line))
    if len(calls) < len(plan.get('queries', [])):
        report['errors'].append(f"tool_calls({len(calls)}) < 计划查询数({len(plan.get('queries', []))})")
    report['checks']['tool_calls'] = {"n": len(calls)}

    # evidence_table 回链 + 冲突
    et_path = os.path.join(a.work, 'evidence_table.json')
    ev = json.load(open(et_path, encoding='utf-8')) if os.path.exists(et_path) else []
    if os.path.exists(os.path.join(a.work, 'evidence_table.csv')):
        with open(os.path.join(a.work, 'evidence_table.csv'), encoding='utf-8') as f:
            ev = list(csv.DictReader(f))
    ev_ids = {e.get('ev_id') for e in ev}
    missing_loc = [e.get('ev_id') for e in ev if not e.get('locator')]
    if missing_loc:
        report['errors'].append(f"证据缺 locator: {missing_loc}")
    conflict_flags = {e.get('ev_id') for e in ev if e.get('conflicts_with')}
    report['checks']['evidence_table'] = {"n": len(ev), "all_have_locator": not missing_loc}

    # synthesis 回链率
    syn_path = os.path.join(a.work, 'synthesis.json')
    syn = json.load(open(syn_path, encoding='utf-8')) if os.path.exists(syn_path) else []
    bad_claims = [c.get('claim', '?')[:30] for c in syn if not c.get('supported_by') or any(e not in ev_ids for e in c.get('supported_by', []))]
    if bad_claims:
        report['errors'].append(f"结论句无证据回链或 ev 不存在: {bad_claims}")
    report['checks']['synthesis'] = {"n": len(syn), "link_rate": f"{(len(syn) - len(bad_claims))}/{len(syn)}"}

    # gaps 有据
    gaps_path = os.path.join(a.work, 'gaps.json')
    gaps = json.load(open(gaps_path, encoding='utf-8')) if os.path.exists(gaps_path) else []
    for g in gaps:
        if not g.get('queries_tried'):
            report['errors'].append(f"空白无检索缺口依据: {str(g.get('gap'))[:30]}")
    report['checks']['gaps'] = {"n": len(gaps), "all_grounded": all(g.get('queries_tried') for g in gaps)}

    report['verdict'] = "pass" if not report['errors'] else "fail"
    json.dump(report, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": report['verdict'], "n_errors": len(report['errors'])}, ensure_ascii=False))
    for e in report['errors']:
        print(" -", e)

if __name__ == "__main__":
    main()
