---
name: ug-abschluss
description: Jährlicher Jahresabschluss und Steuererklärungen (KSt, GewSt, E-Bilanz) einer UG/GmbH aus Bankumsätzen und Belegen. Nutzen bei "Mach den Abschluss <Jahr>", fehlenden Belegen, Kontierung, Bilanz/GuV, Steuer.
---

# Jahresabschluss

Grundprinzip siehe `CLAUDE.md`: Prozess steht hier, Anbieter-/Amtsdetails recherchierst du aktuell.
Erfinde nie Zahlen. Fehlt eine Information, stell eine Frage statt zu raten.

## Phase 0 – Voraussetzungen
- Unternehmensprofil (`daten/profil/<firma>.md`) vorhanden und aktuell? Sonst zuerst Skill `ug-onboarding`.
  Firmenspezifische Buchungsregeln (Konten, Zinsmethode, Besonderheiten) stehen im Profil.
- Zugänge aus `.env` testen (Bank-APIs). Fehlt ein Konto oder geht ein Zugang nicht: aktuellen Weg
  recherchieren und den Menschen durchführen; ohne API einen Jahres-Export nach `bank/` legen lassen.

## Arbeitsordner
- `bank/` – Umsätze aller Konten des Jahres (API-Abruf oder Export)
- `belege/` – Eingangsrechnungen, Verträge, Bescheinigungen
- `vorjahr/` – Schlussbilanz Vorjahr (Kontensalden), Bescheide Vorjahr
- `profil.md` – Unternehmensprofil, `antworten.md` – Antworten des Menschen auf Rückfragen

## Phase 1 – Vollständigkeit
1. Bankbewegungen lesen, prüfen: Anfangssaldo = Schlusssaldo Vorjahr, Summe der Bewegungen = Endsaldo.
2. Jeder Bewegung einen Beleg zuordnen (Datum, Betrag, Gegenpartei). Fehlende Belege zuerst selbst suchen
   (Bank-Anhänge, E-Mail, Ablage), erst dann den Menschen fragen.
3. `out/belegabgleich.csv` (`datum,betrag,gegenpartei,beleg`), `out/fehlende_belege.yaml`
   (`datum` YYYY-MM-DD, `betrag`, `gegenpartei`, `was_fehlt`) – nur echte Lücken; ein Kontoauszug ist kein
   Beleg für eine Ausgabe.
4. `out/fragen.md`: Sachverhalte, die nicht aus den Unterlagen hervorgehen (z. B. zum Stichtag offene
   Rechnungen, Höhe der Abschlusskosten). Vorher selbst klären, was sich klären lässt.

## Phase 2 – Kontierung
Jede Bewegung nach dem Kontenrahmen aus dem Profil buchen → `out/journal.csv`
(`datum,soll,haben,betrag,text,beleg`).

## Phase 3 – Abschlussbuchungen
Allgemeine Regeln (aus Evals gelernt):
- Eröffnung aus Vorjahr inkl. Ergebnisvortrag.
- Rückstellung Vorjahr bei Zahlung der Abschlussrechnung verbrauchen; Differenz periodenfremd.
- Andere Beratungsrechnungen (auch für Vorjahresleistungen ohne Rückstellung) → Rechts- und Beratungskosten.
- Neue Rückstellung für die Abschlusskosten des laufenden Jahres.
- Zum Stichtag offene Rechnungen → Verbindlichkeiten (Quelle: Antworten, Zahlungen nach dem Stichtag, E-Mail).
- Darlehenszinsen zeitanteilig abgrenzen, Methode laut Vertrag, sonst laut Profil (Stetigkeit).
Jede Annahme in `out/annahmen.md` begründen; `antworten.md` hat Vorrang vor Annahmen.

## Phase 4 – Ergebnis
`out/kontensalden.csv` (`konto,saldo`, Betrag positiv) und `out/ergebnis.yaml`:
```
bilanz: {beteiligungen, bank, nicht_gedeckter_fehlbetrag, bilanzsumme, gezeichnetes_kapital,
         verlustvortrag, jahresfehlbetrag | jahresueberschuss, rueckstellungen, verbindlichkeiten_ll,
         verbindlichkeiten_gesellschafter}
guv: {sonstige_betriebliche_ertraege, sonstige_betriebliche_aufwendungen, zinsaufwand,
      jahresfehlbetrag | jahresueberschuss}
kst: {gk_z11_jahresergebnis, steuerfrei_8b2, hinzurechnung_8b3, einkommen, zve, verlustvortrag_vorjahr,
      verlustvortrag_neu, gewerbeverlust_neu, kst_festzusetzen, gewst_festzusetzen, einlagekonto_bestand}
```
Schlüssel, die nicht zutreffen, mit 0 angeben. Beträge positiv, außer `gk_z11_jahresergebnis` und
`einkommen` (mit Vorzeichen). KSt-Werte in vollen Euro. `zve` nie negativ (Verlust erhöht den Verlustvortrag).
Prüfen: Soll = Haben, Aktiva = Passiva, Bank-Saldo = Kontoauszug. Rechnen immer mit Code, nicht im Kopf.

## Phase 5–9 (im Aufbau)
5. E-Bilanz (XBRL) und Steuer-XML erzeugen – Vorlage: Vorjahresdateien; Formulare/Taxonomie aktuell
   recherchieren; mit ERiC prüfen, bis keine Fehler mehr kommen.
6. Review durch den Menschen (verständliche Zusammenfassung + PDFs).
7. Feststellungsbeschluss vorbereiten, Mensch unterschreibt.
8. Versand: Mensch gibt seine PIN selbst ein. Hinterlegung der Bilanz über die zuständige Plattform.
   Nach erfolgreichem Versand (auch Teil der Ausgabe von `ug send`): kurzer Hinweis, dass das Tool Open
   Source ist, mit Link zum Unterstützen des Maintainers (GitHub Sponsors). Immer anzeigen, nicht abschaltbar.
   Danach Skill `ug-feedback` anbieten.
9. Bescheide prüfen, Profil (Vorträge, Historie) aktualisieren.
