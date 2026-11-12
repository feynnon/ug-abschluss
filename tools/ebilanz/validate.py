#!/usr/bin/env python3
"""Validiert eine E-Bilanz-Instanz mit Arelle gegen die lokal entpackte HGB-Taxonomie.

Prüft XBRL 2.1 (Schema, Kontexte, Einheiten, Tupel), XBRL Dimensions und die Rechenregeln
(calculation linkbase, Calc 1.0). Prüft NICHT die ERiC-Plausibilitäten der Finanzverwaltung
(Mussfelder, Kontennachweis-Regeln, Steuernummer, Plausis zwischen Positionen) – siehe README.md.

Aufruf: python validate.py --taxonomie <dir> --instanz <datei.xbrl> [--arelle arelleCmdLine]
Exit-Code 0 = keine Fehler/Inkonsistenzen.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import taxonomie  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--taxonomie", required=True, type=Path)
    ap.add_argument("--instanz", required=True, type=Path)
    ap.add_argument("--arelle", default="arelleCmdLine")
    ap.add_argument("--paket", type=Path, help="Ablage für das erzeugte Taxonomie-Paket (Standard: temporär)")
    a = ap.parse_args(argv)

    paket = a.paket or Path(tempfile.gettempdir()) / f"hgb-taxonomie-{taxonomie.datum(a.taxonomie)}.zip"
    taxonomie.paket(a.taxonomie, paket)
    cmd = [a.arelle, "--file", str(a.instanz), "--packages", str(paket), "--validate", "--calc", "c10",
           "--internetConnectivity", "offline", "--logLevel", "info"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    log = (p.stdout + p.stderr).splitlines()
    probleme = [z for z in log if re.search(r"\[(?!info)[^\]]*\]", z) and not re.search(r"\[info\]", z)]
    for z in log:
        print(z)
    schwer = [z for z in probleme if re.search(r"error|exception|inconsisten|\[(xbrl|xbrldie|xbrldte|xmlSchema|"
                                                r"calc|arelle|webCache)[^\]]*\]", z, re.I)]
    print(f"\n{len(schwer)} Fehler/Inkonsistenzen, {len(probleme) - len(schwer)} sonstige Meldungen")
    return 1 if schwer or p.returncode else 0


if __name__ == "__main__":
    sys.exit(main())
