---
name: ug-feedback
description: Am Ende eines Onboardings oder Jahresabschlusses Verbesserungsvorschläge für dieses Tool als anonymisiertes GitHub-Issue vorbereiten. Nutzen nach Abschluss von ug-onboarding oder ug-abschluss, oder wenn der Mensch "Feedback" sagt.
---

# Feedback an das Projekt

Ziel: Das Tool wird mit jedem Lauf besser, ohne dass private Daten das Gerät verlassen.

## Ablauf
1. Rückblick auf diesen Lauf: Wo hast du recherchieren müssen, was die Skills hätten sagen sollen? Wo hat
   eine Rückfrage an den Menschen sich als unnötig erwiesen? Wo war ein Schritt unklar, falsch oder fehlte?
   Wo hat ein Prüfcode/ERiC Fehler gemeldet? Höchstens die 3–5 wichtigsten Punkte.
2. Issue-Entwurf schreiben: Titel + Text mit Abschnitten „Was passiert ist“, „Was besser wäre“, „Betroffener
   Schritt/Skill“, Tool-Version (`git rev-parse --short HEAD`).
3. **Anonymisieren – Pflicht:** keine Firmennamen, Personennamen, Adressen, Steuernummern, IBANs,
   E-Mail-Adressen, keine konkreten Beträge oder Daten aus Belegen. Stattdessen allgemein beschreiben
   („eine zum Stichtag offene Beraterrechnung“). Im Zweifel weglassen.
4. Den vollständigen Text dem Menschen zeigen und fragen, ob er ihn so senden will. Ohne ausdrückliches Ja
   wird nichts gesendet.
5. Senden lassen – der Mensch schickt ab:
   - mit GitHub-CLI: `gh issue create --repo <repo> --title "…" --body-file <datei> --label feedback`
   - ohne: vorausgefüllten Link erzeugen
     `https://github.com/<repo>/issues/new?labels=feedback&title=<urlencoded>&body=<urlencoded>`
   Repo steht in `README.md`.
6. Keine Antwort/kein Interesse → einfach beenden, nicht erneut fragen.
