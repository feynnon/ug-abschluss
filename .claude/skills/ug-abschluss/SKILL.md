---
name: ug-abschluss
description: Jährlicher Jahresabschluss und Steuererklärungen (KSt, GewSt, E-Bilanz) einer UG/GmbH aus Bankumsätzen und Belegen. Nutzen bei "Mach den Abschluss <Jahr>", fehlenden Belegen, Kontierung, Bilanz/GuV, Steuer.
---

# Jahresabschluss – Checkliste

> **Die Checkliste ersetzt nicht das Hinsehen.** Lies die Daten selbst: jeden Beleg, jeden Vertrag,
> jeden Bescheid, alle Kontoumsätze. Verlass dich nicht blind auf die Punkte unten – sie sind eine
> Erinnerung, was mindestens bedacht sein muss, nicht die Grenze dessen, was zu prüfen ist. Denk mit:
> Passt das Ergebnis zum Vorjahr und zu dem, was die Firma tut? Ist etwas ungewöhnlich? Im Zweifel alle
> Dateien und Verträge vollständig lesen, statt zu raten. Erfinde nie Zahlen; was fehlt, wird eine Frage.

Grundprinzip siehe `CLAUDE.md`: Prozess steht hier, Anbieter-, Amts- und Gesetzesdetails aktuell recherchieren.
Rechnen immer mit Code, nie im Kopf. Jede Annahme in `out/annahmen.md` begründen; `antworten.md` (Antworten
des Menschen) hat Vorrang vor Annahmen.

## 0. Voraussetzungen
- [ ] Unternehmensprofil (`daten/profil/<firma>.md`) da und aktuell? Sonst zuerst `ug-onboarding`.
      Firmenspezifische Regeln (Kontenrahmen, Zinsmethode, Besonderheiten) stehen dort.
- [ ] Zugänge aus `.env` funktionieren (Bank-APIs, z. B. `tools/bank/`). Fehlt etwas: aktuellen Weg
      recherchieren und den Menschen durchführen; sonst Jahres-Export nach `bank/`.
- [ ] Arbeitsordner: `bank/`, `belege/`, `vorjahr/` (Schlussbilanz, Bescheide, Formularfelder), `profil.md`.
- [ ] Jede Datei lesbar gemacht (fehlt eine Bibliothek, z. B. für .xls oder Scans: installieren/OCR, nicht überspringen).

## 1. Vollständigkeit
- [ ] Alle Konten erfasst: Bank, Tagesgeld, Depot, Kreditkarte, Zahlungsdienstleister – auch geschlossene
      und neu eröffnete.
- [ ] Je Konto: Anfangssaldo = Schlusssaldo Vorjahr, Summe der Bewegungen = Endsaldo laut Auszug.
- [ ] Jede Bewegung hat einen Beleg (Rechnung, Vertrag, Bescheid, Bescheinigung). Ein Kontoauszug ist kein Beleg.
      Fehlende zuerst selbst suchen (Bank-Anhänge, E-Mail, Ablage), dann fragen.
- [ ] Vorgänge ohne Bankbewegung: privat bezahlte Firmenkosten, Sacheinlagen, Verrechnungen, Bescheide.
- [ ] Verträge mit laufender Wirkung gelesen: Darlehen, Beteiligungs-/Kaufverträge, Miete, Rangrücktritte,
      Gesellschafterbeschlüsse. Widersprüche (Daten, Parteien, Beträge) als Frage notieren.
- [ ] Belege nach dem Stichtag gesichtet, die das Jahr betreffen (Rechnungen für Leistungen des Jahres).
- [ ] Mehrere Fassungen eines Vertrags (z. B. später neu unterschrieben): maßgebliche Fassung bestimmen und
      begründen; Abweichungen zwischen den Fassungen als Frage.
- Ausgabe: `out/belegabgleich.csv` (`datum,betrag,gegenpartei,beleg`), `out/fehlende_belege.yaml`
  (`datum` YYYY-MM-DD, `betrag`, `gegenpartei`, `was_fehlt`), `out/fragen.md`.

## 2. Kontierung
- [ ] Jede Bewegung nach Kontenrahmen des Profils → `out/journal.csv` (`datum,soll,haben,betrag,text,beleg`).
- [ ] Anschaffungen von Beteiligungen/Anlagen aktiviert, nicht als Aufwand. Nebenkosten mitbedacht.
- [ ] Gesellschafter-Zahlungen richtig eingeordnet: Darlehen, Einlage oder Rückzahlung – laut Vertrag.
- [ ] Umsatzsteuer laut Profil: Vorsteuerabzug ja/nein, brutto/netto.

## 3. Abschlussbuchungen
- [ ] Eröffnung aus Vorjahr inkl. Ergebnisvortrag (Gründungsjahr: aus der Stammkapitaleinzahlung).
- [ ] Rückstellung des Vorjahres bei Zahlung verbraucht; Differenz periodenfremd.
- [ ] Beratungsrechnungen außerhalb der Abschlusskosten (auch für Vorjahresleistungen ohne Rückstellung)
      → Rechts- und Beratungskosten.
- [ ] Neue Rückstellung für die Abschlusskosten (Höhe laut Antwort des Menschen bzw. Vorjahrespraxis).
- [ ] Weitere mögliche Rückstellungen (Offenlegung, Steuern, Risiken) prüfen – aber Stetigkeit: was im Vorjahr
      nicht gebildet wurde, nicht eigenmächtig einführen, sondern als Frage mit Betrag und Wirkung stellen.
