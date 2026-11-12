---
name: ug-onboarding
description: Einrichtung einer UG/GmbH für den Eigenabschluss mit Claude Code – Unternehmensprofil, Zugänge (Bank, Mail, Finanzamt, Offenlegung), Vertrauensaufbau über Evals mit Vorjahren, Übergabe vom Steuerberater. Nutzen bei "Onboarding", "einrichten", "neue Firma", "Setup".
---

# Onboarding – Checkliste

> **Die Checkliste ersetzt nicht das Hinsehen.** Lies die Unterlagen der Firma selbst – Gesellschaftsvertrag,
> Bescheide, Abschlüsse, Verträge, Mails mit Steuerberater und Finanzamt. Die Punkte unten sind das
> Minimum, nicht die Grenze. Denk mit: Was ist an dieser Firma besonders? Im Zweifel alles vollständig
> lesen, statt zu raten.

Ziel: Danach kann der Mensch jedes Jahr „Mach den Abschluss <Jahr>“ sagen.
Grundprinzip (`CLAUDE.md`): Hier steht **was** passieren muss. **Wie** es beim jeweiligen Anbieter/Amt
gerade geht, recherchierst du jedes Mal aktuell und führst den Menschen Schritt für Schritt (Link, Klickpfad,
was er eingibt, was er bekommt, wie lange es dauert). Findet die Recherche nichts Verlässliches: Unsicherheit
offen sagen, Quelle und Stand nennen, den Weg gemeinsam live gehen (der Mensch beschreibt, was er sieht).

Führe eine To-do-Liste für den Menschen (Datei in seiner Ablage) und zeig sie am Ende jeder Antwort.
Schritte mit Wartezeit (Post, Freischaltung) so früh wie möglich und parallel anstoßen.

## 1. Erwartungen und Rahmen
- [ ] Ablauf pro Jahr erklärt: Belege, Rückfragen, Prüfung, Unterschrift, PIN – und was Claude tut.
- [ ] Grenzen klar: Software, keine Steuerberatung; Verantwortung bleibt beim Menschen.
- [ ] Geklärt: Firma(en), wer es bisher macht, welches Jahr erstellt wird und welches Vorjahr Vergleich ist,
      wo Unterlagen liegen.
- [ ] Operatives Geschäft (Umsätze, Personal)? Laufende Pflichten (z. B. Umsatzsteuer-Voranmeldungen, Lohn)
      deckt dieses Repo nicht ab – ehrlich sagen und klären, wer sie übernimmt.

## 2. Unterlagen und Unternehmensprofil
- [ ] Zugriff auf Ablage und Postfach (Steuerberater, Finanzamt, Bank, Register, Notar). Ohne Postfach-Zugriff:
      Weiterleitung oder Export vorschlagen.
- [ ] Verfallende Quellen zuerst sichern (zeitlich begrenzte Bank-Historie, Portale vor Kündigung).
- [ ] Alles Relevante in die Ablage übernehmen, mit Index.
- [ ] Unternehmensprofil nach `profil/_vorlage.md` in `daten/profil/<firma>.md` (privat, nie ins Repo).
      Wichtigste Quellen: Gesellschaftsvertrag, Fragebogen zur steuerlichen Erfassung, letzte Bescheide,
      letzter Jahresabschluss. Jede Angabe mit Quelle.
- [ ] Lücken als „offen“, Widersprüche zwischen Quellen festhalten und auflösen.

## 3. Zugänge (Kategorien – Anbieterweg jeweils aktuell recherchieren)
- [ ] Bankkonten / Depots / Kreditkarten: API mit Lese-Key, sonst Jahres-Export.
- [ ] Zahlungsdienstleister, Rechnungstool: API oder Export.
- [ ] E-Mail und Cloud-Speicher: Connector bzw. lokal synchronisiert.
- [ ] Finanzamt-Zugang der Firma (zum Unterschreiben und Senden): Weg recherchieren; Pfad der Zugangsdatei in
      `.env`, Passwort/PIN gibt nur der Mensch ein. Postweg früh starten.
- [ ] Offenlegung/Hinterlegung: Konto auf der zuständigen Plattform.
- [ ] Steuerberater-Portal: Altunterlagen abholen.
- [ ] Empfangsvollmacht eines Steuerberaters? Dann kann Post dort landen – berücksichtigen.
- [ ] Zugangsdaten nur in `.env`, nie im Chat wiederholen.

## 4. Vertrauen aufbauen: Evals mit Vorjahren (anbieten, nicht erzwingen)
- [ ] Angeboten: „Soll ich zuerst ein Vorjahr nachrechnen und mit dem Steuerberater vergleichen?“
- [ ] Sollwerte aus Abschluss und Erklärungen des Steuerberaters (Formularfelder: `tools/elster/felder_aus_pdf.py`).
- [ ] Eval Vollständigkeit (Belege verstecken) und Eval Abschluss; Profil-Snapshot ohne Wissen aus dem Prüfjahr.
- [ ] Abweichungen erklärt und als Regel/Testfall festgehalten. Muster: `evals/`.
- [ ] Fehlt etwas für den Vergleich: kurze Mail an den Steuerberater **entwerfen** – nur, was sich nicht
      selbst klären lässt, jede Aussage gegen die Unterlagen geprüft. Der Mensch schickt ab.

## 5. Übergabe vom Steuerberater
- [ ] Erst wenn alle Altdaten da sind (inkl. Vertrag/AGB und Nachweisen erledigter Pflichten).
- [ ] Kündigung entwerfen; Zeitpunkt so, dass der Steuerberater nicht schon das nächste Jahr beginnt.
- [ ] Vollmacht/Empfangsvollmacht beim Finanzamt widerrufen – erst, wenn der eigene Zugang funktioniert.
- [ ] Bankverbindung beim Finanzamt aktuell; bei laufenden Pflichten klarer Stichtag, ab wann wer zuständig ist.

## 6. Abschluss des Onboardings
- [ ] Profil vollständig, Zugänge einmal testweise abgerufen.
- [ ] Nächste Fristen recherchiert, mit Quelle und Stand im Profil; offene Punkte auf der To-do-Liste.
- [ ] Skill `ug-feedback` angeboten; Übergabe an `ug-abschluss`.
