# -*- coding: utf-8 -*-
"""【参考实现】Markdown 译文主稿 → Typst 正文（学术专著阅读版 · 156×235）。

本文件是技能 academic-typesetting-typst 的转换器参考实现，来自一本真实学术专著的排版实践，
可直接复制到新项目里改。适配新书时至少要改的四处：
  1. 配置里的 `主稿`、`人名书名表`、`输出PDF` 路径；
  2. `正文起始标题`（首编/首章标题，它决定阿拉伯页码从哪页起）；
  3. `读者版略去整个标题区块`（一般是 ["目录", "注释"]）；
  4. 前置页部分（FRONT_PAGES / front_bucket / fp-* 调用）——按底本前置页结构删改；无“编”的书删掉 PART_RE 与 parthd 分支。

以下为原有说明：
"""
"""《非洲与国际体系》译文主稿 → Typst 正文（项目专用）。

在《规范》通用 md2typ.py 基础上做的事（只做格式转换，不改文字）：
  1. 前置页：原书第 I（内容简介）、III（丛书页）、IV（丛书书目）、V（书名页）、VI（版权页）；
  2. 编扉页：`## 第X编　……` 排成另页居中的编扉页（第一编起改用阿拉伯页码 1）；
  3. 缩略语表：两条一组（缩写 / 中文说明）排成两栏对齐条目；
  4. 译名对照表：“一、人名”这类分节行排成小标题；
  5. 其余沿用通用规则：脚注（带圈号、每页从①起、按注文所在页编号）、首见人名楷体、
     中文语境引号、西文书刊名斜体、行内页标 [N]、书目与索引的嵌套列表等。

用法：python build_typ.py 排版配置.json
"""
from pathlib import Path
import json, re, sys

CFG_PATH = Path(sys.argv[1]).resolve()
CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
BASE = CFG_PATH.parent
MASTER = (BASE / CFG["主稿"]).resolve()
NAMES = (BASE / CFG["人名书名表"]).resolve() if CFG.get("人名书名表") else None
OUT = BASE / CFG.get("输出typ", "正文.typ")
TOOL = Path(__file__).resolve().parent


def cfg(k, default=None):
    return CFG.get(k, default)


CJK = r"　-〿㐀-鿿＀-￯"
PAGETAG_ONLY = re.compile(r"(\[(\d+|[ivxlcdm]+|[IVXLCDM]+)\]\s*)+")
ESC = set("\\#$*_`<>@[]~=+-/'\"(){}|&%^!?.,:;")


def esc(s):
    s = s.replace(r"\[", "[").replace(r"\]", "]").replace(r"\*", "*")

    def literal(t):
        return "".join("\\" + c if c in ESC else c for c in t)

    pieces, pos = [], 0
    for m in re.finditer(r"[!-~]{40,}", s):
        token = m[0]
        if not any(c in token for c in "/&="):
            continue
        pieces.append(literal(s[pos:m.start()]))
        pieces.append("#sym.zws;".join(literal(p) for p in re.split(r"(?<=[/?&=_:.\-])", token)))
        pos = m.end()
    pieces.append(literal(s[pos:]))
    return "".join(pieces)


ZQ = dict(zip("“”‘’", ""))
ZQ_BACK = {v: k for k, v in ZQ.items()}
UNMARK = str.maketrans(ZQ_BACK)
CN_NEAR = re.compile(f'[{CJK}—…{"".join(ZQ.values())}]')
WEST_NEAR = re.compile(r"[A-Za-zÀ-ɏ0-9,.;:!?]")
LETTER = r"[A-Za-zÀ-ɏ]"


