"""Baut eine isolierte Testumgebung (Arbeitsordner) für einen Eval-Lauf.

Der Agent sieht nur, was er auch im Echtbetrieb hätte: Kontoauszüge, Belege,
Vorjahreswerte, Profil, Skill. Keine Ergebnisse des Steuerberaters aus dem Testjahr.

  python3 evals/fixture.py <ziel> --modus eval1|eval2 [--fall 2025|2024|2026_verkauf]
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


def build_aus_quellen(ziel: Path, fall: str, modus: str) -> None:
    """Testfall aus daten/evals/<fall>/: quellen.yaml (bank/belege/vorjahr, Pfade relativ zur Ablage)
    plus optional eigene Unterordner bank/, belege/, vorjahr/ (synthetische Dateien) im Fallordner."""
    fall_dir = DATEN / "evals" / fall
    quellen = yaml.safe_load((fall_dir / "quellen.yaml").read_text()) or {}
    for sub in ("bank", "belege", "vorjahr", "out"):
        (ziel / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("bank", "belege", "vorjahr"):
        dateien = sorted((fall_dir / sub).iterdir()) if (fall_dir / sub).is_dir() else []
        dateien += [UG / rel for rel in quellen.get(sub) or []]
        for f in dateien:
            if (ziel / sub / f.name).exists():
                raise SystemExit(f"Doppelter Dateiname in {sub}/: {f.name}")
            shutil.copy2(f, ziel / sub / f.name)
    if modus == "eval2" and (fall_dir / "antworten.md").exists():
        shutil.copy2(fall_dir / "antworten.md", ziel / "antworten.md")
    snapshot = fall_dir / "profil_snapshot.md"  # kein Wissen aus dem Prüfjahr
    profil = snapshot if snapshot.exists() else next((DATEN / "profil").glob("[!_]*.md"))
    shutil.copy2(profil, ziel / "profil.md")
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


def felder_vorjahr(ziel: Path, fall: str) -> None:
    """Formularfelder des Vorjahres (aus dessen Steuerberater-Erklärung) als Vorlage bereitstellen."""
    try:
        vj = str(int(fall[:4]) - 1)
    except ValueError:
        return
    quelle = DATEN / "evals" / vj / "felder_soll.yaml"
    if quelle.exists():
        (ziel / "vorjahr").mkdir(parents=True, exist_ok=True)
        shutil.copy2(quelle, ziel / "vorjahr/felder_vorjahr.yaml")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ziel", type=Path)
    ap.add_argument("--modus", choices=["eval1", "eval2"], required=True)
    ap.add_argument("--fall", default="2025", help="Ordnername unter daten/evals/")
    a = ap.parse_args()
    if a.ziel.exists():
        shutil.rmtree(a.ziel)
    if a.fall == "2025":
        build(a.ziel, a.modus)
    else:
        build_aus_quellen(a.ziel, a.fall, a.modus)
    felder_vorjahr(a.ziel, a.fall)
    print(f"Testumgebung {a.modus}: {a.ziel}")
