#!/usr/bin/env python3
"""template_audit.py — 模板结构盘点: 母版/版式/占位符/主题字体/主题色。

用法: python3 template_audit.py <template.pptx> [out_report.json]
用途: 生成 deck 前先"摸清模板", 报告写入 work 目录, 作为槽位填充依据。
检查/报告:
  - 幻灯片尺寸; 母版数量; 每母版下每个版式的名称与占位符(idx/type/名称);
  - 主题字体(majorFont/minorFont 的 latin+ea)与主题色(前12个颜色);
  - 若无占位符版式占比过高, 在 warnings 中提示"占位符不足, 需替代方案"。
退出码: 0 成功; 2 文件缺失/损坏。
"""
import json
import os
import re
import sys
import zipfile


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: template_audit.py tpl.pptx [report.json]"}))
        sys.exit(2)
    tpl = sys.argv[1]
    if not os.path.isfile(tpl):
        print(json.dumps({"ok": False, "error": "template missing"}))
        sys.exit(2)
    try:
        from pptx import Presentation
        from pptx.util import Emu
        prs = Presentation(tpl)
    except Exception as e:
        print(json.dumps({"ok": False, "error": "template broken: %s" % e}))
        sys.exit(2)
    report = {"template": os.path.basename(tpl),
              "slide_size": {"w_emu": prs.slide_width, "h_emu": prs.slide_height},
              "existing_slides": len(prs.slides),
              "masters": [], "warnings": []}
    for master in prs.slide_masters:
        m = {"layouts": []}
        for lay in master.slide_layouts:
            phs = []
            for ph in lay.placeholders:
                phs.append({"idx": ph.placeholder_format.idx,
                            "type": str(ph.placeholder_format.type),
                            "name": ph.name})
            m["layouts"].append({"name": lay.name, "placeholders": phs,
                                 "n_placeholders": len(phs)})
        report["masters"].append(m)
    # 主题字体与颜色
    try:
        with zipfile.ZipFile(tpl) as z:
            names = [n for n in z.namelist() if re.match(r"ppt/theme/theme\d+\.xml", n)]
            if names:
                xml = z.read(names[0]).decode("utf-8", "ignore")
                fonts = {}
                for tag in ("majorFont", "minorFont"):
                    m1 = re.search(r"<a:%s>.*?</a:%s>" % (tag, tag), xml, re.S)
                    if m1:
                        latin = re.search(r'<a:latin typeface="([^"]*)"', m1.group(0))
                        ea = re.search(r'<a:ea typeface="([^"]*)"', m1.group(0))
                        fonts[tag] = {"latin": latin.group(1) if latin else None,
                                      "ea": ea.group(1) if ea else None}
                report["theme_fonts"] = fonts
                report["theme_colors"] = re.findall(r'<a:srgbClr val="([0-9A-Fa-f]{6})"/>', xml)[:12]
    except Exception as e:
        report["warnings"].append("theme parse failed: %s" % e)
    # 占位符不足提示
    lays = [l for m in report["masters"] for l in m["layouts"]]
    if lays:
        empty = sum(1 for l in lays if l["n_placeholders"] == 0)
        if empty / len(lays) > 0.3:
            report["warnings"].append(
                "%d/%d 版式无占位符, 文本需用文本框替代方案" % (empty, len(lays)))
    out = sys.argv[2] if len(sys.argv) > 2 else None
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
