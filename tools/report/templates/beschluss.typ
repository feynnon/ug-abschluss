#import "common.typ": *
#let d = json("data.json")

#set page(
  paper: "a4",
  margin: (x: 2.5cm, top: 2.5cm, bottom: 2.5cm),
  footer: context [
    #set text(size: 8pt, fill: muted)
    #d.firma · Beschluss zur Feststellung des Jahresabschlusses #d.jahr
    #h(1fr) Seite #counter(page).display() von #counter(page).final().first()
  ],
)
#set text(font: ("Libertinus Serif", "Times New Roman", "Liberation Serif"), size: 11pt, lang: "de")
#set par(justify: true, leading: 0.7em, spacing: 1em)
#show heading.where(level: 2): it => block(above: 1.5em, below: 0.7em, sticky: true, text(weight: "bold", it.body))

#align(center)[
  #text(size: 9pt, fill: muted)[ENTWURF – bitte erst nach Durchsicht des Prüfberichts unterschreiben]
  #v(0.6em)
  #text(size: 15pt, weight: "bold")[Beschluss des Alleingesellschafters]
  #v(0.1em)
  #text(size: 12pt)[zur Feststellung des Jahresabschlusses zum #d.stichtag \
  und zur Ergebnisverwendung]
  #v(0.2em)
  #text(size: 10pt)[(Niederschrift nach § 48 Abs. 3 GmbHG)]
]
#v(0.8em)

#block(fill: soft, inset: 10pt, radius: 3pt, width: 100%)[
  *Gesellschaft:* #d.firma \
  *Sitz:* #d.sitz #if d.register != "" [ · #d.register] \
  *Stammkapital:* #d.stammkapital EUR \
  *Alleingesellschafter:* #d.gesellschafter.name, #d.gesellschafter.anschrift #if d.gesellschafter.anteil != "" [ (#d.gesellschafter.anteil Prozent der Geschäftsanteile)]
]

Ich, #d.gesellschafter.name, bin Inhaber sämtlicher Geschäftsanteile an der #d.firma (nachfolgend „Gesellschaft“)
und damit ihr alleiniger Gesellschafter. Eine Gesellschafterversammlung wird nicht abgehalten; ich fasse die
nachstehenden Beschlüsse schriftlich. Auf alle Form- und Fristvorschriften für die Einberufung wird verzichtet.
Der Jahresabschluss zum #d.stichtag wurde von der Geschäftsführung aufgestellt#if d.gf_gleich [ (ich bin zugleich alleiniger Geschäftsführer)] und
liegt mir als Anlage 1 vor. Ich beschließe:

== 1. Feststellung des Jahresabschlusses (§ 46 Nr. 1 GmbHG)
Der Jahresabschluss der Gesellschaft zum #d.stichtag, bestehend aus Bilanz und Gewinn- und Verlustrechnung für
das Geschäftsjahr vom #d.beginn bis #d.stichtag, aufgestellt nach den Vorschriften für Kleinstkapitalgesellschaften
(§ 267a HGB), wird in der als *Anlage 1* beigefügten Fassung *festgestellt*.
Die Bilanzsumme beträgt #d.bilanzsumme EUR. Das Geschäftsjahr schließt mit einem *#d.ergebnis_wort* von
*#d.ergebnis_betrag EUR* ab.

== 2. Ergebnisverwendung (§ 46 Nr. 1, § 29 GmbHG)
#for p in d.verwendung [
  #p
  #v(-0.4em)
]

== 3. Hinterlegung des Jahresabschlusses
Der Geschäftsführer wird beauftragt, den festgestellten Jahresabschluss innerhalb der gesetzlichen Frist
(§ 326 Abs. 2 i. V. m. § 325 Abs. 1 HGB, spätestens bis #d.frist_offenlegung) beim Betreiber des Bundesanzeigers zu
hinterlegen und die Steuererklärungen für das Geschäftsjahr abzugeben.

#v(1.6em)
#grid(
  columns: (1fr, 1fr), gutter: 1.2cm,
  [
    #line(length: 100%, stroke: 0.5pt)
    #text(size: 9pt)[Ort, Datum]
  ],
  [
    #line(length: 100%, stroke: 0.5pt)
    #text(size: 9pt)[#d.gesellschafter.name \ Alleingesellschafter#if d.gf_gleich [ und Geschäftsführer]]
  ],
)

#pagebreak()
#align(center)[#text(size: 13pt, weight: "bold")[Anlage 1 zum Beschluss: Jahresabschluss zum #d.stichtag]]
#v(0.4em)
#set text(font: ("Helvetica Neue", "Arial", "Liberation Sans", "DejaVu Sans"), size: 9.5pt)
#text(weight: "bold", size: 11pt)[Bilanz] #h(1fr) #text(size: 8.5pt, fill: muted)[Beträge in EUR]
#fin-table(d.aktiva, d.has_vj, d.stichtag, d.stichtag_vj)
#v(0.5em)
#fin-table(d.passiva, d.has_vj, d.stichtag, d.stichtag_vj)
#if d.fehlbetrag_note != "" [
  #v(0.2em)
  #text(size: 8pt, fill: muted)[#d.fehlbetrag_note]
]
#v(0.8em)
#text(weight: "bold", size: 11pt)[Gewinn- und Verlustrechnung #d.jahr] #h(1fr) #text(size: 8.5pt, fill: muted)[Beträge in EUR]
#fin-table(d.guv, d.has_vj, str(d.jahr), str(d.jahr - 1))
#v(0.5em)
#text(size: 8.5pt, fill: muted)[Angaben unter der Bilanz nach § 264 Abs. 1 Satz 5 HGB (Kleinstkapitalgesellschaft): #d.angaben_unter_bilanz]

#pagebreak()
#text(size: 9pt, fill: muted, tracking: 0.05em)[HINWEISE ZUM ENTWURF – NICHT TEIL DES BESCHLUSSES, VOR DEM UNTERSCHREIBEN LESEN]
#v(0.3em)
#set text(font: ("Helvetica Neue", "Arial", "Liberation Sans", "DejaVu Sans"), size: 9.5pt)
#set par(justify: false)
#for h in d.hinweise [
  #grid(columns: (0.5cm, 1fr), [•], h)
  #v(-0.3em)
]
