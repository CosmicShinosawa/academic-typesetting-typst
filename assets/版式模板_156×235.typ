// ============================================================================
// 学术专著阅读版版式模板 · 156 × 235 mm（Typst 0.15）
// 依据：《学术著作翻译规范》第四、五节；版式参照《当代埃塞俄比亚政治进程研究》。
// 用法：与 版式参数_156×235.json 同目录，由 build_typ.py（或自写转换器）生成 正文.typ 后 import。
//
// 本模板在通用 版式.typ 上的增改（均已实测）：
//   1. 开本 156 × 235 mm，页码在页眉外侧；页眉取“章”短题（三级标题），编、章首页不排页眉；
//   2. 编（第一编/第二编/…）作一级标题，另页居中、单独下沉、不排页码；
//   3. 前置页专用排式：内容简介 / 丛书页 / 丛书书目 / 书名页 / 版权页（函数名 fp-*、fp-title）；
//   4. 粗宋用华文中宋 STZhongsong（Windows 无 Songti SC Bold）；带圈注号用 MS Mincho（含①—㊿）；
//   5. 目录条目自绘：页码按目标页实际编号排（前置罗马、正文阿拉伯），点线连接。
//
// 每本书要改的地方：
//   · 版式参数_156×235.json（开本、字号行距、下沉行数）——一般不用改；
//   · 书() 的默认参数（书名/注号字体）；页眉书名在 build_typ 的配置里给；
//   · fp-series / fp-list / fp-title / fp-copy 的细节（依底本前置页结构）；
//   · 若原书无“编”，把 parthd 定义删除，并让 ## 标题走 hd(2, …)。
//
// 两个 Typst 陷阱（再遇时直接看这里）：
//   · query(heading.where(level: lv => lv <= 3)) 在 0.15 里恒为空，必须写 query(heading).filter(h => h.level <= 3)；
//   · 页眉里若把局部变量起名 h，则 h(1.2em) 会当成“调用 content”报错，改用 rh 等名字。
// ============================================================================
#let P = json("版式参数_156×235.json").at(sys.inputs.at("版式", default: "156×235"))

#let SONG = ("Times New Roman", "SimSun")
#let SONGB = ("Times New Roman", "STZhongsong")   // 粗宋
#let HEI = ("Times New Roman", "SimHei")
#let FANG = ("Times New Roman", "FangSong")
#let KAI = ("Times New Roman", "KaiTi")
#let BODY = P.at("正文字号pt") * 1pt
#let NOTE = P.at("脚注字号pt") * 1pt
#let LINE = P.at("正文行距pt") * 1pt            // 一行：相邻两行基线的距离
#let NOTE-LINE = P.at("脚注行距pt") * 1pt
#let gap(sz) = if sz == NOTE { NOTE-LINE - NOTE } else { LINE - BODY }   // 行与行之间的空白（字框取 1em）
#let 空(n) = n * LINE + gap(BODY)   // “空 n 行”：正常行间空白之外再加 n 行

#let zq(c) = text(font: "SimSun", c)            // 中文语境引号：宋体全角字形
#let kai(b) = text(font: KAI, b)                // 首见人名：楷体

// 带圈注号：宋体只有①—⑩，注号统一用 MS Mincho（明朝体，含①—㊿），字宽一致
#let circ-char(n) = str.from-unicode(if n <= 20 { 0x2460 + n - 1 } else if n <= 35 { 0x3251 + n - 21 } else { 0x32B1 + n - 36 })
#let circ-font = state("circ-font", "MS Mincho")
#let circled(n) = context text(font: circ-font.get(), circ-char(n))

// 注号编法：按注文实际排在哪一页、在该页第几条来编（每页从①起）。
// 注文被排版程序整条挪到下页时，正文注号随之取下页的号，保证注号与注文一一对应、一页内不重号。
#let fn-index-map() = {
  let by = (:)
  for m in query(<fnid>) {
    let k = str(m.location().page())
    by.insert(k, by.at(k, default: ()) + (m.value,))
  }
  let d = (:)
  for (k, ids) in by {
    for (i, id) in ids.sorted().enumerate() { d.insert(str(id), i + 1) }
  }
  d
}
#let entry-index(id) = fn-index-map().at(str(id), default: 1)
#let fn(id, body) = {
  box(context super(typographic: false, baseline: -0.45em, size: 0.62em, circled(entry-index(id))))
  footnote(numbering: (..n) => none, [#metadata(id)<fnid>#context circled(entry-index(id))#h(0.5em)#body])
}

// 页眉：偶数页页码、书名居左；奇数页章名、页码居右（页码在最外侧）。
// 章名取“编/章/一级部分”各级标题中当前页之前最近的一个的短题（supplement）。
#let run-title(p) = {
  let hs = query(heading).filter(h => h.level <= 3)
  let prev = hs.filter(h => h.location().page() < p)
  if prev.len() == 0 { none } else {
    prev.fold(none, (a, b) => {
      if a == none { b } else if b.location().page() >= a.location().page() { b } else { a }
    })
  }
}

