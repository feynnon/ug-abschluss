# tools/report – Prüfbericht und Feststellungsbeschluss (Phase 6/7)

Erzeugt aus dem Arbeitsordner einer Firma zwei PDFs für den Menschen:

- `out/pruefbericht.pdf` – Ergebnis in drei Sätzen, Bilanz und GuV (HGB, verkürzt für Kleinstkapitalgesellschaften,
  mit Vorjahresspalte), Steuerergebnis, automatische Plausibilitätsprüfungen, Annahmen, offene Fragen,
  Checkliste „Was du prüfen solltest“, Anhang Saldenliste und Journal.
- `out/beschluss_feststellung.pdf` – Entwurf eines Beschlusses des Alleingesellschafters (Feststellung des
  Jahresabschlusses, Ergebnisverwendung, Hinterlegung; Niederschrift nach § 48 Abs. 3 GmbHG), Anlage mit Bilanz/GuV
  und eine Hinweisseite (nicht Teil des Beschlusses).

## Benutzung
```
python3 -m venv .venv-report && .venv-report/bin/pip install -r tools/report/requirements.txt
.venv-report/bin/python tools/report/build.py <arbeitsordner> [--jahr 2025]
```
Typst steckt im Python-Paket `typst` (typst-py), es ist weder Admin-Recht noch eine Systeminstallation nötig.
Schrift: Helvetica Neue/Arial (Fallback Liberation/DejaVu) bzw. Libertinus Serif (mitgeliefert).

## Eingaben im Arbeitsordner
`out/ergebnis.yaml` und `out/kontensalden.csv` (Schema siehe Skill `ug-abschluss`, Phase 4), `out/journal.csv`,
`out/annahmen.md`, `out/fragen.md` (Listen mit `-` bzw. `1.`), `profil.md` (Firma, Sitz, Registergericht/HRB,
Stammkapital, Alleingesellschafter werden per Muster aus den Abschnitten „Stammdaten“ und „Personen“ gelesen; Fehlendes wird
als „[bitte ergänzen]“ markiert und als Warnung ausgegeben). Optional `vorjahr/schlussbilanz_<Vorjahr>.yaml`
(`kontensalden` + `jahresergebnis`, oder fertige `bilanz`/`guv`-Blöcke) für die Vorjahresspalte.

## Grenzen
- Entwurf, keine Rechts- oder Steuerberatung. Gesetzesverweise im Beschluss sind vor Verwendung zu prüfen.
- Vorjahres-GuV nur als Gesamtergebnis, wenn nur `jahresergebnis` vorliegt.
- Ein-Personen-Gesellschaft angenommen; bei mehreren Gesellschaftern ist der Beschluss anzupassen.
- Layout/Texte liegen in `templates/*.typ`, Logik in `build.py`.
