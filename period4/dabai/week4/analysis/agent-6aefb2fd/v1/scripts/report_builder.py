#!/usr/bin/env python3
"""report_builder.py — 报告数字程序化回填：模板占位符 {{path.to.value}} 从 stats_results.json 取值。
backfill_check：回填后报告不应残留 {{...}}；且关键数字与来源一致（取值即一致）。
用法: report_builder.py <stats_results.json> <template.md> <out.md>
模板示例:
  Ctrl 组均值 {{tests.0.result.descriptive.0.mean}} (n={{tests.0.result.descriptive.0.n}})。
"""
import json, re, sys

def get_path(obj, path):
    for part in path.split("."):
        if isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    return obj

def fmt(v):
    if v is None:
        return "NA"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)

def main(stats_p, tmpl_p, out_p):
    stats = json.load(open(stats_p, encoding="utf-8"))
    text = open(tmpl_p, encoding="utf-8").read()
    filled, missing = [], []
    def repl(m):
        path = m.group(1)
        try:
            v = get_path(stats, path)
            filled.append({"path": path, "value": v})
            return fmt(v)
        except (KeyError, IndexError, ValueError, TypeError):
            missing.append(path)
            return m.group(0)
    out_text = re.sub(r"\{\{([^}]+)\}\}", repl, text)
    open(out_p, "w", encoding="utf-8").write(out_text)
    ok = not missing
    # 回填审计文件
    json.dump({"filled": filled, "missing": missing}, open(out_p + ".audit.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"pass": ok, "n_filled": len(filled), "missing": missing, "out": out_p}, ensure_ascii=False))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
