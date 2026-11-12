---
name: ug-onboarding
description: Einrichtung einer UG/GmbH für den Eigenabschluss mit Claude Code – Unternehmensprofil, Zugänge (Bank, Mail, ELSTER, Offenlegung), Vertrauensaufbau über Evals mit Vorjahren, Übergabe vom Steuerberater. Nutzen bei "Onboarding", "einrichten", "neue Firma", "Setup".
---

# Onboarding

Ziel: Nach dem Onboarding kann der Mensch jedes Jahr „Mach den Abschluss <Jahr>“ sagen.
Grundprinzip (siehe `CLAUDE.md`): Hier steht **was** passieren muss. **Wie** es beim jeweiligen
Anbieter/Amt gerade geht, recherchierst du jedes Mal aktuell und führst den Menschen Schritt für Schritt
(Link, Klickpfad, was er eingeben muss, was er danach bekommt, wie lange es dauert).

Führe eine To-do-Liste für den Menschen (Datei im Unterlagen-Ordner der Firma) und zeig sie am Ende jeder
Antwort. Starte Schritte mit Wartezeit (Post, Freischaltung) so früh wie möglich und parallel.

## 1. Erwartungen klären
Kurz erklären: Ablauf pro Jahr, was der Mensch tun muss (Belege, Rückfragen, Prüfung, Unterschrift, PIN),
was Claude tut, wo die Grenzen sind (Haftung bleibt beim Menschen; keine Steuerberatung).
Fragen: Firma(en), wer macht es bisher (Steuerberater?), welche Jahre, wo liegen Unterlagen.

## 2. Unterlagen finden und Unternehmensprofil erstellen
- Zugriff auf die Ablage (Cloud-Speicher/lokaler Ordner) und das Postfach, über das Steuerberater,
  Finanzamt, Bank und Register schreiben. Alles relevante in die Ablage übernehmen, mit Index.
- Unternehmensprofil nach `profil/_vorlage.md` in `daten/profil/<firma>.md` erstellen (privater Ordner, nie ins Repo). Wichtigste Quellen: Gesellschaftsvertrag,
  Fragebogen zur steuerlichen Erfassung, letzte Bescheide, letzter Jahresabschluss.
- Lücken als „offen“ markieren und gezielt beim Menschen nachfragen.

## 3. Zugänge einrichten (Integrations-Kategorien)
Für jede Kategorie: herausfinden, was die Firma nutzt; aktuell recherchieren, ob es einen
API-/Export-Weg gibt; den Menschen durchführen; Zugangsdaten landen in `.env`, nie im Chat.

| Kategorie | Wozu | Bevorzugt |
|---|---|---|
| Bankkonten / Depots | Umsätze, Kontostände, Belege | API mit Lese-Key, sonst Jahres-Export |
| E-Mail | Rechnungen, Bescheide, Steuerberater-Korrespondenz | Connector |
| Cloud-Speicher | Ablage aller Unterlagen | Connector / lokal synchronisiert |
| ELSTER (Steuerpflichtiger) | Erklärungen signieren und senden | Organisationszertifikat der Firma |
| ELSTER (Hersteller) | ERiC, Hersteller-ID – nur nötig, solange das Tool nicht fertig ausgeliefert ist | Entwicklerregistrierung |
| Offenlegung / Hinterlegung | Bilanz beim Unternehmensregister | Konto auf der zuständigen Plattform |
| Steuerberater-Portal | Altunterlagen abholen | Export / Download |

Schritte mit Postweg (z. B. ELSTER-Aktivierungscode) zuerst anstoßen. Prüfen, ob ein Steuerberater
empfangsbevollmächtigt ist – dann kann Post dort landen.

## 4. Vertrauen aufbauen: Evals mit Vorjahren (anbieten, nicht erzwingen)
Frag, ob der Mensch zuerst sehen will, dass Claude ein Vorjahr genauso hinbekommt wie der Steuerberater.
Wenn ja:
- Sollwerte aus dem Abschluss des Steuerberaters (Bilanz, GuV, Kontennachweis, Erklärungen) übernehmen.
- Eval „Vollständigkeit“: einige Belege verstecken, Claude muss genau diese finden.
- Eval „Abschluss“: aus Bank + Belegen alle Werte ableiten, Abweichungen erklären und als Regel/Testfall
  festhalten. Profil-Snapshot ohne Wissen aus dem Prüfjahr verwenden.
- Fehlt etwas für einen vollständigen Vergleich (z. B. übermittelte E-Bilanz, ELSTER-Protokolle,
  Kontenblätter), eine kurze Mail an den Steuerberater **entwerfen**: nur das anfragen, was sich nicht
  selbst klären lässt. Vorher alles recherchieren/aus den Unterlagen klären. Der Mensch schickt ab.
Muster: `evals/` in diesem Repo.

## 5. Übergabe vom Steuerberater
Erst wenn alle benötigten Altdaten da sind: Kündigung entwerfen (Vertragsbedingungen prüfen),
Vollmacht/Empfangsvollmacht beim Finanzamt widerrufen, Bankverbindung beim Finanzamt aktuell halten.
Zeitpunkt so wählen, dass der Steuerberater nicht schon mit dem nächsten Jahr beginnt.

## 6. Abschluss des Onboardings
- Profil vollständig, Zugänge funktionieren (einmal testweise abrufen), Fristen des nächsten Abschlusses
  im Profil, offene Punkte auf der To-do-Liste.
- Skill `ug-feedback` anbieten.
- Übergabe an den Skill `ug-abschluss`.