def mark_quotes(s):
    pairs, stack = [], []
    for i, c in enumerate(s):
        if c in "„‚":
            stack.append((c, i))
        elif c == "’" and re.fullmatch(LETTER * 2, s[i - 1:i] + s[i + 1:i + 2]):
            continue
        elif stack and stack[-1][0] + c in ("„“", "„”", "‚‘", "‚’") and not (c in "“‘" and CN_NEAR.match(s[i - 1:i])):
            stack.pop()
        elif c in "“‘":
            stack.append((c, i))
        elif c in "”’":
            want = "“" if c == "”" else "‘"
            if any(o == want for o, _ in stack):
                while stack[-1][0] != want:
                    o, j = stack.pop()
                    if o in "“‘":
                        pairs.append((j, None))
                pairs.append((stack.pop()[1], i))
            else:
                pairs.append((None, i))
    pairs += [(j, None) for o, j in stack if o in "“‘"]
    out = list(s)

    def near(j, step):
        j += step
        while 0 <= j < len(s):
            m = re.match(r"\[\^\d+\]", s[j:]) if step > 0 else None
            if m:
                j += m.end()
            elif s[j] in " *":
                j += step
            else:
                return out[j]
        return ""

    for a, b in sorted(pairs, key=lambda p: p[0] if p[0] is not None else p[1]):
        before = near(a, -1) if a is not None else ""
        after = near(b, 1) if b is not None else ""
        inner = s[a + 1:b] if a is not None and b is not None else s[a + 1:a + 6] if b is None else s[max(0, b - 5):b]
        if (re.search(f"[{CJK}]", inner) or CN_NEAR.match(before)
                or CN_NEAR.match(after) and not WEST_NEAR.match(before)):
            for k in (a, b):
                if k is not None:
                    out[k] = ZQ[s[k]]
    return "".join(out)


def quotes(s):
    res, buf = [], ""
    for i, c in enumerate(s):
        if c in ZQ_BACK or c == "·" and re.search(f"[{CJK}]", s[i - 1:i] + s[i + 1:i + 2]):
            res.append(esc(buf))
            buf = ""
            res.append('#zq("%s");' % ZQ_BACK.get(c, c))
        else:
            buf += c
    res.append(esc(buf))
    return "".join(res)


# ---------- 读入主稿 ----------
text = MASTER.read_text(encoding="utf-8")
text = re.sub(r"\[(\d+|[ivxlcdm]+|[IVXLCDM]+)\]\s*<!--\s*原书此页(略|空白|仅有标题).*?-->", "", text, flags=re.S)
text = re.sub(r"(<!--\s*PDF页序:\s*\d+;\s*原书页码:\s*无;[^>]*-->\s*)\[(?!X\])([IVXLCDM]+)\]", r"\1", text)
text = re.sub(r"<!--.*?-->", "", text, flags=re.S)

lines_all = text.split("\n")
first_h2 = next(i for i, l in enumerate(lines_all) if l.startswith("## "))
front_lines = lines_all[:first_h2]
body_text = "\n".join(lines_all[first_h2:])

# 注释：`[^N]:` 定义，续行缩进四格
notes = {}
body_lines = []
last_note = None
for line in body_text.split("\n"):
    m = re.match(r"^\[\^(\d+)\]:\s?(.*)$", line)
    if m:
        notes[m[1]] = m[2]
        last_note = m[1]
    elif last_note and line.startswith("    ") and line.strip():
        frag = line.strip()
        prev = notes[last_note]
        if prev.endswith("-") and frag[:1].islower():
            notes[last_note] = prev[:-1] + frag      # 行末断词连字符：“Devasta-”+“tion” -> Devastation
        else:
            notes[last_note] = prev + " " + frag
    elif last_note and not line.strip():
        continue
    else:
        if last_note:
            body_lines.append("")
        last_note = None
        body_lines.append(line)
assert sorted(map(int, notes)) == list(range(1, len(notes) + 1)), "注释定义不连续"

# 首见人名（楷体）：人名书名表第二列
first_names = []
for line in (NAMES.read_text(encoding="utf-8").splitlines() if NAMES else []):
    if line.startswith(cfg("人名表行前缀", "| P")) and not re.match(r"^\|\s*-", line):
        c = [x.strip() for x in line.strip("|").split("|")]
        name_col = cfg("人名表中文列", 1)
        if len(c) > name_col and c[name_col] and re.match(f"[{CJK}]", c[name_col]):
            nm = re.sub(r"（[^（）]*）$", "", c[name_col])
            if nm:
                first_names.append(nm)
