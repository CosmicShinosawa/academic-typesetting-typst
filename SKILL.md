---
name: academic-typesetting-typst
description: >-
  学术专著"阅读版"PDF 排版技能（Typst 0.15，156 × 235 mm）。用于把已定稿的中文译稿 Markdown
  排成可交付的阅读版 PDF：页下注带圈数字每页从①起、页眉外侧章短题、前置罗马页码与正文阿拉伯页码、
  自动目录与 PDF 书签、外侧原书边码、图注（黑体图题+宋体资料来源）、参考文献/索引/译名对照表、原书封面。
  触发词：排版、排成 PDF、阅读版、Typst、页下注、带圈注号、156×235、学术专著、书稿、typesetting、
  book layout, PDF, footnote, TOC。不用于：翻译本身、扫描件数字化、Word/PPT 撰写。
---

# 学术专著阅读版排版（Typst）

把**已定稿**的中文译稿 Markdown 排成交付级 PDF。规则本在 `reference/排版规范.md`（完整版，13 节），
本文件只给执行顺序与必须记住的硬规则。

## 何时用这个技能

- 用户说"排版""排成 PDF""做阅读版""出书""按某某书的样子排"；
- 手里有：译文主稿 `.md`（页标 `[N]`、脚注 `[^n]` 定义齐全）、可选的人名书名表、可选的原书扫描 PDF。

**不接的活**：翻译/润色（先回去改 MD）、扫描件数字化、Word/PPT。排版中发现文字问题一律先改 MD 再重排。

## 一、环境（Windows，实测）

- Typst 0.15 **只有 Python 包**，没有 CLI：

  ```python
  import sys
  sys.path.insert(0, r"<仓库>/已翻译/Cute Accelerationism/工作文件/python_deps")   # 内含 typst
  import typst
  ```

- 字体用系统字体（`C:/Windows/Fonts`）：SimSun / Times New Roman / **STZhongsong（粗宋）** / KaiTi / FangSong / **MS Mincho（带圈号）**。
- 依赖 `pymupdf` 做核验与渲染抽看。
- **不要**用 LibreOffice / Word 转 PDF。

## 二、五步执行

1. **备料**：把 `assets/版式模板_156×235.typ` 复制成项目 `工作文件/版式.typ`，`assets/版式参数_156×235.json`
   一同放入（json 文件名不能改，模板按名读取）。封面照 `assets/封面模板.typ` 写 `封面.typ`。
2. **写配置**：照 `examples/排版配置_示例.json` 写 `工作文件/排版配置.json`，至少改：
   主稿路径、人名书名表、`正文起始标题`（"第一编　…" 或 "第一章　…"）、
   `读者版略去整个标题区块`（通常 `["目录","注释"]`）、`目录插在此标题前`、`首见楷体起始标题`、`封面文件`。
3. **转换**：以 `scripts/build_typ_参考实现.py` 为起点（它是本书<sup>1</sup>的实测版本），改主稿解析后运行
   `python build_typ.py 排版配置.json` → 生成 `正文.typ`。
4. **编译**：`typst.compile("正文.typ", output=…, root=".", font_paths=["C:/Windows/Fonts"], sys_inputs={"版式":"156×235"})`。
5. **核验**：`python scripts/核验_阅读版.py 成品.pdf -o 核验报告.txt`，逐条处理；再按规范第 11 节目视抽看 16 类样页，
   结果写进项目 `工作文件/05_审校与排版记录.md`。

<sup>1</sup> 该参考实现里的"前置页/编扉页/缩略语表/索引续行合并/拼音排序"等分支是按一本书写的，换书时按需删改。

## 三、必须记住的硬规则

| 项 | 规则 |
|---|---|
| 开本 | 156 × 235 mm；上 23 / 下 18 / 左右 20 mm（版心 116 × 194） |
| 字号行距 | 正文 10.5 pt / **17.5 pt**（`SimSun` 微描边 `0.12 pt` + 字距 `0.04 em`，楷体/粗宋/标题/脚注不加描边）；脚注 9 pt / **13 pt**；章 15、节 14、编 17；章首下沉 3 行、标题后空 4 行 |
| 粗宋 | Windows 无 Songti SC Bold → **STZhongsong**，并在交付说明写明 |
| 带圈注号 | SimSun 只有 ①—⑩ → 必须 **MS Mincho**，否则 ⑪ 回退成"11" |
| 页码 | 封面/书名页/版权页无页码 → 译者说明起罗马 → 正文起阿拉伯；页眉外侧，章首页页码在页脚 |
| 脚注 | 书末注改页下注，**每页从①起、按注文实际所在页编号**（模板内置 query 机制），注号不断行 |
| 页标 | 主稿 `[N]` 锚点转排至**外侧页边空白处**作边码（`#op(n)`，8.5 pt 无衬线，无方括号），不占正文行内宽度、不进标题/目录/书签 |
| 图注 | 图片版心居中；图题 `图 N  标题` 黑体 9 pt；`资料来源：…` 另起一行宋体 9 pt、首行缩 2 字回行顶格（`#fig()`） |
| 章副标题/题辞 | 章副标题用 `#hd(..., sub: "…")` 分行排印且不进页眉；章首题辞用 `#epigraph(body, source: "…")`；节标题换页可用 `margin-page` 标外侧边码（不进目录/书签） |
| 目录 | 自动生成、收编/章/节三级；**页码按目标页实际编号**（前置罗马、正文阿拉伯），交付前与书签逐条核对 |
| 封面 | 必须用**原书封面**（出版社官网 / Google Books / Open Library，最后才用扫描本且须目视确认是封面），不得用扉页或自制色块 |
| 交付前 | 嵌入字体无回退、无"未收敛"警告、样页目视通过、主稿结构检查器仍 0 错误 |

## 四、文件索引

```
reference/排版规范.md              # 完整规范（先读 §3 §5 §7 §10 §11 §12）
assets/版式模板_156×235.typ        # 版式本体（已实测）；文件头列了每本书要改的地方
assets/版式参数_156×235.json       # 数值（与模板同目录、同名引用）
assets/封面模板.typ                # 满版封面函数（放在 #show 之前调用）
scripts/build_typ_参考实现.py      # MD → Typst 转换器参考实现
scripts/核验_阅读版.py             # 8 项机械核验
examples/排版配置_示例.json        # 配置字段示例
```

## 五、最容易翻车的六件事

1. `set page(...)` 写进函数体只作用于该块 —— 切页码体系必须写在**文档顶层**。
2. 封面 `set page(margin: 0)` 若在 `#show: book.with(...)` 之后调用，会把全书页边距和页码都改掉 → 封面函数放**最前面**。
3. `query(heading.where(level: lv => lv <= 3))` 在 0.15 里**恒为空**，要写 `query(heading).filter(h => h.level <= 3)`。
4. 页眉里局部变量叫 `h` 会让 `h(1.2em)` 报 `expected function, found content`。
5. `outline.entry` 没有 `body`/`page` 字段（只有 `level/element/fill`），目录页码要自绘。
6. 注文若按空格 split 会把整条注拆成"每词一行"；多段注要用专用分隔符（U+2003）。

以上细节与更多坑见 `reference/排版规范.md` 第 12 节。
