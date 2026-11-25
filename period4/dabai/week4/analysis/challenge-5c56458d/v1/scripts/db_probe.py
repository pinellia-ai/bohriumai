#!/usr/bin/env python3
"""db_probe.py — SQLite schema 发现与行数盘点（只读）。
用法: db_probe.py <db.sqlite> <workdir>
产出 schema.tsv(table,column,type,pk,nullable) + row_counts.json + sample_rows.json(每表前3行)
"""
import json, os, sqlite3, sys

def main(db_p, workdir):
    os.makedirs(workdir, exist_ok=True)
    con = sqlite3.connect(f"file:{db_p}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    with open(os.path.join(workdir, "schema.tsv"), "w", encoding="utf-8") as f:
        f.write("table\tcolumn\ttype\tpk\tnotnull\n")
        for t in tables:
            for col in cur.execute(f'PRAGMA table_info("{t}")'):
                f.write(f'{t}\t{col[1]}\t{col[2]}\t{col[5]}\t{col[3]}\n')
    counts = {}
    samples = {}
    for t in tables:
        counts[t] = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        samples[t] = [dict(r) for r in cur.execute(f'SELECT * FROM "{t}" LIMIT 3')]
    json.dump(counts, open(os.path.join(workdir, "row_counts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(samples, open(os.path.join(workdir, "sample_rows.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    con.close()
    print(json.dumps({"tables": tables, "row_counts": counts}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:3])
