#!/usr/bin/env python3
"""export_check.py — 导出合规校验（交付前必跑，全部 PASS 才算完成）。

检查项：
 1. SVG 存在且可解析；text 节点存在（文字未转曲，可编辑）
 2. 每个可见图元（rect/circle/line/path）带 id 与 data-source；data-source 不得为空
 3. 分层结构：layer-background/structure/data/annotation/legend 至少出现 structure 与 annotation
 4. font-family 显式声明（可替换字体）
 5. 图例项数与 legend spec 一致（传入 --legend-n）
 6. PNG 存在且像素尺寸 >= --min-px（默认 1500）
 7. PDF 存在且以 %PDF 开头
输出 JSON：{"pass": bool, "checks": [...] }，任一 FAIL 则整体 fail（exit 1）。
"""
import argparse, json, os, re, sys

def check(svg, png=None, pdf=None, min_px=1500, legend_n=None):
    res = []
    ok = True
    def add(name, passed, detail=""):
        nonlocal ok
        res.append({"check": name, "result": "PASS" if passed else "FAIL", "detail": detail})
        if not passed: ok = False

    if not os.path.exists(svg):
        add("svg_exists", False, svg); return {"pass": False, "checks": res}
    s = open(svg, encoding="utf-8").read()
    # 排除基础设施图元：<defs>（marker 等）与画布底 rect
    s_chk = re.sub(r"<defs>.*?</defs>", "", s, flags=re.S)
    s_chk = re.sub(r'<rect x="0" y="0" width="[^"]*" height="[^"]*" fill="[^"]*"\s*/>', "", s_chk)
    add("svg_exists", True, svg)
    n_text = len(re.findall(r"<text\b", s))
    add("text_editable", n_text > 0, f"text nodes={n_text}（未转曲）")
    glyphs = [m.group(0) for m in re.finditer(r"<(?:rect|circle|line|path)\b[^>]*>", s_chk)]
    no_id = [g[:40] for g in glyphs if 'id="' not in g]
    add("elements_have_id", len(no_id) == 0, f"{len(glyphs)} glyphs, {len(no_id)} missing id")
    no_src = [g[:40] for g in glyphs if 'data-source="' not in g]
    add("elements_have_source", len(no_src) == 0, f"{len(no_src)} missing data-source")
    empty_src = s.count('data-source=""')
    add("source_nonempty", empty_src == 0, f"{empty_src} empty data-source")
    layers_ok = ('id="layer-structure"' in s or 'id="layer-data"' in s) and 'id="layer-annotation"' in s
    add("layered_structure", layers_ok, "structure/data + annotation layers")
    fonts = re.findall(r'font-family="([^"]+)"', s)
    add("font_declared", len(fonts) > 0, "font-family declared on text" if fonts else "no font-family")
    if legend_n is not None:
        n_lg = len(re.findall(r'<(?:rect|line|circle|path)[^>]*id="lg-\d+-glyph"', s))
        add("legend_count", n_lg == legend_n, f"legend glyphs={n_lg}, expected={legend_n}")

    if png:
        if os.path.exists(png):
            try:
                from PIL import Image
                w, h = Image.open(png).size
                add("png_size", max(w, h) >= min_px, f"{w}x{h}px (min {min_px})")
            except Exception as e:
                add("png_size", False, str(e))
        else:
            add("png_exists", False, "PNG missing（渲染失败需如实标注 partial）")
    if pdf:
        exists = os.path.exists(pdf)
        head = open(pdf, "rb").read(5) == b"%PDF-" if exists else False
        add("pdf_valid", exists and head, pdf if not (exists and head) else "")

    return {"pass": ok, "checks": res}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", required=True); ap.add_argument("--png"); ap.add_argument("--pdf")
    ap.add_argument("--min-px", type=int, default=1500); ap.add_argument("--legend-n", type=int)
    a = ap.parse_args()
    out = check(a.svg, a.png, a.pdf, a.min_px, a.legend_n)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)
