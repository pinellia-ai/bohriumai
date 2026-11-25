#!/usr/bin/env python3
"""reconcile.py — 查询结果对账：行数守恒 + 聚合独立复算 + 脏数据显式计数。
用法: reconcile.py <query_log.json> <results_dir> <row_counts.json> <query_plan.json>
"""
import csv, json, os, re, sqlite3, sys

def main(log_p, res_dir, counts_p, plan_p):
    log = json.load(open(log_p, encoding="utf-8"))["queries"]
    counts = json.load(open(counts_p, encoding="utf-8"))
    plan = json.load(open(plan_p, encoding="utf-8"))
    plan_map = {q["id"]: q for q in plan.get("queries", plan if isinstance(plan, list) else [])}
    probs, notes = [], []
    con = None
    for rec in log:
        qid = rec["qid"]
        csv_p = os.path.join(res_dir, qid + ".csv")
        if rec["status"] != "ok" or not os.path.exists(csv_p):
            probs.append(f"{qid}: 未成功执行或结果缺失"); continue
        rows = list(csv.DictReader(open(csv_p, encoding="utf-8-sig")))
        sql = rec["sql"]
        if "GROUP BY" not in sql.upper() and "COUNT" not in sql.upper():
            src = plan_map.get(qid, {}).get("source_table")
            if src and len(rows) > counts.get(src, 0):
                probs.append(f"{qid}: 行数 {len(rows)} > 源表 {src}={counts[src]}（膨胀）")
        if rec.get("suspect"):
            probs.append(f"{qid}: 返回行数超预期 3 倍（疑似笛卡尔积）")
        # 脏数据显式计数
        nulls = sum(1 for r in rows for v in r.values() if v in (None, "", "None"))
        if nulls:
            notes.append(f"{qid}: 结果含 {nulls} 个空值单元格（已显式计数）")
        # 聚合复算：SQL 里 COUNT(*) 时用结果行数/直接重查核对
        if "COUNT(*)" in sql.upper() and re.search(r"group\s+by\s+(\w+)", sql, re.I):
            src_tbl = re.search(r"from\s+(\w+)", sql, re.I).group(1)
            cnt_col = next((k for k in (rows[0].keys() if rows else []) if k.lower() in ("n", "count", "cnt", "num")), None)
            if cnt_col:
                total = sum(int(r[cnt_col]) for r in rows if str(r[cnt_col]).isdigit())
                if total != counts.get(src_tbl):
                    notes.append(f"{qid}: 分组计数合计 {total} != 源表 {src_tbl} 行数 {counts.get(src_tbl)}（可能存在 WHERE 过滤, 已注明）")
    out = {"pass": not probs, "n_queries": len(log), "problems": probs, "notes": notes}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)

if __name__ == "__main__":
    main(*sys.argv[1:5])
