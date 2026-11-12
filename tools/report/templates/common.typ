// Gemeinsame Bausteine fuer Pruefbericht und Beschluss.
// Zahlen kommen bereits als formatierte Strings aus build.py.

#let accent = rgb("#1f3a5f")
#let soft = rgb("#eef2f7")
#let muted = rgb("#5a6472")

// Zeilen: (label, cur, vj, lvl, bold, sum)
#let fin-table(rows, has-vj, cur-head, vj-head) = {
  let cols = if has-vj { (1fr, 3cm, 3cm) } else { (1fr, 3cm) }
  let head = if has-vj {
    (table.header([], align(right, strong(cur-head)), align(right, strong(vj-head))),)
  } else {
    (table.header([], align(right, strong(cur-head))),)
  }
  let body = ()
  for r in rows {
    if r.sum { body.push(table.hline(stroke: 0.5pt + muted)) }
    let lab = pad(left: r.lvl * 0.55cm, if r.bold { strong(r.label) } else { r.label })
    let c = align(right, if r.bold { strong(r.cur) } else { r.cur })
    body.push(lab)
    body.push(c)
    if has-vj {
      body.push(align(right, if r.bold { strong(r.vj) } else { r.vj }))
    }
  }
  block(breakable: false, table(
    columns: cols,
    stroke: none,
    inset: (x: 4pt, y: 3.2pt),
    fill: (_, y) => if y == 0 { soft } else { none },
    ..head,
    ..body,
  ))
}