#let book(书名: "", 文档标题: "", 作者: "", 注号字体: "MS Mincho", doc) = {
  circ-font.update(注号字体)
  set document(title: 文档标题, author: 作者)
  set page(
    width: P.at("页宽mm") * 1mm,
    height: P.at("页高mm") * 1mm,
    margin: (top: P.at("上边距mm") * 1mm, bottom: P.at("下边距mm") * 1mm,
      left: P.at("左边距mm") * 1mm, right: P.at("右边距mm") * 1mm),
    numbering: none,
    header: context {
      let p = here().page()
      let n = here().page-numbering()
      if n == none { return }
      let hs = query(heading).filter(h => h.level <= 3)
      if hs.any(h => h.location().page() == p) { return }   // 编首页、章首页不排页眉
      let rh = run-title(p)
      if rh == none { return }
      let num = text(font: "Times New Roman", weight: "bold", size: 10pt, counter(page).display(n))
      let even = calc.even(counter(page).get().first())
      set text(size: NOTE, font: SONG)
      if P.at("页码位置") == "页眉外侧" {   // 偶数页：页码、书名居左；奇数页：章名、页码居右
        if even { align(left, num + h(1.2em) + text(font: SONG, 书名)) }
        else { align(right, text(font: SONG, rh.supplement) + h(1.2em) + num) }
      } else {
        align(center, if even { text(书名) } else { text(rh.supplement) })
      }
    },
    footer: context {
      let n = here().page-numbering()
      if n == none { return }
      let p = here().page()
      // 页码在页眉外侧时，只有章首页（不排页眉）把页码放在页脚；编扉页不排页码
      let hs = query(heading).filter(h => h.level <= 3)
      if not hs.any(h => h.location().page() == p) { return }
      let ispart = query(heading).any(h => h.level == 1 and h.location().page() == p)
      if ispart { return }
      align(center, text(size: NOTE, font: SONG, counter(page).display(n)))
    },
  )
  set text(font: SONG, size: BODY, lang: "zh", region: "cn", top-edge: 1em, bottom-edge: 0pt,
    cjk-latin-spacing: auto)
  set smartquote(enabled: false)
  set par(justify: true, leading: gap(BODY), spacing: gap(BODY),
    first-line-indent: (amount: 2em, all: true))
  show regex("[\[\]]"): set text(font: "SimSun")          // 方括号：宋体半角
  show emph: it => text(font: KAI, style: "italic", it.body)
  show strong: it => text(font: SONGB, weight: "bold", it.body)

  // 脚注：正文注号上标；注区注号与注文同为小五、在基线，首行缩两字，续行顶格
  set footnote.entry(separator: line(length: 25%, stroke: 0.4pt), indent: 0em, gap: gap(NOTE),
    clearance: 0.8em)
  show footnote.entry: it => {
    set text(size: NOTE)
    set par(leading: gap(NOTE), spacing: gap(NOTE), first-line-indent: (amount: 2em, all: true),
      hanging-indent: 0em)
    par(it.note.body)
  }

  // 标题：编用一级标题（另页、大字、大下沉）；一级部分与章同为“章标题”排式
  show heading: set par(first-line-indent: 0em, justify: false)
  show heading: it => {
    if it.level == 1 {
      v(P.at("编首下沉行") * LINE)
      block(width: 100%, align(center, text(font: SONGB, weight: "bold",
        size: P.at("编标题字号pt") * 1pt, top-edge: 1em, it.body)))
      v(1fr)
    } else {
      let (节前, 节后) = (P.at("节标题前空行"), P.at("节标题后空行"))
      let (size, al, above, below) = if it.level == 2 { (P.at("章标题字号pt") * 1pt, center, 0, P.at("章标题后空行")) }
        else if it.level == 3 { (P.at("章标题字号pt") * 1pt, center, 0, P.at("章标题后空行")) }
        else if it.level == 4 { (P.at("节标题字号pt") * 1pt, center, 节前, 节后) }
        else if it.level == 5 { (11pt, center, 节前, 节后) }
        else { (BODY, left, P.at("小标题前空行"), P.at("小标题后空行")) }
      if (it.level == 2 or it.level == 3) and P.at("章首下沉行") > 0 { v(P.at("章首下沉行") * LINE) }
      v(空(above), weak: true)
      block(above: 0pt, below: 0pt, sticky: true, width: 100%,
        align(al, text(font: SONGB, weight: "bold", size: size, top-edge: 1em, it.body)))
      v(空(below), weak: true)
    }
  }

  // 目录：点线连接、页码右对齐；编、章加粗，节常规。页码按目标页实际编号排（前置罗马、正文阿拉伯）
  set outline(indent: n => if n <= 2 { 0em } else { (n - 2) * 2em })
  show outline.entry: it => context {
    let lv = it.level
    let el = it.element
    let loc = el.location()
    let n = counter(page).at(loc).first()
    let body-start = query(heading).filter(h => h.level == 1).first().location()
    let label = if loc.page() < body-start.page() { numbering("i", n) } else { numbering("1", n) }
    set par(first-line-indent: 0em, hanging-indent: 2em)
    link(loc, block(above: if lv <= 3 { 0.5 * LINE } else { gap(BODY) }, below: 0pt, pad(left: if lv >= 4 { 2em } else { 0em },
      grid(columns: (auto, 1fr, auto), column-gutter: 0.3em, align: horizon,
        text(size: BODY, font: if lv <= 3 { SONGB } else { SONG },
          weight: if lv <= 3 { "bold" } else { "regular" }, el.body),
        it.fill,
        text(size: BODY, font: SONG, weight: "regular", label)))))
  }
  doc
}

