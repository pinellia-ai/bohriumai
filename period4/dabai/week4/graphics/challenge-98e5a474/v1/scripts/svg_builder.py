#!/usr/bin/env python3
"""svg_builder.py — 从 diagram spec JSON 生成分层可编辑 SVG + PNG/PDF 导出件。

spec 格式（JSON）：
{
  "canvas": {"width": 900, "height": 600, "title": "figure-name"},
  "nodes": [{"id":"n-receptor","x":100,"y":80,"w":180,"h":60,"label":"EGFR",
             "shape":"rect|circle","fill":"#dbe9f6","source":"材料§3 p2: 'EGFR激活'"}],
  "edges": [{"id":"e-1","from":"n-receptor","to":"n-raf","type":"activate|inhibit|neutral",
             "label":"磷酸化","source":"材料§3 p2"}],
  "texts": [{"id":"t-title","x":450,"y":30,"s":"标题","size":18,"bold":true,"source":"..."}],
  "legend": [{"id":"lg-1","kind":"arrow","type":"activate","label":"激活","source":"..."}],
  "export": {"png_dpi": 300, "pdf": true, "max_width_in": 7.5}
}
edges 坐标由节点中心自动计算（在边上留 1/2 短半轴间距）。来源缺失的元素 source 必须写 "unverified"。
"""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core_g import Canvas, png_to_pdf, FONT_DEFAULT
from raster import build_png

MARK = {"activate": "arrow-activate", "inhibit": "arrow-inhibit", "neutral": "arrow-neutral"}
COLR = {"activate": "#1a1a1a", "inhibit": "#c0392b", "neutral": "#555555"}


def _anchor(n, side):
    cx, cy = n["x"] + n.get("w", 0) / 2, n["y"] + n.get("h", 0) / 2
    if side == "left":  return n["x"], cy
    if side == "right": return n["x"] + n.get("w", 0), cy
    if side == "top":   return cx, n["y"]
    if side == "bottom":return cx, n["y"] + n.get("h", 0)
    return cx, cy


