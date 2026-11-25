#!/usr/bin/env python3
"""core_g.py — 科研图稿 SVG 原语库（纯标准库）。

设计原则：
1. 每个图元必须有 id 与 data-source（来源定位），保证"元素→材料位置"可核验。
2. 文字一律用 <text> 节点（不转曲），font-family 显式声明，可编辑可替换。
3. 分层：背景层 <g id="layer-background">、结构层、数据层、标注层、图例层。
4. 依赖：仅 Python 标准库。渲染 PNG 依赖 Pillow（缺失时跳过 PNG 并在日志标注）。
"""
import json, math, os, html

FONT_DEFAULT = "Helvetica, Arial, sans-serif"
FONT_CJK_FALLBACK = "PingFang SC, Noto Sans CJK SC, SimHei, sans-serif"

class Canvas:
    def __init__(self, width, height, title="figure", bg="#ffffff"):
        self.w, self.h = width, height
        self.title = title
        self.layers = {"background": [], "structure": [], "data": [], "annotation": [], "legend": []}
        self.bg = bg

    # ---- 原语 ----
    def rect(self, layer, x, y, w, h, fill="none", stroke="#333", sw=1.5, rx=0, elem_id="", source="", extra=""):
        s = f'<rect id="{elem_id}" data-source="{html.escape(source)}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
        self.layers[layer].append(s)

    def circle(self, layer, cx, cy, r, fill="#fff", stroke="#333", sw=1.5, elem_id="", source="", extra=""):
        s = f'<circle id="{elem_id}" data-source="{html.escape(source)}" cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
        self.layers[layer].append(s)

    def line(self, layer, x1, y1, x2, y2, stroke="#333", sw=1.5, dash="", marker="", elem_id="", source=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = f' marker-end="url(#{marker})"' if marker else ""
        s = f'<line id="{elem_id}" data-source="{html.escape(source)}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"{d}{m}/>'
        self.layers[layer].append(s)

    def path(self, layer, d, stroke="#333", sw=1.5, fill="none", marker="", elem_id="", source=""):
        m = f' marker-end="url(#{marker})"' if marker else ""
        s = f'<path id="{elem_id}" data-source="{html.escape(source)}" d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{m}/>'
        self.layers[layer].append(s)

    def text(self, layer, x, y, s_, size=12, anchor="middle", fill="#111", bold=False, elem_id="", source="", font=FONT_DEFAULT):
        w = ' font-weight="bold"' if bold else ""
        t = f'<text id="{elem_id}" data-source="{html.escape(source)}" x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" text-anchor="{anchor}" fill="{fill}"{w}>{html.escape(s_)}</text>'
        self.layers[layer].append(t)

    # ---- 箭头 marker（激活=实心三角，抑制=T形端点，需要时由 SKILL 流程选定） ----
    def markers(self):
        return (
            '<defs>'
            '<marker id="arrow-activate" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1a1a1a"/></marker>'
            '<marker id="arrow-inhibit" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto"><line x1="0" y1="5" x2="9" y2="5" stroke="#1a1a1a" stroke-width="2"/></marker>'
            '<marker id="arrow-neutral" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9" fill="none" stroke="#1a1a1a" stroke-width="1.4"/></marker>'
            '</defs>')

    def svg(self):
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">',
                 f'<title>{html.escape(self.title)}</title>', self.markers(),
                 f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{self.bg}"/>']
        order = ["background", "structure", "data", "annotation", "legend"]
        for name in order:
            if self.layers[name]:
                parts.append(f'<g id="layer-{name}">')
                parts.extend(self.layers[name])
                parts.append('</g>')
        parts.append('</svg>')
        return "\n".join(parts)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.svg())
        return path


def render_png(svg_path, png_path, dpi=300, scale=None):
    """SVG→PNG。Pillow 不直接支持 SVG，采用简单光栅化兜底：
    优先调用系统 rsvg-convert / inkscape / cairosvg；都不可用时生成占位 PNG 并返回 False。
    评测环境（scientific-python）若可用 cairosvg 则自动使用。"""
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=svg_path, write_to=png_path, scale=(scale or dpi / 96))
        return True
    except Exception:
        pass
    for cmd in (["rsvg-convert", "-d", str(dpi), "-p", str(dpi), svg_path, "-o", png_path],
                ["inkscape", svg_path, "--export-type=png", f"--export-filename={png_path}", f"--export-dpi={dpi}"]):
        try:
            import subprocess
            r = subprocess.run(cmd, capture_output=True, timeout=60)
            if r.returncode == 0 and os.path.exists(png_path):
                return True
        except Exception:
            continue
    try:
        from PIL import Image
        w = int((scale or dpi / 96) * 100)
        img = Image.new("RGB", (w, max(40, w // 4)), "white")
        img.save(png_path, dpi=(dpi, dpi))
        return False  # 占位：真实渲染失败，调用方必须如实记录
    except Exception:
        return False


def png_to_pdf(png_path, pdf_path, page_w_pt=540, page_h_pt=720):
    """把 PNG 包进单页 PDF（Image XObject，DCTDecode 不适用 PNG，用 FlateDecode 走 zlib）。
    纯标准库实现，保证导出 PDF 真实存在。"""
    import zlib, struct
    from PIL import Image
    img = Image.open(png_path).convert("RGB")
    w, h = img.size
    raw = img.tobytes()
    data = zlib.compress(raw)
    # Content stream: draw image scaled to page
    content = f"q {page_w_pt} 0 0 {page_h_pt} 0 0 cm /Im0 Do Q".encode()
    objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w_pt} {page_h_pt}] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>".encode())
    objs.append(f"<< /Type /XObject /Subtype /Image /Width {w} /Height {h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(data)} >>".encode() + b"\nstream\n" + data + b"\nendstream")
    objs.append(f"<< /Length {len(content)} >>".encode() + b"\nstream\n" + content + b"\nendstream")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    with open(pdf_path, "wb") as f:
        f.write(bytes(out))
    return pdf_path


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
