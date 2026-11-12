"""Prüft, ob ein Eval-Agent außerhalb seines Arbeitsordners gelesen hat (Schummel-Kontrolle).

  python3 evals/audit.py <transkript.jsonl> <arbeitsordner>

Liest alle Werkzeugaufrufe aus dem Transkript (Claude Code stream-json bzw. Sub-Agent-Transkript) und
meldet jeden Pfad außerhalb des Arbeitsordners sowie Zugriffe auf Sollwerte/Steuerberater-Unterlagen.
Exit-Code 1, wenn etwas Verdächtiges gefunden wurde.
"""
import json
import re
import sys
from pathlib import Path

ERLAUBT = [re.compile(p) for p in (
    r"/\.claude/projects/[^/]+/memory/",   # wird vom System automatisch geladen
    r"^/(usr|bin|opt|private/var|tmp|System|Library/Frameworks)/",
    r"/scratchpad/|^/private/tmp/claude-\d+/scratch",  # eigene Hilfsskripte des Agenten
    r"/miniconda3/|/\.venv/|site-packages",
)]
VERDAECHTIG = re.compile(r"ground_truth|felder_soll|holdout|daten/|/evals/(?!runs/)", re.I)


def pfade(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("file_path", "path", "notebook_path") and isinstance(v, str):
                yield v
            elif k == "command" and isinstance(v, str):
                yield from re.findall(r"((?:~|/Users|/Volumes|/private|/home)/[^\s'\"|;&<>]+|(?<![\w/])\.\./[^\s'\"|;&<>]*)", v)
            else:
                yield from pfade(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from pfade(v)


def main() -> int:
    transkript, arbeit = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
    funde = set()
    for zeile in transkript.read_text(errors="ignore").splitlines():
        try:
            ereignis = json.loads(zeile)
        except json.JSONDecodeError:
            continue
        for p in pfade(ereignis.get("message", ereignis)):
            if VERDAECHTIG.search(p) or p.startswith("../../../"):
                funde.add(p)
                continue
            if (p.startswith("/") or p.startswith("~")) and not p.startswith(str(arbeit)) and not any(e.search(p) for e in ERLAUBT):
                funde.add(p)
    for f in sorted(funde):
        print("VERDÄCHTIG:", f)
    print("sauber" if not funde else f"{len(funde)} verdächtige Zugriffe")
    return 1 if funde else 0


if __name__ == "__main__":
    sys.exit(main())