def build(spec, outdir):
    c = Canvas(spec["canvas"]["width"], spec["canvas"]["height"], spec["canvas"].get("title", "figure"),
               spec["canvas"].get("bg", "#ffffff"))
    nodes = {n["id"]: n for n in spec.get("nodes", [])}
    idx = {nid: i for i, nid in enumerate(nodes)}
    font = spec["canvas"].get("font", FONT_DEFAULT)

    # 背景：可选分区（compartments）
    for comp in spec.get("compartments", []):
        c.rect("background", comp["x"], comp["y"], comp["w"], comp["h"], fill=comp.get("fill", "#f6f8fa"),
               stroke=comp.get("stroke", "#9aa5b1"), sw=1.2, rx=8, elem_id=comp["id"], source=comp.get("source", "unverified"))
        if comp.get("label"):
            c.text("background", comp["x"] + comp["w"] / 2, comp["y"] + 16, comp["label"], size=comp.get("label_size", 13),
                   bold=True, fill="#444", elem_id=comp["id"] + "-label", source=comp.get("source", "unverified"), font=font)

    # 边（画在节点下层）
    for e in spec.get("edges", []):
        a, b = nodes[e["from"]], nodes[e["to"]]
        # 自动选边：按相对位置
        dx, dy = (b["x"] + b.get("w", 0) / 2) - (a["x"] + a.get("w", 0) / 2), (b["y"] + b.get("h", 0) / 2) - (a["y"] + a.get("h", 0) / 2)
        if abs(dx) >= abs(dy):
            s = _anchor(a, "right" if dx > 0 else "left"); t = _anchor(b, "left" if dx > 0 else "right")
        else:
            s = _anchor(a, "bottom" if dy > 0 else "top"); t = _anchor(b, "top" if dy > 0 else "bottom")
        typ = e.get("type", "neutral")
        c.line("structure", s[0], s[1], t[0], t[1], stroke=COLR.get(typ, "#1a1a1a"), sw=e.get("width", 1.8),
               dash=e.get("dash", ""), marker=MARK.get(typ, MARK["neutral"]), elem_id=e["id"], source=e.get("source", "unverified"))
        if e.get("label"):
            mx, my = (s[0] + t[0]) / 2, (s[1] + t[1]) / 2 - 5
            c.text("annotation", mx, my, e["label"], size=e.get("label_size", 11), fill="#333",
                   elem_id=e["id"] + "-label", source=e.get("source", "unverified"), font=font)

    # 节点
    for n in spec.get("nodes", []):
        shp = n.get("shape", "rect")
        if shp == "circle":
            r = n.get("r", max(n.get("w", 40), n.get("h", 40)) / 2)
            c.circle("structure", n["x"], n["y"], r, fill=n.get("fill", "#dbe9f6"), stroke=n.get("stroke", "#2c5f8a"),
                     sw=n.get("sw", 1.8), elem_id=n["id"], source=n.get("source", "unverified"))
            c.text("annotation", n["x"], n["y"] + 4, n.get("label", ""), size=n.get("size", 12), bold=n.get("bold", False),
                   elem_id=n["id"] + "-label", source=n.get("source", "unverified"), font=font)
        else:
            c.rect("structure", n["x"], n["y"], n.get("w", 160), n.get("h", 50), fill=n.get("fill", "#dbe9f6"),
                   stroke=n.get("stroke", "#2c5f8a"), sw=n.get("sw", 1.8), rx=n.get("rx", 6), elem_id=n["id"], source=n.get("source", "unverified"))
            c.text("annotation", n["x"] + n.get("w", 160) / 2, n["y"] + n.get("h", 50) / 2 + n.get("size", 12) * 0.35,
                   n.get("label", ""), size=n.get("size", 12), bold=n.get("bold", False),
                   elem_id=n["id"] + "-label", source=n.get("source", "unverified"), font=font)

    # 独立文字
    for t in spec.get("texts", []):
        c.text("annotation", t["x"], t["y"], t["s"], size=t.get("size", 12), anchor=t.get("anchor", "middle"),
               bold=t.get("bold", False), fill=t.get("fill", "#111"), elem_id=t["id"], source=t.get("source", "unverified"), font=font)

    # 图例
    lg = spec.get("legend", [])
    if lg:
        lx, ly = spec["canvas"]["width"] - spec.get("legend_box", {}).get("w", 190) - 12, 12
        bw, bh = spec.get("legend_box", {}).get("w", 190), 18 + 20 * len(lg)
        c.rect("legend", lx, ly, bw, bh, fill="#ffffff", stroke="#bbb", sw=1, rx=4, elem_id="legend-box", source="figure-own")
        for i, it in enumerate(lg):
            yy = ly + 16 + i * 20
            if it.get("kind") == "arrow":
                typ = it.get("type", "neutral")
                c.line("legend", lx + 10, yy + 4, lx + 46, yy + 4, stroke=COLR.get(typ, "#1a1a1a"), sw=1.8,
                       marker=MARK.get(typ, MARK["neutral"]), elem_id=f"lg-{i}-glyph", source=it.get("source", "figure-own"))
            else:
                c.rect("legend", lx + 14, yy - 3, 26, 12, fill=it.get("fill", "#dbe9f6"), stroke="#555", sw=1,
                       elem_id=f"lg-{i}-glyph", source=it.get("source", "figure-own"))
            c.text("legend", lx + 54, yy + 8, it.get("label", ""), size=11, anchor="start",
                   elem_id=f"lg-{i}-text", source=it.get("source", "unverified"), font=font)

    os.makedirs(outdir, exist_ok=True)
    base = spec["canvas"].get("title", "figure").replace(" ", "_")
    svg_path = os.path.join(outdir, base + ".svg")
    c.save(svg_path)
    result = {"svg": svg_path}
    ex = spec.get("export", {})
    png_path = os.path.join(outdir, base + ".png")
    r = build_png(spec, png_path, dpi=ex.get("png_dpi", 300))
    result["png"] = png_path
    result["png_rendered"] = True
    result["png_px"] = r["px"]
    result["font_used"] = r["font_used"]
    if ex.get("pdf", True):
        miw = ex.get("max_width_in", 7.5)
        pw_pt = min(miw * 72, spec["canvas"]["width"] * 0.75)
        ph_pt = pw_pt * spec["canvas"]["height"] / spec["canvas"]["width"]
        result["pdf"] = png_to_pdf(png_path, os.path.join(outdir, base + ".pdf"), pw_pt, ph_pt)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    print(json.dumps(build(json.load(open(a.spec, encoding="utf-8")), a.outdir), ensure_ascii=False, indent=1))
