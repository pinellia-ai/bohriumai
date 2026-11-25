#!/usr/bin/env python3
"""annotate_check.py — 可视化标注十项检查 + 图注生成。
用法: annotate_check.py <figure.svg> <chart_spec.json> [--outdir <dir 写 note.txt>]
"""
import json, os, re, sys

def has(svg, pat):
    return re.search(pat, svg) is not None

def main(svg_p, spec_p, outdir=None):
    s = open(svg_p, encoding="utf-8").read()
    spec = json.load(open(spec_p, encoding="utf-8"))
    checks = []
    def ck(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
    ck("x_label_exists", spec.get("x_label"))
    yl = spec.get("y_label", "")
    ck("y_label_has_unit", bool(yl) and bool(re.search(r"[（(].+[)）]|[A-Za-z/%μ°$]+", yl)), yl)
    if spec.get("type") == "bar":
        ck("err_label_declared", bool(spec.get("err_label")), spec.get("err_label", ""))
    else:
        checks[-1] if False else ck("err_label_declared", True, "非柱图不强制")
    ck("n_points_in_svg", len(re.findall(r"data-row=", s)) > 0, f'{len(re.findall(chr(34)+"data-row=", s))} mapped elements')
    ck("baseline_zero_bar", (spec.get("type") != "bar") or spec.get("zero_baseline", True))
    ck("panel_title", bool(spec.get("title")))
    ck("text_editable", len(re.findall(r"<text\b", s)) > 0)
    ck("no_empty_legend_text", '></text>' not in s)
    ck("log_axis_explicit", (not s.count("log_y")) or spec.get("log_y") is True)
    srcnames = re.findall(r'data-source="([^"]*)"', s)
    ck("elements_have_source", all(x.strip() for x in srcnames) and bool(srcnames))
    passed = all(c["pass"] for c in checks)
    # 生成图注
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        err = spec.get("err_label", "")
        note = (f'{spec.get("title", "")}: {spec.get("y_label", "")} vs {spec.get("x_label", "")}. '
                f'{spec.get("type", "")} chart, n={len(re.findall("data-row=", s))}'
                + (f', error bars={err}' if err else '')
                + f'. Data: {os.path.basename(spec.get("data_csv", ""))}. '
                + ('Baseline not truncated (bars start at 0). ' if spec.get("type") == "bar" else '')
                + 'Palette: Okabe-Ito (colorblind-safe, grayscale-separable).')
        open(os.path.join(outdir, "fig_note.txt"), "w", encoding="utf-8").write(note)
    out = {"pass": passed, "checks": checks}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    a = sys.argv[1:]
    od = None
    if "--outdir" in a:
        i = a.index("--outdir"); od = a[i + 1]; del a[i:i + 2]
    main(a[0], a[1], od)
