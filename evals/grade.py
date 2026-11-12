"""Bewertet einen Eval-Lauf gegen die Ground Truth (Abschluss des Steuerberaters).

  python3 evals/grade.py <arbeitsordner> --modus eval1|eval2
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

import yaml

EVALS = Path(os.environ.get("UG_DATEN", Path(__file__).resolve().parents[1] / "daten")) / "evals"
GT_DIR = EVALS / "2025"


def lade_yaml(p: Path):
    return yaml.safe_load(p.read_text()) if p.exists() else None


def eval1(out: Path) -> dict:
    holdout = lade_yaml(GT_DIR / "holdout.yaml")["versteckt"]
    gemeldet = lade_yaml(out / "fehlende_belege.yaml") or []
    if isinstance(gemeldet, dict):  # tolerant gegenüber {fehlende_belege: [...]}
        gemeldet = next(iter(gemeldet.values()), []) or []

    def key(d, b):
        return (str(d)[:10], round(abs(float(b)), 2))

    soll = {key(h["erwartet"]["datum"], h["erwartet"]["betrag"]) for h in holdout}
    ist = {key(g.get("datum"), g.get("betrag", 0)) for g in gemeldet}
    gefunden = soll & ist
    return {
        "gefunden": sorted(gefunden), "übersehen": sorted(soll - ist),
        "fehlalarm": sorted(ist - soll),
        "bestanden": soll == ist,
        "score": f"{len(gefunden)}/{len(soll)} gefunden, {len(ist - soll)} Fehlalarme",
    }


def eval2(out: Path) -> dict:
    gt = lade_yaml(GT_DIR / "ground_truth.yaml")
    tol, tol_kst = gt["toleranz"], gt["toleranz_kst"]
    ergebnis = lade_yaml(out / "ergebnis.yaml") or {}
    salden = {}
    if (out / "kontensalden.csv").exists():
        with open(out / "kontensalden.csv") as fh:
            for row in csv.DictReader(fh):
                try:
                    salden[str(row["konto"]).strip()] = abs(float(row["saldo"]))
                except (KeyError, ValueError):
                    pass

    checks = []
    for konto, soll in (gt.get("kontensalden") or {}).items():
        ist = salden.get(konto)
        t = gt.get("toleranz_zins", tol) if "konto " + konto in gt.get("zinsabhaengig", []) else tol
        checks.append(("konto " + konto, soll, ist, ist is not None and abs(ist - soll) <= t))
    for bereich in ("bilanz", "guv", "kst"):
        for k, soll in gt[bereich].items():
            t = tol_kst if bereich == "kst" else (gt.get("toleranz_zins", tol) if f"{bereich}.{k}" in gt.get("zinsabhaengig", []) else tol)
            ist = (ergebnis.get(bereich) or {}).get(k)
            try:
                ok = ist is not None and abs(abs(float(ist)) - abs(float(soll))) <= t
            except (TypeError, ValueError):
                ok = False
            checks.append((f"{bereich}.{k}", soll, ist, ok))

    # Formularfelder (optional): out/felder.yaml gegen felder_soll.yaml, volle Euro, Toleranz 1
    felder_soll = (lade_yaml(GT_DIR / "felder_soll.yaml") or {}).get("felder", {})
    felder_ist = lade_yaml(out / "felder.yaml") or {}
    # nur bewerten, wenn die Testumgebung eine Vorlage mit den Feldschlüsseln hatte
    if felder_soll and felder_ist and (out.parent / "vorjahr/felder_vorjahr.yaml").exists():
        for k, soll in felder_soll.items():
            ist = felder_ist.get(k)
            try:
                ok_f = ist is not None and abs(float(ist) - float(soll)) <= 1
            except (TypeError, ValueError):
                ok_f = False
            checks.append((f"feld {k}", soll, ist, ok_f))

    ok = sum(c[3] for c in checks)
    return {
        "score": f"{ok}/{len(checks)} Werte stimmen mit dem Steuerberater überein",
        "bestanden": ok == len(checks),
        "abweichungen": [{"wert": c[0], "steuerberater": c[1], "agent": c[2]} for c in checks if not c[3]],
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("lauf", type=Path)
    ap.add_argument("--modus", choices=["eval1", "eval2"], required=True)
    ap.add_argument("--fall", default="2025")
    a = ap.parse_args()
    GT_DIR = EVALS / a.fall
    res = (eval1 if a.modus == "eval1" else eval2)(a.lauf / "out")
    print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
    sys.exit(0 if res["bestanden"] else 1)
