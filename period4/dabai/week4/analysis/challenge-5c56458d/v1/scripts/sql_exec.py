#!/usr/bin/env python3
"""sql_exec.py — 查询计划受控执行（只读+写拦截+留痕）。
用法: sql_exec.py <query_plan.json> <db.sqlite> <outdir>
"""
import csv, json, os, re, sqlite3, sys, time

FORBIDDEN = re.compile(r"\b(create|insert|update|delete|drop|alter|attach|replace)\b", re.I)

def main(plan_p, db_p, outdir):
    plan = json.load(open(plan_p, encoding="utf-8"))
    os.makedirs(os.path.join(outdir, "results"), exist_ok=True)
    con = sqlite3.connect(f"file:{db_p}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    log = []
    for q in plan.get("queries", plan if isinstance(plan, list) else []):
        qid, sql = q["id"], q["sql"].strip().rstrip(";")
        rec = {"qid": qid, "sql": sql}
        if FORBIDDEN.search(sql):
            rec.update({"status": "rejected", "reason": "写语句/DDL 被拦截（只读协议）", "rows": 0})
            log.append(rec); continue
        t0 = time.time()
        try:
            cur = con.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = [dict(r) for r in cur.fetchall()]
            rec.update({"status": "ok", "rows": len(rows), "columns": cols,
                        "seconds": round(time.time() - t0, 3),
                        "suspect": len(rows) > q.get("expected_rows_max", 10 ** 6) * 3,
                        "grain": q.get("expected_grain", "")})
            base = os.path.join(outdir, "results", qid)
            with open(base + ".csv", "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=cols or ["result"])
                w.writeheader()
                for r in rows: w.writerow({c: r.get(c) for c in cols})
            json.dump(rows, open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        except Exception as e:
            rec.update({"status": "error", "error": str(e), "rows": 0, "seconds": round(time.time() - t0, 3)})
        log.append(rec)
    con.close()
    json.dump({"db": os.path.abspath(db_p), "queries": log},
              open(os.path.join(outdir, "query_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = all(r["status"] == "ok" for r in log) and bool(log)
    print(json.dumps({"pass": ok, "n_queries": len(log),
                      "statuses": {r["qid"]: r["status"] for r in log}}, ensure_ascii=False, indent=1))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
