#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""incremental — 快照增量识别与追踪（真实可运行，仅标准库）。

用法（首轮建基线；后续轮对照 state.json 出增量）：
  python3 incremental.py --input /input --workdir /app/work --state /app/work/state.json \
      [--window-start 2025-01-01 --window-end 2025-06-30]

输出 incremental.json + 更新后的 state.json（幂等可复算）：
  baseline/snapshot 记录（抓取时间、结果计数、逐条 dedupe_key 全量保留）/
  new_items（相对上次快照的新增，附判定依据）/ repeats（重复=已被见过的 key）/ 
  version_changes（同 key 不同 DOI/年份形态）/ window（时间窗与边界处理）
"""
import argparse, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/input")
    ap.add_argument("--workdir", default="/app/work")
    ap.add_argument("--state", required=True)
    ap.add_argument("--window-start", default=None)
    ap.add_argument("--window-end", default=None)
    args = ap.parse_args()

    records, load_log = SL.load_records(args.input)
    if not records:
        print("corpus empty", file=sys.stderr)
        return 2

    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    state = {"runs": [], "seen_keys": {}}
    if os.path.exists(args.state):
        with open(args.state, encoding="utf-8") as fh:
            state = json.load(fh)
    seen = state.get("seen_keys", {})

    new_items, repeats, version_changes = [], [], []
    for r in records:
        key = SL.dedupe_key(r)
        f = r.get("fields", {})
        item = {"record_id": r["record_id"], "dedupe_key": key,
                "title": f.get("title"), "doi": SL.norm_doi(f.get("doi", "")) or None,
                "year": r.get("norm", {}).get("year"), "source": r["source"]}
        if key in seen:
            repeats.append({"record_id": r["record_id"], "dedupe_key": key,
                            "first_seen_run": seen[key], "action": "suppress"})
            # 版本变化：同 key 但 DOI/年份形态不同 → 记录为版本更新候选
            if item["doi"] and item["doi"] not in str(seen.get(key + "::doi", "")):
                version_changes.append({"record_id": r["record_id"], "dedupe_key": key,
                                        "note": "同去重键不同字段形态，人工判定是否新版本"})
        else:
            item["judgment_basis"] = "dedupe_key=%s 未见于上次快照 seen_keys（首轮为基线）" % key
            new_items.append(item)
        seen[key] = now
        if item["doi"]:
            seen[key + "::doi"] = item["doi"]

    in_window, out_window = [], []
    for it in new_items:
        y = it.get("year")
        if args.window_start and args.window_end and y:
            if args.window_start[:4] <= str(y) <= args.window_end[:4]:
                in_window.append(it)
            else:
                it2 = dict(it); it2["reason"] = "year_out_of_window"
                out_window.append(it2)
        else:
            in_window.append(it)

    state["runs"].append({"ts": now, "corpus_records": len(records),
                          "new_count": len(new_items), "repeat_count": len(repeats)})
    state["seen_keys"] = seen
    SL.write_json(args.state, state)
    out = {"run_ts": now, "is_baseline": len(state["runs"]) == 1,
           "window": {"start": args.window_start, "end": args.window_end,
                      "note": "窗口边界=年份四位数比对；跨窗边界条目列入 out_window 不静默丢弃"},
           "corpus_records": len(records),
           "new_items": in_window, "new_count": len(in_window),
           "out_window": out_window, "repeats": repeats[:200], "repeat_count": len(repeats),
           "version_changes": version_changes[:100],
           "idempotence_note": "dedupe_key 全量保留于 state.json；同快照重跑不产生二次新增",
           "load_log": load_log}
    SL.write_json(os.path.join(args.workdir, "incremental.json"), out)
    print("new=%d repeats=%d version_changes=%d baseline=%s" %
          (len(in_window), len(repeats), len(version_changes), out["is_baseline"]))
    return 0

if __name__ == "__main__":
    sys.exit(main())