first_names.sort(key=len, reverse=True)
kai_done = set()
kai_half = []
kai_on = [False]
used_notes = set()


def inline(s, in_note=False, marked=False):
    if not marked:
        s = mark_quotes(s)
    out = []
    pos = 0
    pat = re.compile(r"\[\^(\d+)\]|\*\*(.+?)\*\*|(?<![\*A-Za-z0-9])\*(?!\s)(.+?)(?<!\s)\*(?![\*A-Za-z0-9])|<br>")
    for m in pat.finditer(s):
        out.append(plain(s[pos:m.start()], in_note))
        if m[1]:
            assert not in_note, "注中有注"
            used_notes.add(m[1])
            out.append("#sym.wj;#fn(" + m[1] + ")[" + note_body(notes[m[1]]) + "];")
        elif m[2] is not None:
            out.append("#strong[" + inline(m[2], in_note, True) + "];")
        elif m[3] is not None:
            out.append("#emph[" + inline(m[3], in_note, True) + "];")
        else:
            out.append("#linebreak();")
        pos = m.end()
    out.append(plain(s[pos:], in_note))
    return "".join(out)


def note_body(s):
    segs = []
    for seg in mark_quotes(s).split("\u2003"):
        if seg.startswith(">"):
            segs.append("#text(font: FANG)[" + inline(seg.lstrip("> ").strip(), True, True) + "]")
        else:
            segs.append(inline(seg, True, True))
    return "#linebreak();#h(2em);".join(segs)


SUBS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
SUPS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def plain(s, in_note):
    if re.search("[₀-₉]", s or ""):
        parts = re.split("([₀-₉]+)", s)
        return "".join(("#sub[" + p.translate(SUBS) + "];") if i % 2 else plain(p, in_note) for i, p in enumerate(parts))
    if re.search("[⁰¹²³⁴-⁹]", s or ""):
        parts = re.split("([⁰¹²³⁴-⁹]+)", s)
        return "".join(("#super[" + p.translate(SUPS) + "];") if i % 2 else plain(p, in_note) for i, p in enumerate(parts))
    if not s:
        return ""
    if in_note or not kai_on[0] or not first_names:
        return quotes(s)
    res, pos = [], 0
    for m in re.finditer("(?:" + "|".join(re.escape(n) for n in first_names) + r")(?=（)", s):
        name = m[0]
        if name in kai_done:
            continue
        if m.start() and s[m.start() - 1] == "·":
            kai_half.append(s[max(0, m.start() - 8):m.end()].translate(UNMARK))
            continue
        kai_done.add(name)
        res.append(quotes(s[pos:m.start()]))
        res.append("#kai[" + quotes(name) + "];")
        pos = m.end()
    res.append(quotes(s[pos:]))
    return "".join(res)


# ---------- 前置页 ----------
front_bucket = {}
cur = None
for raw in front_lines:
    m = re.match(r"^\[(I|II|III|IV|V|VI|VII|VIII|IX|X)\]\s*(.*)$", raw.strip())
    if m:
        cur = m[1]
        front_bucket.setdefault(cur, [])
        rest = m[2].strip()
        if rest:
            front_bucket[cur].append(rest)
        continue
    if cur:
        front_bucket.setdefault(cur, []).append(raw.rstrip())


def front_blocks(page):
    blocks, buf = [], []
    for l in front_bucket.get(page, []):
        if not l.strip():
            if buf:
                blocks.append(buf)
                buf = []
        else:
            buf.append(l.strip())
    if buf:
        blocks.append(buf)
    return blocks