// 标题：## 一级部分、### 章（均另页起排）、#### 节、##### 小标题
#let hd(lv, mode, outlined: true, newpage: false, running: none, body) = {
  if newpage { pagebreak(weak: true) }
  heading(level: lv, outlined: outlined, bookmarked: true,
    supplement: if running == none { body } else { running }, body)
}

// 编扉页：另起一页（或由调用方已换页），居中大字，单独下沉；作一级标题登记（进目录与书签）
#let parthd(body, newpage: true) = {
  if newpage { pagebreak(weak: true) }
  heading(level: 1, outlined: true, bookmarked: true, supplement: body, body)
}

#let titlepage(body) = {
  v(28%)
  align(center, text(font: HEI, size: 16pt, top-edge: 1em, body))
  v(2 * LINE)
}
#let titleline(body) = block(above: 0.6 * LINE, below: 0pt, width: 100%, {
  set par(first-line-indent: 0em, justify: false)
  align(center, body)
})
#let copyrightpage(body) = {
  pagebreak()
  v(1fr)
  set text(size: NOTE, font: SONG)
  set par(first-line-indent: 0em, justify: false, leading: gap(NOTE), spacing: 0.5em)
  body
}
#let toc() = {
  pagebreak(weak: true)
  heading(level: 2, outlined: false, bookmarked: true, supplement: [目录])[目录]
  outline(title: none, depth: 4)
}

// ---------- 前置页排式（本项目专有） ----------
// 内容简介（原书第 I 页）：左对齐正文，首行缩两字
#let fp-blurb(body) = {
  pagebreak(weak: true)
  v(P.at("页高mm") * 1mm * 0.11)
  set text(size: 10pt)
  set par(first-line-indent: (amount: 2em, all: true), leading: 16pt - 10pt)
  body
}
// 丛书页（原书第 III 页）：名单居中排；丛书说明另起通栏正排
#let fp-series(body) = {
  pagebreak(weak: true)
  v(P.at("页高mm") * 1mm * 0.14)
  set par(first-line-indent: 0em, justify: false, leading: 5pt, spacing: 0.35em)
  set text(size: 10pt)
  align(center, body)
}
#let fp-series-note(body) = {
  set par(first-line-indent: (amount: 2em, all: true), justify: true, leading: 16pt - 10pt, spacing: 0.5em)
  set text(size: 10pt)
  block(above: 0.9 * LINE, width: 100%, body)
}
// 丛书书目（原书第 IV 页）：小字，行距紧凑
#let fp-list(body) = {
  pagebreak(weak: true)
  v(P.at("页高mm") * 1mm * 0.06)
  set par(first-line-indent: 0em, justify: false, leading: 3.2pt, spacing: 0.32em)
  set text(size: NOTE)
  body
}
// 书名页（原书第 V 页）
#let fp-title(title, sub, author, affil, pub) = {
  pagebreak(weak: true)
  v(P.at("页高mm") * 1mm * 0.24)
  align(center, text(font: SONGB, weight: "bold", size: 19pt, top-edge: 1em, title))
  v(1.5em)
  align(center, text(size: 10.5pt, sub))
  v(4em)
  align(center, text(size: 13pt, author))
  v(0.7em)
  align(center, text(size: 10.5pt, affil))
  v(1fr)
  align(center, text(size: 12pt, pub))
  v(P.at("页高mm") * 1mm * 0.14)
}
// 版权页（原书第 VI 页，照录原文）
#let fp-copy(body) = {
  pagebreak(weak: true)
  set text(size: 8.5pt, font: SONG)
  set par(first-line-indent: 0em, justify: false, leading: 2.6pt, spacing: 0.18em)
  v(P.at("页高mm") * 1mm * 0.03)
  body
}

