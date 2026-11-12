# ug-abschluss

Jahresabschluss und Steuererklärungen kleiner Kapitalgesellschaften (UG/GmbH) mit Claude Code –
ohne Software mit Oberfläche. Der Mensch liefert Unterlagen, beantwortet Rückfragen, prüft und unterschreibt.

## Grundprinzip: so viel wie möglich an Claude auslagern, so wenig wie möglich festschreiben

Dieses Repo beschreibt **was** in welcher Reihenfolge passieren muss – nicht **wie** es bei einem
bestimmten Anbieter, Portal oder Amt gerade funktioniert. Das recherchiert Claude jedes Mal neu.

Festgeschrieben wird nur:
1. **Der Prozess**: Phasen, Reihenfolge, was am Ende jeder Phase vorliegen muss, wann der Mensch entscheidet.
2. **Wiederverwendbarer Code**, der exakt sein muss und sich selten ändert: Rechnen/Prüfen, ERiC-Anbindung.
3. **Wissen über die konkrete Firma**: Unternehmensprofil, Vorjahreswerte, Evals mit Sollwerten.
4. **Regeln, die aus Fehlern gelernt wurden** – kurz, mit Begründung, idealerweise mit Testfall.

Nicht festgeschrieben werden:
- Klickpfade, Menünamen, URLs von Formularen, Abläufe bei Banken, ELSTER, Registern, Steuerberatern.
  → Im Skill steht stattdessen: „Recherchiere den aktuellen Weg und führe den Menschen Schritt für Schritt.“
- Gesetzliche Details, Fristen, Grenzwerte, Steuersätze, soweit sie sich ändern können.
  → Recherchieren, mit Quelle nennen. Ausnahme: Werte, die der Rechencode braucht, mit Quelle und Stand.
- Anbieterspezifische Integrationen. Es gibt eine Liste von Integrations-*Kategorien*, keine Anbieter-Doku.

Bevor du etwas Neues ins Repo schreibst, frag dich: Kann Claude das beim nächsten Mal selbst herausfinden?
Wenn ja, schreib nur den Prozessschritt auf, nicht die Lösung.

## Weitere Regeln
- Das Repo ist öffentlich gedacht: **keine Firmendaten im Repo.** Profile, Evals mit echten Zahlen und
  Belege liegen in `daten/` (Symlink auf privaten Ordner, gitignored) bzw. `$UG_DATEN`.
- Keine Zugangsdaten im Chat wiederholen oder committen; sie liegen in `.env` (gitignored).
- Passwörter, PINs, CAPTCHAs und das Absenden von Erklärungen/Mails macht immer der Mensch.
- Texte, die der Mensch verschickt, vorher Satz für Satz gegen die Unterlagen prüfen.
- Der Mensch sieht am Ende jeder Antwort seine aktuelle To-do-Liste (mit Links).
- Evals dürfen kein Wissen aus dem Prüfjahr enthalten (Profil-Snapshot, versteckte Belege).

## Aufbau
- `.claude/skills/ug-onboarding/` – Einrichtung für eine neue Firma (einmalig)
- `.claude/skills/ug-abschluss/` – jährlicher Abschluss
- `.claude/skills/ug-feedback/` – anonymisiertes Feedback als GitHub-Issue
- `profil/_vorlage.md` – Vorlage; Profile je Firma in `daten/profil/`
- `evals/` – Testgerüst; Testfälle mit echten Sollwerten in `daten/evals/`
