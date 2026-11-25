#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""round_gain — 多轮检索边际收益与停止判断（真实可运行，仅标准库）。

用法：
  python3 round_gain.py --search-log /app/work/search_log.jsonl --workdir /app/work

输出 gain.json：逐轮新增命中、边际收益曲线、收敛判定与停止建议。
停止判据（可复核）：连续两轮新增命中数 ≤ 上轮命中数的 10%，判 converged。
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search-log", required=True)
    ap.add_argument("--workdir", default="/app/work")
    args = ap.parse_args()
    slog = SL.load_jsonl(args.search_log)
    by_round, order = {}, []
    for r in slog:
        rid = r.get("round_id")
        if rid not in by_round:
            by_round[rid] = set()
            order.append(rid)
        by_round[rid].update(r.get("hit_ids") or [])
    seen, rows = set(), []
    for rid in order:
        cur = by_round[rid]
        new = cur - seen
        rows.append({"round_id": rid, "cumulative_unique": len(seen | cur),
                     "new_this_round": len(new), "new_record_ids": sorted(new)[:30],
                     "marginal_gain": round(len(new) / max(1, len(cur)), 4)})
        seen |= cur
    converged = False
    if len(rows) >= 3:
        last2 = rows[-2:]
        converged = all(r["marginal_gain"] <= 0.10 for r in last2)
    out = {"rounds": rows, "unique_hits_total": len(seen),
           "converged": converged,
           "stop_rule": "连续两轮边际增益≤10% 判收敛；未收敛且预算允许则追加子问题查询，否则如实报告残余缺口",
           "residual_note": None if converged else "未达收敛判据：存在未覆盖子问题或术语变体，结果标 partial 并列出残余缺口"}
    SL.write_json(os.path.join(args.workdir, "gain.json"), out)
    print("rounds=%d unique=%d converged=%s" % (len(rows), len(seen), converged))
    return 0

if __name__ == "__main__":
    sys.exit(main())
