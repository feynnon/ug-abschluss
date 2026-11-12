#!/usr/bin/env bash
# Ein Eval-Lauf: Testumgebung bauen, Claude Code headless laufen lassen, bewerten.
#   evals/run.sh eval1|eval2
set -euo pipefail
MODUS=${1:?eval1 oder eval2}
REPO=$(cd "$(dirname "$0")/.." && pwd)
LAUF="$REPO/evals/runs/$(date +%Y%m%d-%H%M%S)-$MODUS"

python3 "$REPO/evals/fixture.py" "$LAUF" --modus "$MODUS"

if [ "$MODUS" = eval1 ]; then
  AUFGABE="Nutze den Skill ug-abschluss. Führe für das Jahr 2025 nur Phase 1 (Vollständigkeit) aus. Es gibt keinen Zugriff auf E-Mail; arbeite nur mit diesem Ordner."
else
  AUFGABE="Nutze den Skill ug-abschluss. Erstelle den Jahresabschluss 2025 (Phasen 1 bis 4). Es gibt keinen Zugriff auf E-Mail und niemand beantwortet Rückfragen: Triff bei fehlenden Informationen die plausibelste Annahme, dokumentiere sie in out/annahmen.md und stelle die Frage zusätzlich in out/fragen.md."
fi

cd "$LAUF"
claude -p "$AUFGABE" \
  --allowedTools "Read" "Write" "Edit" "Glob" "Grep" "Skill" "Bash(pdftotext:*)" "Bash(python3:*)" "Bash(ls:*)" \
  --output-format json > "$LAUF/claude_output.json" 2> "$LAUF/claude_stderr.log" || true

python3 "$REPO/evals/grade.py" "$LAUF" --modus "$MODUS" | tee "$LAUF/grade.json" || true
echo "Lauf: $LAUF"
