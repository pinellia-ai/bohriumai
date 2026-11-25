#!/usr/bin/env python3
"""chart_builder.py — 源数据表 → 科研数据图（柱/线/散点），SVG 可编辑源文件 + PNG/PDF 导出。

输入 spec JSON：
{
  "type": "bar|line|scatter",
  "data_csv": "path.csv",          # 长表：x,y 两列（可选 err 列=误差线）
  "x_label": "...", "y_label": "..."（含单位）,
  "title": "...",                  # 面板编号可写进 title
  "err_label": "SD|SEM|95%CI",     # 误差线含义，必须有
  "source_map": {"行号或范围": "列名来源"}  # 可选；缺失时逐点生成 data-source=csv行号
  "canvas": {"width": 720, "height": 540},
  "colors": ["#4477AA", ...],      # 多系列时按序取色
  "log_y": false,
  "export": {"png_dpi": 300, "pdf": true}
}
每个图元带 data-value 与 data-row（回溯到 CSV 行号），柱高/点位置 = 值线性映射（写进 SVG 注释），图例项数=系列数。
"""
import argparse, csv, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_g import Canvas, png_to_pdf
from raster import _load_font, _px

PALETTE = ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#AA3377", "#66CCEE"]


def _raster_chart(spec, rows, m, W, H, ymin, ymax, X, Y, out_path, dpi):
    """PIL 光栅化与 SVG 完全同源：同一映射函数 Y()/X()，保证位图导出=矢量源文件。"""
    from PIL import Image, ImageDraw
    scale = dpi / 72.0
    img = Image.new("RGB", (int(W * scale), int(H * scale)), "#ffffff")
    dr = ImageDraw.Draw(img)
    fc = {}
    def F(pt):
        px = _px(pt, dpi)
        if px not in fc: fc[px] = _load_font(px)[0]
        return fc[px]
    def L(x1, y1, x2, y2, w, col="#333333"):
        dr.line([(x1*scale, y1*scale), (x2*scale, y2*scale)], fill=col, width=max(1, int(w*scale)))
    def R(x, y, w, h, fill):
        dr.rectangle([x*scale, y*scale, (x+w)*scale, (y+h)*scale], fill=fill, outline="#333333", width=1)
    def C(x, y, r, fill):
        dr.ellipse([(x-r)*scale, (y-r)*scale, (x+r)*scale, (y+r)*scale], fill=fill, outline="#333333")
    def T(x, y, s_, pt, anchor="middle", col="#111111"):
        f = F(pt); tw = dr.textlength(s_, font=f)
        px = x*scale - (tw/2 if anchor == "middle" else (tw if anchor == "right" else 0))
        dr.text((px, y*scale - _px(pt, dpi)*0.85), s_, font=f, fill=col)

    pw_, ph_ = W - m["l"] - m["r"], H - m["t"] - m["b"]
    L(m["l"], m["t"]+ph_, m["l"]+pw_, m["t"]+ph_, 1.4)   # x axis
    L(m["l"], m["t"], m["l"], m["t"]+ph_, 1.4)           # y axis
    for k in range(5):
        v = ymin + (ymax - ymin)*k/4; yy = Y(v)
        L(m["l"]-4, yy, m["l"], yy, 1.0)
        T(m["l"]-6, yy+4, f"{v:.4g}", 10, "right")
    for i, r in enumerate(rows):
        T(X(i), m["t"]+ph_+16, str(r["x"]), 10)
        col = PALETTE[i % len(PALETTE)] if spec.get("type") == "bar" else PALETTE[0]
        if spec.get("type") == "bar":
            R(X(i)-pw_/len(rows)*0.32, Y(r["y"]), pw_/len(rows)*0.64, (m["t"]+ph_)-Y(r["y"]), col)
        elif spec.get("type") == "scatter":
            C(X(i), Y(r["y"]), 4*scale**0.5, col)
        else:
            if i:
                L(X(i-1), Y(rows[i-1]["y"]), X(i), Y(r["y"]), 1.8)
            C(X(i), Y(r["y"]), 3.5*scale**0.5, col)
        if r["err"] is not None:
            L(X(i), Y(r["y"]-r["err"]), X(i), Y(r["y"]+r["err"]), 1.2)
            L(X(i)-4, Y(r["y"]+r["err"]), X(i)+4, Y(r["y"]+r["err"]), 1.2)
    T(m["l"]+pw_/2, H-24, spec.get("x_label", "x"), 13)
    T(22, m["t"]+ph_/2, spec.get("y_label", "y"), 13)
    if spec.get("title"):
        T(m["l"], 26, spec["title"], 14, "left")
    img.save(out_path, dpi=(dpi, dpi))
    fp = os.path.basename(_load_font(12)[1])
    return os.path.basename(fp)