def front_content(page, split_long: bool = False):
    """逐行排：上一行或本行为长行（≥40 字，视为整段）时另起一段，否则换行。
    split_long=True 时把长行单独分出（用于丛书页：名单居中、说明文字通栏）。"""
    short, longparts = [], []
    for b in front_blocks(page):
        prev_long = None
        for l in b:
            t = inline(l)
            is_long = len(l) >= 40
            if split_long and len(l) >= 100:
                longparts.append(t)
                prev_long = None
                continue
            if prev_long is None:
                short.append(t)
            elif prev_long or is_long:
                short.append("#parbreak();" + t)
            else:
                short.append("#linebreak();" + t)
            prev_long = is_long
    if split_long:
        return "".join(short), "#parbreak();".join(longparts)
    return "".join(short)


front_out = []
if "I" in front_bucket:
    front_out.append("#fp-blurb[" + front_content("I") + "]")
if "III" in front_bucket:
    s3, l3 = front_content("III", split_long=True)
    front_out.append("#fp-series[" + s3 + "]")
    if l3:
        front_out.append("#fp-series-note[" + l3 + "]")
if "IV" in front_bucket:
    front_out.append("#fp-list[" + front_content("IV") + "]")
if "V" in front_bucket:
    v = [x for b in front_blocks("V") for x in b]
    while len(v) < 5:
        v.append("")
    front_out.append("#fp-title([" + inline(v[0]) + "],[" + inline(v[1]) + "],[" +
                     inline(v[2]) + "],[" + inline(v[3]) + "],[" + inline(v[4]) + "])")
if "VI" in front_bucket:
    front_out.append("#fp-copy[" + front_content("VI") + "]")

# ---------- 分块 ----------
blocks = []
cur = []
for line in body_lines + [""]:
    if line.strip() == "" or re.match(r"^#+ ", line):
        if cur:
            blocks.append(cur)
            cur = []
        if line.strip():
            blocks.append([line])
    else:
        cur.append(line)

out = list(front_out)
mode = "front"
center = False
toc_done = False
roman_set = False
arabic_set = False
index_buf = []
part = ""
skip_section_level = None
skip_section_titles = set(cfg("读者版略去整个标题区块", []))
abbr_pending = None

PART_RE = re.compile(r"^第[一二三四五六七八九十百]+编")
GLSUB_RE = re.compile(r"^[一二三四五六七八九十]+、")
PAGETAG = r"\[(?:\d+|[ivxlcdm]+|[IVXLCDM]+)\]"

