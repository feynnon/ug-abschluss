#import "common.typ": *
#let d = json("data.json")

#set page(
  paper: "a4",
  margin: (x: 2cm, top: 2.2cm, bottom: 2.4cm),
  footer: context [
    #set text(size: 8pt, fill: muted)
    #d.firma · Prüfbericht Jahresabschluss #d.jahr · ENTWURF
    #h(1fr) Seite #counter(page).display() von #counter(page).final().first()
  ],
)
#set text(font: ("Helvetica Neue", "Arial", "Liberation Sans", "DejaVu Sans"), size: 10pt, lang: "de")
#set par(leading: 0.62em, spacing: 0.9em)
#show heading.where(level: 1): it => {
  v(1.1em, weak: true)
  block(sticky: true, text(size: 14pt, weight: "bold", fill: accent, it.body))
  v(0.2em)
}
#show heading.where(level: 2): it => block(sticky: true, text(size: 11pt, weight: "bold", fill: accent, it.body))

#let box-note(body, fill: soft) = block(width: 100%, fill: fill, inset: 10pt, radius: 3pt, body)

// ---- Titel
#text(size: 9pt, fill: muted, tracking: 0.06em)[PRÜFBERICHT · ENTWURF ZUR DURCHSICHT]
#v(-0.3em)
#text(size: 22pt, weight: "bold", fill: accent)[Jahresabschluss #d.jahr]
#v(-0.5em)
#text(size: 13pt)[#d.firma]
#v(-0.3em)
#text(size: 9pt, fill: muted)[Stichtag #d.stichtag · Stand #d.erstellt · automatisch erstellt mit ug-abschluss (Claude Code)]
#v(0.5em)

#box-note[
  *Dieser Bericht ist für dich als Gesellschafter geschrieben.* Du musst kein Steuerexperte sein: Lies Abschnitt 1,
  geh dann die Checkliste in Abschnitt 8 durch und beantworte die offenen Fragen (Abschnitt 7). Erst wenn du
  zufrieden bist, unterschreibst du den Feststellungsbeschluss (separate Datei) und es geht in den Versand.
]

= 1  Das Ergebnis in drei Sätzen
#box-note(fill: rgb("#e8f1e8"))[
  #for (i, s) in d.summary.enumerate() [
    #s #if i < d.summary.len() - 1 [ ]
  ]
]
#if d.ueberschuldung [
  #box-note(fill: rgb("#fbeee0"))[
    *Achtung, Überschuldung in der Bilanz:* Die Schulden sind höher als das Vermögen
    (rechnerisch #d.eigenkapital_text EUR Eigenkapital). Das ist bei einer Holding mit Gesellschafterdarlehen
    nicht ungewöhnlich, muss aber bewusst beurteilt werden – siehe Checkliste, Punkt „Überschuldung“.
  ]
]

= 2  Bilanz zum #d.stichtag
Gliederung nach § 266 HGB in der verkürzten Form für Kleinstkapitalgesellschaften (§ 267a HGB). Beträge in EUR.
#v(0.3em)
#fin-table(d.aktiva, d.has_vj, d.stichtag, d.stichtag_vj)
#v(0.8em)
#fin-table(d.passiva, d.has_vj, d.stichtag, d.stichtag_vj)
#if d.fehlbetrag_note != "" [
  #v(0.3em)
  #text(size: 8.5pt, fill: muted)[#d.fehlbetrag_note]
]
#if d.has_vj [
  #v(0.2em)
  #text(size: 8.5pt, fill: muted)[Vorjahreswerte aus #d.vj_quelle.]
]

= 3  Gewinn- und Verlustrechnung #d.jahr
Gesamtkostenverfahren, verkürzt nach § 275 Abs. 5 HGB (Kleinstkapitalgesellschaft); Positionen ohne Betrag sind
weggelassen. Aufwand steht mit Minuszeichen. Beträge in EUR.
#v(0.3em)
#fin-table(d.guv, d.has_vj, str(d.jahr), str(d.jahr - 1))
#if d.guv_vj_note != "" [
  #v(0.3em)
  #text(size: 8.5pt, fill: muted)[#d.guv_vj_note]
]

