"""Umsätze und Belege eines Jahres per Qonto-API in einen Arbeitsordner holen.

  python3 tools/bank/qonto.py <arbeitsordner> --jahr 2025 [--env .env]

Schreibt <arbeitsordner>/bank/qonto_<iban-ende>_<jahr>.csv und lädt angehängte Belege nach
<arbeitsordner>/belege/qonto/. Zugangsdaten aus .env: QONTO_LOGIN, QONTO_SECRET_KEY.
Nur lesende Endpunkte. Anbieterdetails können sich ändern – bei Fehlern die aktuelle API-Doku prüfen.
"""
import argparse
import csv
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://thirdparty.qonto.com/v2"


def lade_env(pfad: Path) -> None:
    if not pfad.exists():
        return
    for zeile in pfad.read_text().splitlines():
        zeile = zeile.strip()
        if zeile and not zeile.startswith("#") and "=" in zeile:
            k, v = zeile.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def get(pfad: str, **params):
    url = f"{API}{pfad}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={
        "Authorization": f"{os.environ['QONTO_LOGIN']}:{os.environ['QONTO_SECRET_KEY']}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ziel", type=Path)
    ap.add_argument("--jahr", type=int, required=True)
    ap.add_argument("--env", type=Path, default=Path(__file__).resolve().parents[2] / ".env")
    ap.add_argument("--ohne-belege", action="store_true")
    a = ap.parse_args()
    lade_env(a.env)

    org = get("/organization")["organization"]
    (a.ziel / "bank").mkdir(parents=True, exist_ok=True)
    beleg_dir = a.ziel / "belege" / "qonto"
    for konto in org["bank_accounts"]:
        txs, seite = [], 1
        while seite:
            d = get("/transactions", bank_account_id=konto["id"], per_page=100, current_page=seite,
                    **{"status[]": "completed", "settled_at_from": f"{a.jahr}-01-01T00:00:00Z",
                       "settled_at_to": f"{a.jahr}-12-31T23:59:59Z"})
            txs += d["transactions"]
            seite = d["meta"]["next_page"]
        txs.sort(key=lambda t: t["settled_at"])
        datei = a.ziel / "bank" / f"qonto_{konto['iban'][-4:]}_{a.jahr}.csv"
        with open(datei, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["datum", "betrag", "gegenpartei", "verwendungszweck", "referenz", "belege"])
            for t in txs:
                betrag = t["amount"] if t["side"] == "credit" else -t["amount"]
                namen = []
                if not a.ohne_belege:
                    for att_id in t.get("attachment_ids") or []:
                        att = get(f"/attachments/{att_id}")["attachment"]
                        beleg_dir.mkdir(parents=True, exist_ok=True)
                        name = f"{t['settled_at'][:10]}_{att['file_name']}"
                        urllib.request.urlretrieve(att["url"], beleg_dir / name)
                        namen.append(name)
                w.writerow([t["settled_at"][:10], f"{betrag:.2f}", t.get("label", ""),
                            t.get("reference") or "", t.get("transaction_id", ""), ";".join(namen)])
        saldo = sum((t["amount"] if t["side"] == "credit" else -t["amount"]) for t in txs)
        print(f"{datei.name}: {len(txs)} Buchungen, Summe {saldo:.2f}, aktueller Kontostand {konto['balance']}")


if __name__ == "__main__":
    main()
