#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学术著作阅读版 PDF 交付前机械核验（《规范》第四节（一）、第八节第 3 条）。

用法：
    python 核验_阅读版.py 成品.pdf [-o 报告.txt] [--params 版式参数_156×235.json] [--key 156×235]

检查项（结果写 UTF-8 报告，逐条人工判断；不改 PDF）：
  1. 页数、页面尺寸、PDF 元数据；
  2. 嵌入字体清单与"意外字体"（多为缺字回退）；
  3. 每页脚注注区编号是否自 ① 起连续；
  4. 实测行距（基线距）众数，对照版式参数；
  5. 半页以下空白的页清单（章末页/编扉页/末页属正常，其余须说明）；
  6. 目录页码与 PDF 书签目标页是否一一对应；
  7. 书签层级与条数；
  8. 正文越出版心的行（页眉页脚不计）。
依赖：pymupdf（pip install pymupdf）。
"""
import argparse, collections, io, json, re, sys
from pathlib import Path

import pymupdf

# 允许的嵌入字体（前缀或子串匹配）；配置里可追加"封面字体"
ALLOWED = ("SimSun", "SimHei", "FangSong", "KaiTi", "STZhongsong", "STSong",
           "TimesNewRoman", "MS-Mincho", "MSMincho", "SourceHanSerif", "NotoSerif")

CIRC = {chr(x): x - 0x2460 + 1 for x in range(0x2460, 0x2474)}          # ①—⑳
CIRC.update({chr(x): x - 0x3251 + 21 for x in range(0x3251, 0x3260)})   # ㉑—㉟
CIRC.update({chr(x): x - 0x32B1 + 36 for x in range(0x32B1, 0x32C0)})   # ㊱—㊿


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--params", default=None, help="版式参数 json（默认取同目录 版式参数_156×235.json）")
    ap.add_argument("--key", default="156×235", help="版式参数里的一套名字")
    a = ap.parse_args()

    pdf = Path(a.pdf)
    out = Path(a.out) if a.out else pdf.with_suffix(".核验报告.txt")
    d = pymupdf.open(str(pdf))
    f = io.open(out, "w", encoding="utf-8")
    W = f.write

    # 版式参数
    params = {}
    pj = Path(a.params) if a.params else Path(__file__).with_name("版式参数_156×235.json")
    if pj.exists():
        try:
            params = json.loads(pj.read_text(encoding="utf-8")).get(a.key, {})
        except Exception as e:
            W("（版式参数读取失败：%s）\n" % e)
    body_lh = params.get("正文行距pt")
    note_lh = params.get("脚注行距pt")
    pw, ph = params.get("页宽mm"), params.get("页高mm")

    W("核验对象：%s\n\n" % pdf.name)
    W("=== 1. 版面 ===\n")
    p0 = d[0]
    W("页数 %d；尺寸 %.1f × %.1f mm%s\n" % (
        d.page_count, p0.rect.width / 72 * 25.4, p0.rect.height / 72 * 25.4,
        "" if not (pw and ph) else ("（期望 %.0f × %.0f %s）" % (
            pw, ph, "✓" if abs(p0.rect.width / 72 * 25.4 - pw) < 0.6 and abs(p0.rect.height / 72 * 25.4 - ph) < 0.6 else "✗"))))
    W("元数据 title=%r author=%r\n" % (d.metadata.get("title"), d.metadata.get("author")))

    W("\n=== 2. 嵌入字体 ===\n")
    fonts = collections.Counter()
    for pg in d:
        for x in pg.get_fonts():
            fonts[x[3].split("+")[-1]] += 1
    for name, cnt in sorted(fonts.items()):
        W("  %-42s %d\n" % (name, cnt))
    odd = [n for n in fonts if not any(t in n or n.startswith(t) for t in ALLOWED)]
    W("  意外字体：%s\n" % (odd if odd else "无（无回退）"))

    W("\n=== 3. 每页脚注注区编号 ===\n")
    bad = []
    for pno in range(d.page_count):
        pg = d[pno]
        h = pg.rect.height
        nums = []
        for blk in pg.get_text("dict")["blocks"]:
            for ln in blk.get("lines", []):
                if ln["bbox"][1] < h * 0.62:      # 只看页下 38%
                    continue
                txt = "".join(s["text"] for s in ln["spans"]).strip()
                if txt and txt[0] in CIRC and (len(txt) == 1 or txt[1] not in CIRC):
                    nums.append(CIRC[txt[0]])
        if nums and nums != list(range(1, len(nums) + 1)):
            bad.append((pno + 1, nums[:10]))
    W("  不从①起连续的页 %d 个：%s\n" % (len(bad), bad[:20] if bad else "无"))
    if bad:
        W("  说明：长注跳行会造成误报，请渲染这些页目视确认。\n")

    W("\n=== 4. 实测行距（基线距众数）===\n")
    sp = collections.Counter()
    for pg in d:
        ys = sorted(ln["bbox"][1] for blk in pg.get_text("dict")["blocks"] for ln in blk.get("lines", []))
        for x, y in zip(ys, ys[1:]):
            if 4 < y - x < 30:
                sp[round(y - x, 1)] += 1
    W("  众数(pt)：%s\n" % sp.most_common(6))
    if body_lh:
        W("  期望：正文 %.1f pt、脚注 %.1f pt\n" % (body_lh, note_lh or 0))

    W("\n=== 5. 半页以下空白的页 ===\n")
    short = []
    for pno in range(d.page_count):
        pg = d[pno]
        h = pg.rect.height
        ys = [ln["bbox"][3] for blk in pg.get_text("dict")["blocks"] for ln in blk.get("lines", [])]
        frac = (max(ys) / h) if ys else 0.0
        if frac < 0.55:
            short.append((pno + 1, round(frac, 2)))
    W("  %d 页：%s\n" % (len(short), short[:40]))
    W("  说明：章末页、编扉页、封面、全书末页属正常；其余须逐一说明。\n")

    W("\n=== 6. 目录页码 vs 书签目标页 ===\n")
    toc = d.get_toc()
    W("  书签 %d 条，层级 1–%d\n" % (len(toc), max((t[0] for t in toc), default=0)))
    toc_pages = [p for p in range(min(14, d.page_count)) if " . " in d[p].get_text() or ". . ." in d[p].get_text()]
    W("  疑似目录页（1-based）：%s\n" % [p + 1 for p in toc_pages])
    entries = []
    for p in toc_pages:
        for line in d[p].get_text().split("\n"):
            s = line.strip()
            m = re.search(r"([ivxlcdm]+|\d+)\s*$", s)
            if m and " . " in s:
                title = s[: s.index(" . ")].strip().rstrip(".·\u3000 ")
                entries.append((title, m.group(1)))
    W("  目录条目 %d 条（目录自身不进目录，故比书签少 1 为正常）\n" % len(entries))
    # 按出现顺序与书签逐条对齐（同名标题如“结语”会出现多次，不能用字典按名匹配）
    book_list = [(t.strip(), p) for _, t, p in toc]
    matched, miss, bi = [], [], 0
    for t, v in entries:
        j = bi
        while j < len(book_list) and book_list[j][0] != t:
            j += 1
        if j < len(book_list):
            matched.append((t, v, book_list[j][1]))
            bi = j + 1
        else:
            miss.append(t)
    W("  顺序对齐成功 %d 条，未对上 %d 条%s\n" % (
        len(matched), len(miss), ("：" + "、".join(miss[:6])) if miss else ""))
    # 阿拉伯页码条目：书签页 − 目录页码 应为常数
    diffs = collections.Counter()
    for t, v, pg in matched:
        if v.isdigit():
            diffs[pg - int(v)] += 1
    W("  阿拉伯页码条目 %d 条；偏移（书签页−目录页）分布：%s\n" % (sum(diffs.values()), diffs.most_common(5)))
    if len(diffs) <= 1:
        W("  → 目录页码与正文页码一致 ✓\n")
    else:
        base = diffs.most_common(1)[0][0]
        bad2 = [(t, v, pg) for t, v, pg in matched if v.isdigit() and pg - int(v) != base]
        W("  → 偏移不一致 %d 条：%s\n" % (len(bad2), bad2[:10]))
    # 罗马页码条目：目标页应落在正文之前
    romans = [(t, v) for t, v in entries if not v.isdigit()]
    W("  罗马页码条目 %d 条：%s\n" % (len(romans), romans))


    W("\n=== 7. 越出版心的行（页眉页脚不计）===\n")
    if pw and ph:
        left, right = 20 * 72 / 25.4 - 3 * 72 / 25.4, (pw - 20) * 72 / 25.4 + 3 * 72 / 25.4
        top, bottom = 23 * 72 / 25.4 - 14 * 72 / 25.4, (ph - 18) * 72 / 25.4 + 3 * 72 / 25.4
        over = []
        for pno in range(d.page_count):
            for blk in d[pno].get_text("dict")["blocks"]:
                for ln in blk.get("lines", []):
                    x0, y0, x1, y1 = ln["bbox"]
                    if y1 < 23 * 72 / 25.4 or y0 > (ph - 18) * 72 / 25.4:   # 页眉区、页脚区跳过
                        continue
                    if x0 < left or x1 > right or y1 > bottom:
                        txt = "".join(s["text"] for s in ln["spans"])[:30]
                        over.append((pno + 1, round(x0, 1), round(x1, 1), txt))
        W("  %d 行越界：%s\n" % (len(over), over[:12]))
    else:
        W("  缺版式参数，跳过。\n")

    W("\n=== 8. 图片 ===\n")
    W("  图片对象 %d 个（封面等）\n" % sum(len(pg.get_images()) for pg in d))
    f.close()
    print("核验完成 ->", out)


if __name__ == "__main__":
    main()