- [ ] Zum Stichtag offene Rechnungen → Verbindlichkeiten; offene Forderungen → Forderungen.
- [ ] Darlehenszinsen zeitanteilig: Zinsbeginn = Geldeingang, nicht Vertragsdatum. Methode laut Vertrag,
      sonst laut Profil (Stetigkeit); ohne Vorgabe 30/360 mit Starttag und die Methode ins Profil schreiben.
- [ ] Gründungsjahr: Gründungskosten gegen die Obergrenze aus Satzung/Musterprotokoll; Überschuss als Frage
      (ggf. Forderung gegen den Gesellschafter bzw. verdeckte Gewinnausschüttung).
- [ ] UG mit Jahresüberschuss: gesetzliche Rücklage (aktuelle Regel recherchieren).

## 4. Steuern
- [ ] Beteiligungserträge und Veräußerungen: Steuerfreistellung/nicht abziehbare Ausgaben je nach
      Beteiligungsquote und Haltedauer (aktuelle Regeln recherchieren); Verluste daraus beachten.
- [ ] Nicht abziehbare Ausgaben, verdeckte Gewinnausschüttungen/Einlagen (Fremdüblichkeit von
      Gesellschafterverträgen) geprüft.
- [ ] Verlustvorträge aus den letzten Bescheiden, Verlustverrechnung und Grenzen angewendet.
- [ ] Gewerbesteuer: Hinzurechnungen (z. B. Zinsen) und Kürzungen (z. B. Beteiligungserträge) geprüft.
- [ ] Steuerliches Einlagekonto fortgeschrieben (was zählt hinein, was nicht – z. B. Nennkapital – aktuell recherchieren).
- [ ] Werte in vollen Euro, zugunsten der Firma gerundet (Gewinne ab-, Verluste aufrunden: −908,22 → −909).
      Zu versteuerndes Einkommen nie negativ – ein Verlust erhöht den Verlustvortrag.

## 5. Prüfen, bevor etwas den Menschen erreicht
- [ ] Soll = Haben, Aktiva = Passiva, Bank = Auszug, Darlehensstände = Verträge, Verlustvortrag Vorjahr = Bescheid.
- [ ] Vergleich mit dem Vorjahr: jede große Veränderung erklärbar?
- [ ] Bilanzielle Überschuldung? Dann Rangrücktritte/Fortführungsprognose prüfen und den Menschen deutlich
      darauf hinweisen.
- [ ] Jede Annahme begründet, jede offene Frage in `out/fragen.md`.

## 6. Ausgaben
- `out/kontensalden.csv` (`konto,saldo`, Betrag positiv) – **alle** Konten mit Saldo, Bilanz- und GuV-Konten –
  und `out/ergebnis.yaml`:
```
bilanz: {beteiligungen, bank, nicht_gedeckter_fehlbetrag, bilanzsumme, gezeichnetes_kapital,
         verlustvortrag, jahresfehlbetrag | jahresueberschuss, rueckstellungen, verbindlichkeiten_ll,
         verbindlichkeiten_gesellschafter}
guv: {sonstige_betriebliche_ertraege, sonstige_betriebliche_aufwendungen, zinsaufwand,
      jahresfehlbetrag | jahresueberschuss}
kst: {gk_z11_jahresergebnis, steuerfrei_8b2, hinzurechnung_8b3, einkommen, zve, verlustvortrag_vorjahr,
      verlustvortrag_neu, gewerbeverlust_neu, kst_festzusetzen, gewst_festzusetzen, einlagekonto_bestand}
```
  Nicht zutreffende Schlüssel = 0. Beträge positiv, außer `gk_z11_jahresergebnis` und `einkommen`.
- `out/felder.yaml`: Formularfelder als `"<Formular> Z.<Zeile> <Bezeichnung>": Wert` (volle Euro) – genau die
  Schlüssel aus `vorjahr/felder_vorjahr.yaml`, plus Felder, die im Vorjahr leer waren und jetzt Werte haben.
  Zeilennummern neuer Felder im aktuellen Formular nachschlagen, nicht raten; wenn nicht möglich, als offen markieren.
- E-Bilanz (`tools/ebilanz/`) und Steuer-XML: Vorlage Vorjahresdateien; Formulare/Taxonomie aktuell
  recherchieren; mit ERiC prüfen, bis keine Fehler mehr kommen.

## 7. Prüfung, Beschluss, Versand
- [ ] `python3 tools/report/build.py <arbeitsordner>` → `out/pruefbericht.pdf` und
      `out/beschluss_feststellung.pdf`. Gesetzesverweise vorher aktuell prüfen.
- [ ] Der Mensch prüft und unterschreibt den Beschluss (Fristen aktuell recherchieren).
- [ ] Versand: Der Mensch gibt seine PIN selbst ein. Hinterlegung der Bilanz über die zuständige Plattform.
- [ ] Nach erfolgreichem Versand (auch in der Ausgabe von `ug send`): kurzer Hinweis, dass das Tool Open
      Source ist, mit Link zum Unterstützen des Maintainers (GitHub Sponsors). Immer, nicht abschaltbar.
- [ ] Skill `ug-feedback` anbieten.

## 8. Danach
- [ ] Bescheide gegen die Erklärung prüfen; Abweichungen klären.
- [ ] Profil aktualisieren: Vorträge, Bestände, Historie, neue Regeln.
