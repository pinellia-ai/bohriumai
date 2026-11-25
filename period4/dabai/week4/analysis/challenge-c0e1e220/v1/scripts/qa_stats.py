#!/usr/bin/env python3
"""qa_stats.py — 统计解释与结果对账：解释中的数字必须回查到 stats_results.json。
用法: qa_stats.py <stats_results.json> <interpretation.json>
"""
import json, re, sys

def numbers_in(x, acc):
    if isinstance(x, (int, float)):
        acc.append(float(x))
    elif isinstance(x, dict):
        for v in x.values(): numbers_in(v, acc)
    elif isinstance(x, list):
        for v in x: numbers_in(v, acc)

def main(stats_p, interp_p):
    stats = json.load(open(stats_p, encoding="utf-8"))
    interp = json.load(open(interp_p, encoding="utf-8"))
    acc = []
    numbers_in(stats, acc)
    stat_vals = {round(v, 3) for v in acc if abs(v) < 1e6}
    probs = []
    forbidden = ["证明有效", "证实了", "显著优于一切", "绝对"]
    for item in interp.get("interpretations", interp if isinstance(interp, list) else []):
        text = json.dumps(item, ensure_ascii=False)
        for w in forbidden:
            if w in text: probs.append(f"过度措辞: '{w}'")
        # 数值回查
        for m in re.findall(r"-?\d+\.\d+", text):
            v = float(m)
            if v in (0.05, 0.95, 0.01, 0.001, 3.0):
                continue
            if not any(abs(abs(v) - abs(s)) < 0.01 for s in acc if abs(s) < 1e6):
                probs.append(f"解释数字 {m} 未能在 stats_results 中找到")
    out = {"pass": not probs, "n_interp": len(interp.get("interpretations", interp if isinstance(interp, list) else [])), "problems": probs[:20]}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)

if __name__ == "__main__":
    main(*sys.argv[1:3])