= 4  Steuerergebnis
#d.steuer_intro
#v(0.3em)
#table(
  columns: (1fr, 2.6cm),
  stroke: none,
  inset: (x: 4pt, y: 3.5pt),
  fill: (_, y) => if y == 0 { soft } else { none },
  table.header([*Position*], align(right)[*EUR*]),
  ..d.steuer.map(s => (
    [#s.label #if s.hinweis != "" [\ #text(size: 8.5pt, fill: muted)[#s.hinweis]]],
    align(right, s.wert),
  )).flatten(),
)

= 5  Plausibilitätsprüfungen (automatisch)
#for c in d.checks [
  #grid(
    columns: (2.3cm, 1fr), gutter: 4pt,
    if c.ok { text(fill: rgb("#2f7a3a"), weight: "bold")[OK] } else { text(fill: rgb("#b3261e"), weight: "bold")[ABWEICHUNG] },
    c.text,
  )
  #v(-0.3em)
]

= 6  Annahmen, auf denen die Zahlen beruhen
Wo Unterlagen fehlten, hat Claude eine begründete Annahme getroffen. *Jede Annahme ist ein Punkt, den du bestätigen
oder korrigieren kannst.* Antworten des Gesellschafters haben immer Vorrang vor Annahmen.
#v(0.2em)
#if d.annahmen.len() == 0 [ _Keine Annahmen dokumentiert._ ] else [
  #for a in d.annahmen [
    #grid(columns: (0.5cm, 1fr), [•], a)
    #v(-0.25em)
  ]
]

= 7  Offene Fragen an dich
#if d.fragen.len() == 0 [ _Keine offenen Fragen._ ] else [
  Bitte beantworte jede Frage kurz (Ja/Nein oder Zahl). Antworten ändern gegebenenfalls Zahlen in diesem Bericht.
  #v(0.2em)
  #for (i, f) in d.fragen.enumerate() [
    #grid(columns: (0.8cm, 1fr), strong[#(i + 1).], f)
    #v(-0.25em)
  ]
]

= 8  Checkliste: Was du prüfen solltest
Nimm dir dafür 20–30 Minuten. Du brauchst nur den Kontoauszug, deine Verträge und diesen Bericht.
#v(0.3em)
#for c in d.checkliste [
  #block(breakable: false, grid(
    columns: (0.7cm, 1fr), gutter: 4pt,
    box(width: 9pt, height: 9pt, stroke: 0.8pt + accent, radius: 1pt),
    [*#c.punkt* #if c.hinweis != "" [\ #text(fill: muted)[#c.hinweis]]],
  ))
  #v(0.15em)
]
#v(0.5em)
#box-note[
  *Nächster Schritt:* Sind alle Punkte geklärt, gib Claude Bescheid. Dann werden Zahlen aktualisiert, falls du
  etwas korrigiert hast, und du bekommst den finalen Feststellungsbeschluss zur Unterschrift.
]

#pagebreak()
= Anhang A  Saldenliste zum #d.stichtag
Endsalden je Konto (Kontenrahmen laut Profil). Beträge in EUR, ohne Soll/Haben-Angabe.
#v(0.3em)
#table(
  columns: (1.6cm, 1fr, 2.6cm),
  stroke: none,
  inset: (x: 4pt, y: 2.8pt),
  fill: (_, y) => if y == 0 { soft } else { none },
  table.header([*Konto*], [*Bezeichnung*], align(right)[*Saldo*]),
  ..d.saldenliste.map(r => (r.at(0), r.at(1), align(right, r.at(2)))).flatten(),
)

= Anhang B  Buchungsjournal #d.jahr
#set text(size: 8pt)
#table(
  columns: (1.8cm, 0.9cm, 0.9cm, 1.8cm, 1fr, 4.6cm),
  stroke: none,
  inset: (x: 3pt, y: 2.4pt),
  fill: (_, y) => if y == 0 { soft } else { none },
  table.header([*Datum*], [*Soll*], [*Haben*], align(right)[*EUR*], [*Buchungstext*], [*Beleg*]),
  ..d.journal.map(r => (r.at(0), r.at(1), r.at(2), align(right, r.at(3)), r.at(4), r.at(5))).flatten(),
)
