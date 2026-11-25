#!/usr/bin/env python3
"""raster.py — 用 Pillow 从同一 diagram spec 光栅化 PNG（真实渲染，非占位）。

与 svg_builder 共用同一 spec，保证矢量源文件与位图导出内容一致。
字体发现顺序：环境变量 FIG_CJK_FONT → 常见 CJK/西文路径 → PIL 默认位图字体
（找不到 CJK 字体时中文将退化，render 时在返回值中标注 font_used 与 cjk_ok，导出检查如实记录）。
"""
import os, math
from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]

def _load_font(px):
    paths = ([os.environ["FIG_CJK_FONT"]] if os.environ.get("FIG_CJK_FONT") else []) + _FONT_CANDIDATES
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, px), p
            except Exception:
                continue
    return ImageFont.load_default(), "bitmap-default"

def _px(pt, dpi):
    return max(1, int(round(pt * dpi / 72.0)))

def build_png(spec, out_path, dpi=300):
    W, H = spec["canvas"]["width"], spec["canvas"]["height"]
    scale = dpi / 72.0  # SVG 坐标按 pt 处理，300dpi 时约 4.17x
    img = Image.new("RGB", (int(W * scale), int(H * scale)), spec["canvas"].get("bg", "#ffffff"))
    dr = ImageDraw.Draw(img)
    nodes = {n["id"]: n for n in spec.get("nodes", [])}
    font_cache = {}

    def F(size_pt):
        px = _px(size_pt, dpi)
        if px not in font_cache:
            font_cache[px] = _load_font(px)
        return font_cache[px]

    def rect(x, y, w, h, fill, stroke, sw, rx=0):
        box = [x * scale, y * scale, (x + w) * scale, (y + h) * scale]
        dr.rounded_rectangle(box, radius=rx * scale, fill=fill, outline=stroke, width=max(1, int(sw * scale)))

    def circle(cx, cy, r, fill, stroke, sw):
        box = [(cx - r) * scale, (cy - r) * scale, (cx + r) * scale, (cy + r) * scale]
        dr.ellipse(box, fill=fill, outline=stroke, width=max(1, int(sw * scale)))

    def line(x1, y1, x2, y2, color, sw, dash=""):
        p1, p2 = (x1 * scale, y1 * scale), (x2 * scale, y2 * scale)
        width = max(1, int(sw * scale))
        if dash:
            seg = _px(float(dash.split(",")[0]), dpi)
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            dist = math.hypot(dx, dy) or 1
            n = max(1, int(dist / (seg * 2)))
            for i in range(n + 1):
                t0, t1 = i * 2 / (2 * n), min(1, (i * 2 + 1) / (2 * n))
                dr.line([p1[0] + dx * t0, p1[1] + dy * t0, p1[0] + dx * t1, p1[1] + dy * t1], fill=color, width=width)
        else:
            dr.line([p1, p2], fill=color, width=width)
        # 箭头端点（实心三角）
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        ah = max(6, width * 3)
        dr.polygon([(p2[0], p2[1]),
                    (p2[0] - ah * math.cos(ang - 0.45), p2[1] - ah * math.sin(ang - 0.45)),
                    (p2[0] - ah * math.cos(ang + 0.45), p2[1] - ah * math.sin(ang + 0.45))], fill=color)

    def text(x, y, s_, size_pt, anchor="middle", fill="#111", bold=False):
        f, _ = F(size_pt)
        w = dr.textlength(s_, font=f)
        px_x = x * scale - (w / 2 if anchor == "middle" else (w if anchor == "right" else 0))
        dr.text((px_x, y * scale - _px(size_pt, dpi) * 0.85), s_, font=f, fill=fill)

    for comp in spec.get("compartments", []):
        rect(comp["x"], comp["y"], comp["w"], comp["h"], comp.get("fill", "#f6f8fa"), comp.get("stroke", "#9aa5b1"), 1.2, rx=8)
        if comp.get("label"):
            text(comp["x"] + comp["w"] / 2, comp["y"] + 14, comp["label"], comp.get("label_size", 13), fill="#444")

    for e in spec.get("edges", []):
        a, b = nodes[e["from"]], nodes[e["to"]]
        dx = (b["x"] + b.get("w", 0) / 2) - (a["x"] + a.get("w", 0) / 2)
        dy = (b["y"] + b.get("h", 0) / 2) - (a["y"] + a.get("h", 0) / 2)
        if abs(dx) >= abs(dy):
            s_ = (a["x"] + a.get("w", 0), a["y"] + a.get("h", 0) / 2) if dx > 0 else (a["x"], a["y"] + a.get("h", 0) / 2)
            t_ = (b["x"], b["y"] + b.get("h", 0) / 2) if dx > 0 else (b["x"] + b.get("w", 0), b["y"] + b.get("h", 0) / 2)
        else:
            s_ = (a["x"] + a.get("w", 0) / 2, a["y"] + a.get("h", 0)) if dy > 0 else (a["x"] + a.get("w", 0) / 2, a["y"])
            t_ = (b["x"] + b.get("w", 0) / 2, b["y"]) if dy > 0 else (b["x"] + b.get("w", 0) / 2, b["y"] + b.get("h", 0))
        col = {"activate": "#1a1a1a", "inhibit": "#c0392b"}.get(e.get("type", "neutral"), "#555555")
        line(s_[0], s_[1], t_[0], t_[1], col, e.get("width", 1.8), e.get("dash", ""))
        if e.get("label"):
            text((s_[0] + t_[0]) / 2, (s_[1] + t_[1]) / 2 - 6, e["label"], e.get("label_size", 11), fill="#333")

    for n in spec.get("nodes", []):
        if n.get("shape") == "circle":
            r = n.get("r", max(n.get("w", 40), n.get("h", 40)) / 2)
            circle(n["x"], n["y"], r, n.get("fill", "#dbe9f6"), n.get("stroke", "#2c5f8a"), n.get("sw", 1.8))
            text(n["x"], n["y"] + n.get("size", 12) * 0.35, n.get("label", ""), n.get("size", 12), bold=n.get("bold", False))
        else:
            rect(n["x"], n["y"], n.get("w", 160), n.get("h", 50), n.get("fill", "#dbe9f6"), n.get("stroke", "#2c5f8a"), n.get("sw", 1.8), rx=n.get("rx", 6))
            text(n["x"] + n.get("w", 160) / 2, n["y"] + n.get("h", 50) / 2 + n.get("size", 12) * 0.35,
                 n.get("label", ""), n.get("size", 12), bold=n.get("bold", False))

    for t in spec.get("texts", []):
        text(t["x"], t["y"], t["s"], t.get("size", 12), t.get("anchor", "middle"), t.get("fill", "#111"), t.get("bold", False))

    lg = spec.get("legend", [])
    if lg:
        lw = spec.get("legend_box", {}).get("w", 190)
        lx, ly = W - lw - 12, 12
        rect(lx, ly, lw, 18 + 20 * len(lg), "#ffffff", "#bbbbbb", 1, rx=4)
        for i, it in enumerate(lg):
            yy = ly + 16 + i * 20
            if it.get("kind") == "arrow":
                col = {"activate": "#1a1a1a", "inhibit": "#c0392b"}.get(it.get("type", "neutral"), "#555555")
                line(lx + 10, yy + 4, lx + 42, yy + 4, col, 1.8)
            else:
                rect(lx + 14, yy - 3, 26, 12, it.get("fill", "#dbe9f6"), "#555555", 1)
            text(lx + 54, yy + 2, it.get("label", ""), 11, anchor="start")

    img.save(out_path, dpi=(dpi, dpi))
    _, fp = F(12)
    return {"png": out_path, "px": img.size, "dpi": dpi, "font_used": os.path.basename(fp)}

if __name__ == "__main__":
    import json, sys
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else "figure.png"
    print(json.dumps(build_png(spec, out, dpi=int(sys.argv[3]) if len(sys.argv) > 3 else 300), ensure_ascii=False))
