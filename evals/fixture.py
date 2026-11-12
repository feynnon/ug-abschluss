"""Baut eine isolierte Testumgebung (Arbeitsordner) für einen Eval-Lauf.

Der Agent sieht nur, was er auch im Echtbetrieb hätte: Kontoauszüge, Belege,
Vorjahreswerte, Profil, Skill. Keine Ergebnisse des Steuerberaters aus dem Testjahr.

  python3 evals/fixture.py <ziel> --modus eval1|eval2
"""
import argparse
import os
import shutil
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
# Firmendaten liegen außerhalb des Repos (privat): $UG_DATEN oder Symlink ./daten
DATEN = Path(os.environ.get("UG_DATEN", REPO / "daten"))
CFG = yaml.safe_load((DATEN / "config.yaml").read_text())
UG = Path(CFG["ablage"]).expanduser()  # Ablage mit Originalbelegen
QUELLEN_2025 = yaml.safe_load((DATEN / "evals/2025/quellen.yaml").read_text())
UPLOAD = UG / QUELLEN_2025["upload_ordner"]


def build_2026_verkauf(ziel: Path) -> None:
    """Synthetischer Testfall Anteilsverkauf 2026: echte Belege 2026 + ausgedachter Verkauf."""
    fall = DATEN / "evals/2026_verkauf"
    for sub in ("bank", "belege", "vorjahr", "out"):
        (ziel / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("bank", "belege", "vorjahr"):
        for f in (fall / sub).iterdir():
            shutil.copy2(f, ziel / sub / f.name)
    echte = [UG / p for p in yaml.safe_load((fall / "quellen.yaml").read_text())["belege"]]
    for f in echte:
        shutil.copy2(f, ziel / "belege" / f.name)
    shutil.copy2(fall / "antworten.md", ziel / "antworten.md")
    shutil.copy2(next((DATEN / "profil").glob("[!_]*.md")), ziel / "profil.md")
    shutil.copy2(REPO / "profil/_vorlage.md", ziel / "profil_vorlage.md")
    shutil.copytree(REPO / ".claude", ziel / ".claude")


def build(ziel: Path, modus: str) -> None:
    if ziel.exists():
        shutil.rmtree(ziel)
    (ziel / "bank").mkdir(parents=True)
    (ziel / "belege").mkdir()
    (ziel / "vorjahr").mkdir()
    (ziel / "out").mkdir()

    holdout = yaml.safe_load((DATEN / "evals/2025/holdout.yaml").read_text())
    versteckt = {h["datei"] for h in holdout["versteckt"]} if modus == "eval1" else set()

    for pdf in sorted((UPLOAD / "4_Sonstige/Kontoauszuege 2025").glob("*.pdf")):
        shutil.copy2(pdf, ziel / "bank" / pdf.name)

    for sub in ("1_Rechnungseingang", "4_Sonstige"):
        for f in sorted((UPLOAD / sub).iterdir()):
            rel = f"{sub}/{f.name}"
            if f.is_dir() or f.name.startswith(("_", ".")) or rel in versteckt:
                continue
            shutil.copy2(f, ziel / "belege" / f.name)

    # Darlehensvertrag 2024 (Rangrücktritt) liegt schon in 4_Sonstige; Bescheide Vorjahr:
    for f in (UG / QUELLEN_2025["bescheide_vorjahr"]).glob("*Bescheid*2024*.pdf"):
        shutil.copy2(f, ziel / "vorjahr" / f.name)
    shutil.copy2(DATEN / "evals/2025/schlussbilanz_2024.yaml", ziel / "vorjahr/schlussbilanz_2024.yaml")

    if modus == "eval2":  # Eval 2 = Phase 1 ist erledigt, Rückfragen sind beantwortet
        shutil.copy2(DATEN / "evals/2025/antworten.md", ziel / "antworten.md")
    shutil.copy2(DATEN / "evals/2025/profil_snapshot.md", ziel / "profil.md")  # kein Wissen aus der Zukunft
    shutil.copy2(REPO / "profil/_vorlage.md", ziel / "profil_vorlage.md")
    shutil.copytree(REPO / ".claude", ziel / ".claude")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ziel", type=Path)
    ap.add_argument("--modus", choices=["eval1", "eval2"], required=True)
    ap.add_argument("--fall", default="2025", choices=["2025", "2026_verkauf"])
    a = ap.parse_args()
    if a.ziel.exists():
        shutil.rmtree(a.ziel)
    if a.fall == "2026_verkauf":
        build_2026_verkauf(a.ziel)
    else:
        build(a.ziel, a.modus)
    print(f"Testumgebung {a.modus}: {a.ziel}")