for b in blocks:
    first = b[0]
    current_heading = re.match(r"^(#+) (.*)$", first)
    if skip_section_level is not None:
        if current_heading and len(current_heading[1]) <= skip_section_level:
            skip_section_level = None
        else:
            continue
    if current_heading and current_heading[2].strip() in skip_section_titles:
        skip_section_level = len(current_heading[1])
        continue
    if first.startswith("<div"):
        center = "right" if "right" in first else "center"
        continue
    if first.startswith("</div>"):
        center = False
        continue
    m = re.match(r"^(#+) (.*)$", first)
    if m:
        lv, title = len(m[1]), m[2].strip()
        if title in cfg("读者版略去标题", []):
            continue
        if lv == 1:
            continue          # 书名页由前置页（原书第 V 页）承担
        # 罗马页码：从“罗马页码起始标题”起
        if lv == 2 and not roman_set and mode == "front" and title != cfg("正文起始标题"):
            roman_start = cfg("罗马页码起始标题")
            if not roman_start or title == roman_start:
                out.append('#pagebreak(weak: true)\n#set page(numbering: "i")\n#counter(page).update(1)')
                roman_set = True
        if lv == 2 and title == cfg("目录插在此标题前") and not toc_done:
            out.append("#toc()")
            toc_done = True
        if lv == 2 and title == cfg("首见楷体起始标题"):
            kai_on[0] = True
        if lv == 2 and title == cfg("正文起始标题"):
            mode = "body"
        if lv <= cfg("书目部分层级", 2) and cfg("书目部分标题") and title.startswith(cfg("书目部分标题")):
            mode = "bib"
        if title == cfg("人物小传标题", "人物小传"):
            mode = "bio"
            kai_on[0] = False
        if title == cfg("索引标题", "索引"):
            mode = "index"
        if lv == 2 and title in cfg("标题排式", {}):
            mode = cfg("标题排式", {})[title]
        if lv == 2 and title == cfg("译名对照表标题", "译名对照表"):
            mode = "glossary"
        if lv == 2 and title == cfg("缩略语表标题", "缩略语表"):
            mode = "abbr"
            abbr_pending = None
        if index_buf:
            out.append("#indexblock[" + "#parbreak();".join(index_buf) + "]")
            index_buf = []
        outl = (lv <= cfg("目录收录层级", 3)
                or bool(cfg("目录另收标题正则") and re.match(cfg("目录另收标题正则"), title))) \
            and title not in cfg("目录排除标题", [])
        if lv == 2 and PART_RE.match(title):
            if not arabic_set:
                out.append('#pagebreak(weak: true)\n#set page(numbering: "1")\n#counter(page).update(1)')
                out.append("#parthd(newpage: false)[" + inline(title) + "]")
                arabic_set = True
            else:
                out.append("#parthd[" + inline(title) + "]")
            continue
        if lv == 2:
            part = title
        brk = lv <= 3 and out and not out[-1].startswith("#hd(")
        run = ""
        if lv == 2 or lv == 3:
            short = cfg("页眉章名", {}).get(title) or re.sub(r"（[^（）]*[A-Za-z][^（）]*）", "", title).replace("*", "")
            if len(short) > 18:
                print(f"警告：页眉章名超过18字，请在排版配置“页眉章名”中给短题：{short}")
            if short != title:
                run = f", running: [{inline(short)}]"
        out.append(f'#hd({lv}, "{mode}", outlined: {str(outl).lower()}, newpage: {str(brk).lower()}{run})[{inline(title)}]')
        continue
    # 独立图片
    image_text = " ".join(re.sub(r"^>\s?", "", line) for line in b)
    image_match = re.fullmatch(r"(\[(?:\d+|[ivxlcdm]+|[IVXLCDM]+)\])?\s*!\[([^\]]*)\]\(([^)]+)\)", image_text)
    if image_match:
        continue
    if first.startswith("<div"):
        continue
    # 引文
    if all(l.startswith(">") for l in b):
        q = " ".join(re.sub(r" {2,}$", "<br>", re.sub(r"^>\s?", "", l)) for l in b)
        verse = "<br>" in q
        out.append(f"#bq(verse: {str(verse).lower()})[{inline(q)}]")
        continue
    # HTML 表
    if re.match(r"^(\[\d+\])?<table>", first):
        tag = re.match(r"^(\[\d+\])?", first)[0]
        rows = [re.findall(r'<td(?: colspan="(\d+)")?>(.*?)</td>', l) for l in b if l.startswith("<tr>")]
        ncol = max(sum(int(n or 1) for n, _ in r) for r in rows)
        cells = [(f"table.cell(colspan: {n})" if n else "") + ("[" + (inline(tag) if not i and not j else "") + "#strong[" + inline(c) + "]]" if i == 0 else "[" + inline(c) + "]")
                 for i, r in enumerate(rows) for j, (n, c) in enumerate(r)]
        out.append(f'#tbl({ncol}, mode: "{mode}", keep: true, ' + ", ".join(cells) + ")")
        continue
    # Markdown 表
    if all(l.startswith("|") for l in b):
        rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in b]
        rows = [r for r in rows if not all(re.fullmatch(r":?-+:?", c) for c in r)]
        ncol = max(len(r) for r in rows)
        cells = []
        for i, r in enumerate(rows):
            r = r + [""] * (ncol - len(r))
            for c in r:
                cells.append(("[#strong[" + inline(c) + "]]") if i == 0 else ("[" + inline(c) + "]"))
        out.append(f'#tbl({ncol}, mode: "{mode}", ' + ", ".join(cells) + ")")
        continue
    # 书目/索引：词头不写成列表项、子条目缩进成列表
    if mode in ("bib", "index") and len(b) > 1 and not b[0].startswith("- ") and all(re.match(r"^ +- ", l) for l in b[1:]):
        b = ["- " + b[0]] + b[1:]
    # 嵌套列表
    if b and all(re.match(r"^( *)- ", l) for l in b) and (mode in ("bib", "index") or any(l.startswith(" ") for l in b)):
        for l in b:
            lvl = (len(l) - len(l.lstrip(" "))) // 2
            item = '#li("' + mode + '", ' + str(lvl) + ')[' + inline(l.lstrip(" ")[2:]) + "]"
            (index_buf if mode == "index" else out).append(item)
        continue
    # 编号列表
    if len(b) > 1 and all(re.match(r"^(\[(\d+|[ivxlcdm]+)\])?\d+\. ", l) for l in b):
        for l in b:
            out.append('#li("' + mode + '", 0)[' + inline(l) + "]")
        continue
    # 项目符号列表
    if all(l.startswith("- ") for l in b):
        for l in b:
            out.append('#p("bio")[· ' + inline(l[2:]) + "]")
        continue
    para = " ".join(b)
    if center:
        out.append(("#signature[" if center == "right" else "#centerblock[") + inline(para) + "]")
        continue
    if para.startswith("——") and len(para) < 120 and mode not in ("bib", "index", "glossary"):
        out.append("#signature[" + inline(para) + "]")
        continue
    if PAGETAG_ONLY.fullmatch(para.strip()):
        continue
    if mode == "index":
        # 索引：原书双栏展平后的纯页码续行接回上一条
        for line in (b if len(b) > 1 else [para]):
            t = line.strip()
            if not t:
                continue
            if (re.fullmatch(r"[\d,\- ]+", t) or t.startswith(",")) and index_buf:
                index_buf[-1] = index_buf[-1].rstrip() + " " + inline(t)
            else:
                index_buf.append(inline(t))
        continue
    if mode == "glossary":
        # 对照表：每条一行（“中文译名　原文”），逐行排出；分节标题另排小标题
        for line in (b if len(b) > 1 else [para]):
            t = line.strip()
            if not t:
                continue
            if GLSUB_RE.match(t):
                out.append("#glsub[" + inline(t) + "]")
            else:
                out.append('#p("glossary")[' + inline(t) + "]")
        continue
    if mode == "abbr":
        t0 = para.strip()
        tagm = re.match(r"^((?:" + PAGETAG + r")*)(.*)$", t0)
        tag, t = tagm.group(1), tagm.group(2).strip()
        if re.fullmatch(r"[A-Za-z0-9/\.\- ]{1,20}", t) and re.search(r"[A-Za-z]", t):
            abbr_pending = (tag, t)
            continue
        if abbr_pending:
            out.append("#abbrev[" + inline(abbr_pending[0]) + inline(abbr_pending[1]) + "][" + inline(para) + "]")
            abbr_pending = None
        else:
            out.append('#p("body")[' + inline(para) + "]")
        continue
    out.append(f'#p("{mode}")[{inline(para)}]')

if index_buf:
    out.append("#indexblock[" + "#parbreak();".join(index_buf) + "]")
assert used_notes == set(notes), ("有注未用", sorted(set(notes) - used_notes)[:10])

tpl = (TOOL / "版式.typ").relative_to(BASE).as_posix()
header = (f'#import "{tpl}": *\n')
if cfg("封面文件"):
    header += (f'#import "{cfg("封面文件")}": cover\n#cover()\n#pagebreak()\n')
header += (f'#show: book.with(书名: "{cfg("页眉书名", cfg("书名"))}", 文档标题: "{cfg("书名")}", '
           f'作者: "{cfg("作者", "")}", 注号字体: "{cfg("注号字体", "MS Mincho")}")\n\n')

OUT.write_text(header + "\n\n".join(out) + "\n", encoding="utf-8")
print("blocks", len(out), "notes", len(used_notes), "kai", len(kai_done))
if kai_half:
    print(f"首见人名写了名、人名表只登记姓，未排楷体（{len(kai_half)}）：", "；".join(kai_half[:12]))
