// 封面模板：把原书封面图满版排在一页上（封面页参数只作用于本页）。
// 用法：把 cover() 的图片路径改成你的封面图（建议裁掉扫描黑边），
//       并在 正文.typ 里 **放在 #show: book.with(...) 之前** 调用 #cover()，
//       否则 set page 会泄漏到全书，把页边距和页码都改掉。
// 注意：书内可用原书封面（封面设计页），不得用扉页或自制色块顶替。
#let cover() = {
  set page(width: 156mm, height: 235mm, margin: 0mm, numbering: none, header: none, footer: none)
  image("封面.jpg", width: 156mm, height: 235mm, fit: "cover")
}