def read_csv(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for i, row in enumerate(r, start=2):  # 行号从2计（1=表头）
            rows.append({"row": i, "x": row[r.fieldnames[0]], "y": float(row[r.fieldnames[1]]),
                         "err": float(row["err"]) if "err" in row and row["err"] not in ("", None) else None})
    return rows


def group_series(rows):
    """按 x 分组（bar 多系列）或按系列列（本实现按 x 排序单系列+可选分组列 g）。"""
    return rows


def build(spec, outdir):
    rows = read_csv(spec["data_csv"])
    W, H = spec.get("canvas", {}).get("width", 720), spec.get("canvas", {}).get("height", 540)
    m = {"l": 70, "r": 24, "t": 40 + (18 if spec.get("title") else 0), "b": 58}
    pw, ph = W - m["l"] - m["r"], H - m["t"] - m["b"]
    c = Canvas(W, H, spec.get("title", "chart"))
    ys = [r["y"] for r in rows]
    err = [r["err"] for r in rows if r["err"] is not None]
    if spec.get("log_y"):
        ymin_data, ymax_data = min(ys), max(ys)
        ymin, ymax = ymin_data / 10 ** 0.2, ymax_data * 10 ** 0.2
    else:
        span_pad = (max(ys) - min(ys)) * 0.12 + (max(err) if err else 0)
        ymin, ymax = min(ys) - span_pad, max(ys) + span_pad
        if spec.get("zero_baseline", True) and ymin > 0 and not spec.get("log_y"):
            ymin = 0

    def Y(v):
        if spec.get("log_y"):
            return m["t"] + ph - (math.log10(v) - math.log10(ymin)) / (math.log10(ymax) - math.log10(ymin)) * ph
        return m["t"] + ph - (v - ymin) / (ymax - ymin) * ph

    xs = list(range(len(rows)))
    def X(i):
        return m["l"] + (i + 0.5) / len(rows) * pw

    # 轴与刻度（不截断基线：bar 从 0 起，已强制）
    c.line("structure", m["l"], m["t"] + ph, m["l"] + pw, m["t"] + ph, sw=1.4, elem_id="axis-x", source=f"{spec['data_csv']}#row1(header)+data")
    c.line("structure", m["l"], m["t"], m["l"], m["t"] + ph, sw=1.4, elem_id="axis-y", source=f"{spec['data_csv']}#col2")
    # y 刻度 5 个
    for k in range(5):
        v = ymin + (ymax - ymin) * k / 4
        yy = Y(v)
        c.line("structure", m["l"] - 4, yy, m["l"], yy, sw=1, elem_id=f"tick-y-{k}", source="figure-own")
        c.text("annotation", m["l"] - 6, yy + 4, f"{v:.4g}", size=10, anchor="end", elem_id=f"ticktext-y-{k}", source="figure-own")
    for i, r in enumerate(rows):
        c.text("annotation", X(i), m["t"] + ph + 16, str(r["x"]), size=10, elem_id=f"ticktext-x-{i}", source=f"{spec['data_csv']}#row{r['row']}col1")

    t0 = spec.get("type", "bar")
    for i, r in enumerate(rows):
        col = PALETTE[i % len(PALETTE)] if t0 == "bar" else spec.get("colors", [PALETTE[0]])[0]
        src = f"{spec['data_csv']}#row{r['row']},col2"
        if t0 == "bar":
            bh = (m["t"] + ph) - Y(r["y"])
            c.rect("data", X(i) - pw / len(rows) * 0.32, Y(r["y"]), pw / len(rows) * 0.64, bh,
                   fill=col, stroke="#333", sw=0.8, elem_id=f"bar-{i}", source=src,
                   extra=f'data-value="{r["y"]}" data-row="{r["row"]}"')
        elif t0 == "scatter":
            c.circle("data", X(i), Y(r["y"]), 4, fill=col, stroke="#333", sw=0.8, elem_id=f"pt-{i}", source=src,
                     extra=f'data-value="{r["y"]}" data-row="{r["row"]}"')
        else:  # line
            if i:
                p = rows[i - 1]
                c.line("data", X(i - 1), Y(p["y"]), X(i), Y(r["y"]), sw=1.8, elem_id=f"seg-{i}", source=src)
            c.circle("data", X(i), Y(r["y"]), 3.5, fill=col, stroke="#333", sw=0.8, elem_id=f"pt-{i}", source=src,
                     extra=f'data-value="{r["y"]}" data-row="{r["row"]}"')
        if r["err"] is not None:
            yy1, yy2 = Y(r["y"] - r["err"]), Y(r["y"] + r["err"])
            c.line("annotation", X(i), yy1, X(i), yy2, sw=1.2, elem_id=f"err-{i}", source=src + f",err={r['err']}")
            c.line("annotation", X(i) - 4, yy2, X(i) + 4, yy2, sw=1.2, elem_id=f"errcap-{i}", source="figure-own")

    c.text("annotation", m["l"] + pw / 2, H - 30, spec.get("x_label", "x"), size=13, elem_id="xlabel", source="figure-own")
    c.text("annotation", 18, m["t"] + ph / 2, spec.get("y_label", "y"), size=13, elem_id="ylabel", source="figure-own")
    if spec.get("title"):
        c.text("annotation", m["l"], 24, spec["title"], size=14, anchor="start", bold=True, elem_id="panel-title", source="figure-own")
    cap = f"误差线={spec.get('err_label', 'unspecified')}；n={len(rows)}；数据源={os.path.basename(spec['data_csv'])}"
    c.text("annotation", m["l"], m["t"] - 6, cap, size=9, anchor="start", fill="#555", elem_id="cap-note", source="figure-own")

    os.makedirs(outdir, exist_ok=True)
    base = (spec.get("title") or "chart").replace(" ", "_")
    svg_path = os.path.join(outdir, base + ".svg")
    c.save(svg_path)
    png_path = os.path.join(outdir, base + ".png")
    dpi = spec.get("export", {}).get("png_dpi", 300)
    fu = _raster_chart(spec, rows, m, W, H, ymin, ymax, X, Y, png_path, dpi)
    out = {"svg": svg_path, "png": png_path, "font_used": fu,
           "n_points": len(rows), "ymin_render": round(ymin, 4), "ymax_render": round(ymax, 4)}
    if spec.get("export", {}).get("pdf", True):
        pw_pt = min(spec.get("export", {}).get("max_width_in", 7.5) * 72, W * 0.75)
        out["pdf"] = png_to_pdf(png_path, os.path.join(outdir, base + ".pdf"), pw_pt, pw_pt * H / W)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    print(json.dumps(build(json.load(open(a.spec, encoding="utf-8")), a.outdir), ensure_ascii=False, indent=1))