// 段落
#let p(mode, body) = {
  if mode == "bib" {
    set text(size: NOTE)
    set par(first-line-indent: 0em, hanging-indent: 2em, leading: gap(NOTE), spacing: 0.35em, justify: false)
    par(body)
  } else if mode == "glossary" {
    // 对照表五号，行距同正文；每条转行悬挂两字。
    set text(size: BODY)
    set par(first-line-indent: 0em, hanging-indent: 2em, leading: gap(BODY), spacing: gap(BODY))
    par(body)
  } else if mode == "bio" {
    set par(first-line-indent: 0em, hanging-indent: 2em)
    par(body)
  } else {
    par(body)
  }
}
// 缩略语表条目：缩写列 + 中文说明列（两栏对齐）
#let abbrev(a, d) = {
  set par(first-line-indent: 0em, justify: false)
  set text(size: BODY)
  block(above: 0pt, below: 2pt, width: 100%, grid(columns: (5em, 1fr), column-gutter: 0.6em,
    text(font: ("Times New Roman", "SimSun"))[#a], d))
}
// 对照表分节标题（一、人名）
#let glsub(body) = block(above: 1.2 * LINE, below: 0.6 * LINE, width: 100%, {
  set par(first-line-indent: 0em, justify: false)
  align(left, text(font: SONGB, weight: "bold", size: BODY, body))
})
// 嵌套列表条目（书目、索引）：按层级整体缩进，转行再缩两字
#let li(mode, level, body) = {
  set text(size: if mode == "bib" or mode == "index" { NOTE } else { BODY })
  set par(first-line-indent: (amount: level * 1em, all: true), hanging-indent: level * 1em + 2em, justify: false,
    leading: if mode == "bib" or mode == "index" { gap(NOTE) } else { gap(BODY) },
    spacing: if mode == "bib" { 0.35em } else if mode == "index" { gap(NOTE) } else { gap(BODY) })
  par(body)
}
#let indexblock(body) = {
  set text(size: NOTE)
  set par(first-line-indent: 0em, hanging-indent: 2em, leading: gap(NOTE), spacing: gap(NOTE), justify: false)
  columns(2, gutter: 2em, body)
}
// 独立引文：用段落整体缩进（块内行无法随注挪页），整体左缩两字、首行再缩两字；诗行不加首行缩进
#let bq(verse: false, body) = {
  v(空(P.at("引文前后空行")), weak: true)
  {
    set text(font: FANG)
    set par(hanging-indent: 2em, first-line-indent: (amount: if verse { 2em } else { 4em }, all: true))
    body
  }
  parbreak()
  v(空(P.at("引文前后空行")), weak: true)
}
#let signature(body) = block(above: 0.5 * LINE, below: LINE, width: 100%, {
  set par(first-line-indent: 0em, justify: false)
  align(right, body)
})
#let centerblock(body) = block(above: 0.5 * LINE, below: 0.5 * LINE, width: 100%, {
  set par(first-line-indent: 0em, justify: false)
  align(center, body)
})
#let tbl(n, mode: "body", keep: false, ..cells) = {
  set text(size: if mode == "bib" or mode == "front" { NOTE } else { BODY })
  set par(first-line-indent: 0em, justify: false, leading: gap(NOTE))
  block(above: 0.5 * LINE, below: 0.5 * LINE, breakable: not keep, table(
    columns: if keep { (20%,) + (1fr,) * (n - 1) } else if n == 3 and mode == "front" { (auto, 35%, 1fr) } else if n == 3 { (auto, 30%, 1fr) } else if n == 2 and mode == "bib" { (auto, 1fr) } else if n == 2 { (1fr, 1fr) } else { n },
    stroke: (x, y) => if y == 0 { (top: 0.6pt, bottom: 0.4pt) } else { none },
    inset: (x: 4pt, y: 3pt),
    align: left + top,
    ..cells.pos(),
    table.hline(stroke: 0.6pt),
  ))
}
