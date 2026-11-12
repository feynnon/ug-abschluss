# ug-abschluss

Jahresabschluss und Steuererklärungen (Körperschaftsteuer, Gewerbesteuer, E-Bilanz) für kleine
Kapitalgesellschaften (UG/GmbH) – mit Claude Code, ohne Buchhaltungssoftware.

Du lieferst Bankumsätze und Belege, beantwortest Rückfragen, prüfst das Ergebnis und reichst mit deinem
eigenen ELSTER-Zertifikat ein. Claude erledigt den Rest.

> **Status: in Entwicklung.** Buchhaltung bis Bilanz und Steuerberechnung ist gegen echte
> Steuerberater-Abschlüsse getestet. Erzeugen und Prüfen der ELSTER-Daten und der Versand sind im Aufbau.

## Wichtig
- Das ist Software, keine Steuerberatung. Du reichst selbst ein und bist für den Inhalt verantwortlich.
- Deine Daten bleiben bei dir: Firmendaten liegen außerhalb des Repos (`daten/`, siehe unten),
  Zugangsdaten in `.env`. Beides wird nie committet.

## Loslegen
1. Repo klonen und in Claude Code öffnen.
2. „Starte das Onboarding für meine Firma“ – der Skill `ug-onboarding` führt dich durch alles Weitere.
3. Jedes Jahr: „Mach den Abschluss <Jahr>“.

## Aufbau
- `CLAUDE.md` – Grundprinzip: Prozess festschreiben, Details jedes Mal aktuell recherchieren
- `.claude/skills/` – `ug-onboarding`, `ug-abschluss`, `ug-feedback`
- `profil/_vorlage.md` – Vorlage für das Unternehmensprofil
- `evals/` – Testgerüst: baut eine isolierte Testumgebung aus einem Vorjahr und vergleicht mit den Werten
  des Steuerberaters
- `daten/` (nicht im Repo) – deine Firmendaten: `config.yaml` (Pfad zur Ablage), `profil/`, `evals/`.
  Am besten ein Symlink auf einen privaten Ordner; alternativ Umgebungsvariable `UG_DATEN`.

## Feedback
Nach jedem Lauf schlägt Claude ein anonymisiertes Issue vor (Skill `ug-feedback`). Du siehst den Text
vollständig und entscheidest selbst, ob du ihn abschickst. Repo: `feynnon/ug-abschluss`.

## Unterstützen
Das Projekt ist kostenlos und Open Source. Wenn es dir den Steuerberater gespart hat, freue ich mich über
Unterstützung via [GitHub Sponsors](https://github.com/sponsors/feynnon).

## Lizenz
[GNU AGPL-3.0](LICENSE)
