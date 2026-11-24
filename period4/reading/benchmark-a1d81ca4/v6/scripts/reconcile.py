#!/usr/bin/env python3
"""通用对账器: reconcile.py counts.json
counts.json: {"total": N, "parts": {"a": n1, "b": n2, ...}} 或 {"left": N, "right": M, "label": "..."}
输出 reconciliation.csv, 全部通过退出码 0, 否则 1。"""
import json, sys, csv

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'counts.json'
    data = json.load(open(src))
    rows, ok_all = [], True
    if 'parts' in data:
        s = sum(data['parts'].values())
        ok = (s == data['total'])
        rows.append(['total_vs_sum_parts', data['total'], s, 'PASS' if ok else 'FAIL'])
        ok_all &= ok
        for k, v in data['parts'].items():
            rows.append([f'part:{k}', '', v, 'info'])
    if 'left' in data and 'right' in data:
        ok = (data['left'] == data['right'])
        rows.append([data.get('label', 'left_vs_right'), data['left'], data['right'], 'PASS' if ok else 'FAIL'])
        ok_all &= ok
    with open('reconciliation.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['check', 'expected', 'actual', 'result']); w.writerows(rows)
    print(f"reconciliation: {'ALL PASS' if ok_all else 'HAS FAILURES'} ({len(rows)} checks)")
    sys.exit(0 if ok_all else 1)

if __name__ == '__main__':
    main()
