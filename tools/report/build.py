#!/usr/bin/env python3
"""Phase 6/7: Pruefbericht und Feststellungsbeschluss als PDF erzeugen.

Aufruf:  python tools/report/build.py <arbeitsordner> [--jahr 2025]

Liest <arbeitsordner>/out/{kontensalden.csv,ergebnis.yaml,annahmen.md,fragen.md,journal.csv} und
<arbeitsordner>/profil.md (optional: vorjahr/schlussbilanz_<jahr-1>.yaml) und schreibt nach
<arbeitsordner>/out/: pruefbericht.pdf, beschluss_feststellung.pdf.
Keine Firmendaten im Repo: alles kommt aus dem Arbeitsordner.
"""
import argparse
import csv
import json
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

import typst
import yaml

HERE = Path(__file__).parent
PLATZHALTER = "[bitte ergänzen]"

# Bezeichnungen SKR03 (nur Anzeige; unbekannte Konten erscheinen als "Konto N")
SKR03 = {
    "517": "Anteile an verbundenen Unternehmen / Beteiligungen", "505": "Beteiligungen",
    "730": "Verbindlichkeiten gegenüber Gesellschaftern (aufgelaufene Zinsen)",
    "750": "Verbindlichkeiten gegenüber Gesellschaftern (Darlehen)",
    "800": "Gezeichnetes Kapital", "868": "Verlustvortrag", "977": "Sonstige Rückstellungen (Abschlusskosten)",
    "1200": "Bank", "1610": "Verbindlichkeiten aus Lieferungen und Leistungen",
    "2020": "Periodenfremde Aufwendungen", "2114": "Zinsen auf Gesellschafterdarlehen",
    "4900": "Sonstige betriebliche Aufwendungen", "4950": "Rechts- und Beratungskosten",
    "4957": "Abschluss- und Prüfungskosten", "4970": "Nebenkosten des Geldverkehrs",
    "9000": "Saldenvorträge / Eröffnung",
}


# ---------- Hilfen ----------
def eur(x, vorzeichen=False):
    """1234.5 -> '1.234,50' (deutsches Format)."""
    s = f"{abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if x < -0.004:
        return "-" + s
    return ("+" + s) if vorzeichen and x > 0.004 else s


def eur0(x):
    return f"{round(x):,}".replace(",", ".")


def dt(d):
    return d.strftime("%d.%m.%Y")


def lese_csv(p):
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lese_yaml(p):
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}


def lese_liste(p):
    """Markdown-Liste ('- ' oder '1. ') -> Liste von Strings; Folgezeilen werden angehängt."""
    if not p.exists():
        return []
    items = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$", line)
        if m:
            items.append(m.group(1).strip())
        elif items:
            items[-1] += " " + line.strip()
    return [re.sub(r"[*_`]", "", i) for i in items]


def num(d, k):
    return float((d or {}).get(k) or 0)


# ---------- Profil ----------
def lese_profil(p, warn):
    txt = p.read_text(encoding="utf-8") if p.exists() else ""
    pr = {"firma": PLATZHALTER, "sitz": PLATZHALTER, "sitz_kurz": "", "register": "", "stammkapital": PLATZHALTER,
          "gesellschafter": {"name": PLATZHALTER, "anschrift": PLATZHALTER, "anteil": ""}, "gf_gleich": False}
    m = re.search(r"^#\s*Unternehmensprofil\s*[–-]?\s*(.+)$", txt, re.M)
    if m:
        pr["firma"] = m.group(1).strip()
    else:
        warn("Firmenname nicht im Profil gefunden")
    m = re.search(r"^-\s*" + re.escape(pr["firma"]) + r",\s*(.+?,\s*(\d{5})\s+([^\n,]+))\s*$", txt, re.M)
    if m:
        pr["sitz"] = m.group(3).strip()
        pr["sitz_kurz"] = m.group(3).strip()
    else:
        warn("Sitz nicht im Profil gefunden (erwartet: '- <Firma>, <Straße>, <PLZ> <Ort>')")
    m = re.search(r"(?:AG|Amtsgericht)\s+([A-ZÄÖÜa-zäöüß-]+)\s+(HR[AB]\s*\d+)", txt)
    if m:
        pr["register"] = f"Amtsgericht {m.group(1)}, {m.group(2)}"
    else:
        warn("Registergericht/HRB nicht im Profil gefunden")
    m = re.search(r"Stammkapital\s+([\d.]+(?:,\d+)?)\s*(?:EUR|€)", txt)
    if m:
        pr["stammkapital"] = m.group(1)
    else:
        warn("Stammkapital nicht im Profil gefunden")
    m = re.search(r"^-\s*([^,\n]+?),\s*(?:geb\.\s*[\d.]+,\s*)?([^:\n]+?):\s*(\d+)\s*%\s*Gesellschafter([^\n]*)$", txt, re.M)
    if m:
        pr["gesellschafter"] = {"name": m.group(1).strip(), "anschrift": m.group(2).strip(), "anteil": m.group(3)}
        pr["gf_gleich"] = bool(re.search(r"\bGF\b|Geschäftsführer", m.group(4)))
    else:
        warn("Alleingesellschafter nicht im Profil gefunden (erwartet: '- Name, [geb. ..,] Anschrift: 100 % Gesellschafter, ...')")
    return pr


# ---------- Bilanzlogik ----------
def bilanz_werte(b):
    """Normalisiert ein bilanz-Dict (Schema aus SKILL.md Phase 4)."""
    w = {}
    w["beteiligungen"] = num(b, "beteiligungen")
    w["bank"] = num(b, "bank")
    kap, vv = num(b, "gezeichnetes_kapital"), num(b, "verlustvortrag")
    erg = num(b, "jahresueberschuss") - num(b, "jahresfehlbetrag")
    ek = kap - vv + erg
    w.update(kapital=kap, vortrag=-vv, ergebnis=erg, ek_rechn=ek)
    w["fehlbetrag"] = max(0.0, -ek)
    w["ek"] = max(0.0, ek)
    w["rueck"] = num(b, "rueckstellungen")
    w["vll"] = num(b, "verbindlichkeiten_ll")
    w["vges"] = num(b, "verbindlichkeiten_gesellschafter")
    w["aktiva"] = w["beteiligungen"] + w["bank"] + w["fehlbetrag"]
    w["passiva"] = w["ek"] + w["rueck"] + w["vll"] + w["vges"]
    return w


def bilanz_aus_salden(salden, ergebnis):
    """Vorjahresbilanz aus Kontensalden (SKR03-Bereiche) ableiten."""
    b = dict.fromkeys(["beteiligungen", "bank", "gezeichnetes_kapital", "verlustvortrag", "rueckstellungen",
                       "verbindlichkeiten_ll", "verbindlichkeiten_gesellschafter"], 0.0)
    for k, v in salden.items():
        k, v = int(k), float(v)
        if 500 <= k < 530:
            b["beteiligungen"] += v
        elif 1200 <= k < 1300:
            b["bank"] += v
        elif k == 800:
            b["gezeichnetes_kapital"] += v
        elif k == 868:
            b["verlustvortrag"] += v
        elif 970 <= k < 980:
            b["rueckstellungen"] += v
        elif 1600 <= k < 1700:
            b["verbindlichkeiten_ll"] += v
        elif k in (730, 750) or 700 <= k < 760:
            b["verbindlichkeiten_gesellschafter"] += v
    if ergebnis is not None:
        b["jahresfehlbetrag" if ergebnis < 0 else "jahresueberschuss"] = abs(ergebnis)
    return b


def row(label, cur="", vj="", lvl=0, bold=False, sum=False):
    return dict(label=label, cur=cur, vj=vj, lvl=lvl, bold=bold, sum=sum)


def bilanz_zeilen(c, v):
    """c, v: bilanz_werte (v darf None sein). Gibt (aktiva, passiva, fehlbetrag_note)."""
    def f(key, neg=False, signed=False):
        a = eur(c[key], signed)
        b = eur(v[key], signed) if v else ""
        return a, b
    def r(label, key, lvl=1, bold=False, sum=False, signed=False):
        a, b = f(key, signed=signed)
        return row(label, a, b, lvl, bold, sum)

    akt = [row("AKTIVA", bold=True),
           row("A. Anlagevermögen", lvl=0, bold=True), r("Finanzanlagen: Beteiligungen", "beteiligungen", 1)]
    akt += [row("B. Umlaufvermögen", bold=True), r("Guthaben bei Kreditinstituten", "bank", 1)]
    if c["fehlbetrag"] or (v and v["fehlbetrag"]):
        akt.append(row("F. Nicht durch Eigenkapital gedeckter Fehlbetrag", *f("fehlbetrag"), 0, True))
    akt.append(r("Summe Aktiva", "aktiva", 0, True, True))

    pas = [row("PASSIVA", bold=True), row("A. Eigenkapital", bold=True),
           r("I. Gezeichnetes Kapital", "kapital", 1)]
    if c["vortrag"] or (v and v["vortrag"]):
        pas.append(r("IV. Verlustvortrag", "vortrag", 1))
    lab = "V. Jahresüberschuss" if c["ergebnis"] > 0 else "V. Jahresfehlbetrag"
    pas.append(r(lab, "ergebnis", 1))
    if c["fehlbetrag"] or (v and v["fehlbetrag"]):
        pas.append(row("Nicht gedeckter Fehlbetrag (Ausweis unter Aktiva F.)", *f("fehlbetrag", signed=True), 1))
    pas.append(r("Summe Eigenkapital", "ek", 1, False, True))
    pas += [row("B. Rückstellungen", *f("rueck"), 0, True),
            row("C. Verbindlichkeiten", eur(c["vll"] + c["vges"]), eur(v["vll"] + v["vges"]) if v else "", 0, True),
            r("gegenüber Gesellschaftern (Darlehen inkl. Zinsen)", "vges", 1),
            r("aus Lieferungen und Leistungen", "vll", 1),
            r("Summe Passiva", "passiva", 0, True, True)]
    note = ""
    if c["fehlbetrag"]:
        note = (f"Das Eigenkapital ist rechnerisch negativ ({eur(-c['fehlbetrag'])} EUR). Nach § 268 Abs. 3 HGB wird der "
                "Betrag, um den die Verluste das Eigenkapital übersteigen, auf der Aktivseite als „nicht durch Eigenkapital "
                "gedeckter Fehlbetrag“ ausgewiesen; das Eigenkapital steht dann mit 0 in der Summe.")
    return akt, pas, note


def guv_zeilen(g, kst, vj_ergebnis):
    def a(k):
        return num(g, k)
    ertr = a("sonstige_betriebliche_ertraege")
    aufw = a("sonstige_betriebliche_aufwendungen")
    zins = a("zinsaufwand")
    steuern = num(kst, "kst_festzusetzen") + num(kst, "gewst_festzusetzen")
    erg = ertr - aufw - zins - steuern
    gv = a("jahresueberschuss") - a("jahresfehlbetrag")
    has = vj_ergebnis is not None
    d = lambda x: "-" if has else ""
    z = []
    if ertr:
        z.append(row("Sonstige betriebliche Erträge", eur(ertr), d(0), 0))
    z.append(row("Sonstige betriebliche Aufwendungen", eur(-aufw), d(0), 0))
    if zins:
        z.append(row("Zinsen und ähnliche Aufwendungen", eur(-zins), d(0), 0))
    z.append(row("Steuern vom Einkommen und Ertrag", eur(-steuern), d(0), 0))
    z.append(row("Jahresüberschuss" if gv > 0 else "Jahresfehlbetrag", eur(gv), eur(vj_ergebnis) if has else "", 0, True, True))
    return z, erg, gv


# ---------- Journal-Check ----------
def journal_salden(journal):
    s = {}
    for r in journal:
        b = float(r["betrag"])
        s[r["soll"]] = s.get(r["soll"], 0) + b
        s[r["haben"]] = s.get(r["haben"], 0) - b
    return s


def konto_name(k):
    return SKR03.get(k, f"Konto {k}")


# ---------- Hauptteil ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ordner", type=Path, help="Arbeitsordner (enthält out/ und profil.md)")
    ap.add_argument("--jahr", type=int, help="Geschäftsjahr (sonst aus journal.csv)")
    args = ap.parse_args()
    root, out = args.ordner.resolve(), args.ordner.resolve() / "out"
    warnungen = []
    warn = warnungen.append

    erg = lese_yaml(out / "ergebnis.yaml")
    if not erg.get("bilanz") or not erg.get("guv"):
        sys.exit("out/ergebnis.yaml fehlt oder enthält kein bilanz/guv")
    salden = {r["konto"]: float(r["saldo"]) for r in lese_csv(out / "kontensalden.csv")}
    journal = lese_csv(out / "journal.csv")
    annahmen, fragen = lese_liste(out / "annahmen.md"), lese_liste(out / "fragen.md")
    pr = lese_profil(root / "profil.md", warn)

    jahr = args.jahr or (int(journal[0]["datum"][:4]) if journal else date.today().year - 1)
    stichtag, stichtag_vj = f"31.12.{jahr}", f"31.12.{jahr - 1}"

    # Vorjahr
    vj = vj_erg = vj_quelle = None
    vp = root / "vorjahr" / f"schlussbilanz_{jahr - 1}.yaml"
    if vp.exists():
        y = lese_yaml(vp)
        vj_erg = y.get("jahresergebnis")
        vb = y.get("bilanz") or bilanz_aus_salden(y.get("kontensalden") or {}, vj_erg)
        if vj_erg is None and y.get("guv"):
            vj_erg = num(y["guv"], "jahresueberschuss") - num(y["guv"], "jahresfehlbetrag")
        vj = bilanz_werte(vb)
        if abs(vj["aktiva"] - vj["passiva"]) > 0.01:
            warn(f"Vorjahresbilanz geht nicht auf (Aktiva {eur(vj['aktiva'])} / Passiva {eur(vj['passiva'])}); Vorjahresspalte weggelassen")
            vj = None
        vj_quelle = f"vorjahr/{vp.name}"
    else:
        warn(f"Keine Vorjahresbilanz ({vp.name}); Bericht ohne Vorjahresspalte")

    c = bilanz_werte(erg["bilanz"])
    akt, pas, fnote = bilanz_zeilen(c, vj)
    guv, guv_rechn, guv_ergebnis = guv_zeilen(erg["guv"], erg.get("kst"), vj_erg if vj else None)
    vj_erg_ok = vj_erg if vj else None

    # Checks
    checks = []
    def chk(ok, text):
        checks.append({"ok": bool(ok), "text": text})
    chk(abs(c["aktiva"] - c["passiva"]) < 0.01, f"Bilanz: Summe Aktiva {eur(c['aktiva'])} = Summe Passiva {eur(c['passiva'])} EUR.")
    bs = num(erg["bilanz"], "bilanzsumme")
    if bs:
        chk(abs(bs - c["aktiva"]) < 0.01, f"Bilanzsumme laut ergebnis.yaml ({eur(bs)}) stimmt mit der Bilanz überein.")
    chk(abs(guv_rechn - guv_ergebnis) < 0.01, f"GuV rechnet auf: Erträge - Aufwendungen - Zinsen - Steuern = {eur(guv_rechn)} EUR.")
    chk(abs(c["ergebnis"] - guv_ergebnis) < 0.01, "Jahresergebnis in Bilanz und GuV ist identisch.")
    if erg.get("kst") and "gk_z11_jahresergebnis" in erg["kst"]:
        chk(abs(round(guv_ergebnis) - num(erg["kst"], "gk_z11_jahresergebnis")) <= 1,
            f"Steuerliche Ausgangsgröße ({eur0(num(erg['kst'], 'gk_z11_jahresergebnis'))} EUR) entspricht dem Handelsergebnis.")
    if journal and salden:
        js = journal_salden(journal)
        abw = [k for k in salden if abs(abs(js.get(k, 0)) - salden[k]) > 0.01]
        chk(not abw, "Saldenliste stimmt mit dem Buchungsjournal überein" + (f" (Abweichung bei Konten: {', '.join(abw)})." if abw else "."))
    if vj:
        chk(True, f"Vorjahresbilanz {stichtag_vj} geht auf (Summe {eur(vj['aktiva'])} EUR).")
    for w in warnungen:
        chk(False, "Hinweis zu den Eingaben: " + w)

    # Zusammenfassung (3 Sätze)
    erg_w = "Jahresüberschuss" if guv_ergebnis > 0 else "Jahresfehlbetrag"
    s1 = f"{pr['firma']} schließt {jahr} mit einem {erg_w} von {eur(abs(guv_ergebnis))} EUR ab"
    if vj_erg_ok is not None:
        s1 += f" (Vorjahr: {eur(abs(vj_erg_ok))} EUR {'Überschuss' if vj_erg_ok > 0 else 'Fehlbetrag'})"
    exp = sorted(((k, v) for k, v in salden.items() if k[0] in "24" and k not in ("2114",)), key=lambda kv: -kv[1])[:3]
    teile = [f"{konto_name(k)} ({eur(v)} EUR)" for k, v in exp]
    if num(erg["guv"], "zinsaufwand"):
        teile.append(f"Darlehenszinsen ({eur(num(erg['guv'], 'zinsaufwand'))} EUR)")
    s1 += ("; die größten Kostenblöcke sind " + ", ".join(teile) + ".") if teile else "."
    s2 = f"Die Bilanzsumme zum {stichtag} beträgt {eur(c['aktiva'])} EUR"
    if c["fehlbetrag"]:
        s2 += (f"; weil die Verbindlichkeiten das Vermögen übersteigen, weist die Bilanz einen nicht durch Eigenkapital gedeckten "
               f"Fehlbetrag von {eur(c['fehlbetrag'])} EUR aus.")
    else:
        s2 += f" und das Eigenkapital {eur(c['ek'])} EUR."
    k = erg.get("kst") or {}
    s3 = (f"Steuerlich fallen {eur0(num(k, 'kst_festzusetzen'))} EUR Körperschaftsteuer und {eur0(num(k, 'gewst_festzusetzen'))} EUR "
          f"Gewerbesteuer an")
    if num(k, "verlustvortrag_neu"):
        s3 += f"; der steuerliche Verlustvortrag steigt auf {eur0(num(k, 'verlustvortrag_neu'))} EUR."
    else:
        s3 += "."
    summary = [s1, s2, s3]

    # Steuer
    lab = {
        "gk_z11_jahresergebnis": ("Jahresergebnis laut Handelsbilanz (Ausgangswert, Anlage GK Zeile 11)", "Mit Vorzeichen; Verlust negativ."),
        "steuerfrei_8b2": ("Steuerfreie Beteiligungserträge (§ 8b Abs. 2 KStG)", "Gewinne aus Anteilsverkäufen sind zu 95 % steuerfrei."),
        "hinzurechnung_8b3": ("Hinzurechnung nicht abziehbarer Ausgaben (§ 8b Abs. 3 KStG)", "5 % der steuerfreien Erträge gelten als nicht abziehbar."),
        "einkommen": ("Einkommen", "Ergebnis nach steuerlichen Korrekturen."),
        "zve": ("Zu versteuerndes Einkommen", "Nie negativ; ein Verlust erhöht stattdessen den Verlustvortrag."),
        "verlustvortrag_vorjahr": ("Körperschaftsteuerlicher Verlustvortrag aus dem Vorjahr", "Laut Feststellungsbescheid des Vorjahres."),
        "verlustvortrag_neu": ("Körperschaftsteuerlicher Verlustvortrag zum Jahresende (neu)", "Mindert künftige Gewinne steuerlich."),
        "gewerbeverlust_neu": ("Gewerbeverlust zum Jahresende (neu)", "Entsprechend für die Gewerbesteuer."),
        "kst_festzusetzen": ("Festzusetzende Körperschaftsteuer", ""),
        "gewst_festzusetzen": ("Festzusetzende Gewerbesteuer", ""),
        "einlagekonto_bestand": ("Steuerliches Einlagekonto (Bestand)", "Nur echte Einlagen; Gesellschafterdarlehen zählen nicht."),
    }
    keys = [x for x in lab if x in k or x in ("kst_festzusetzen", "gewst_festzusetzen")] + [x for x in k if x not in lab]
    steuer = [{"label": lab.get(key, (key, ""))[0], "wert": eur0(num(k, key)), "hinweis": lab.get(key, (key, ""))[1]}
              for key in keys]
    steuer_intro = ("Die Steuerberechnung folgt dem Handelsergebnis. Unten siehst du, wie daraus Körperschaftsteuer (KSt) "
                    "und Gewerbesteuer (GewSt) werden. Vollständig in Euro.")

    # Checkliste
    cl = [
        ("Stammdaten stimmen", f"Firma, Sitz, Registernummer und Stichtag {stichtag} auf Seite 1 und im Beschluss sind korrekt."),
        ("Kontostand", f"Der Bankbestand zum {stichtag} ({eur(c['bank'])} EUR) entspricht dem Saldo auf deinem Kontoauszug / in der Banking-App."),
    ]
    if vj:
        cl.append(("Anfangsbestände", f"Die Vorjahreswerte (Bilanzsumme {eur(vj['aktiva'])} EUR) sind die Zahlen der Schlussbilanz {jahr - 1}, wie vom Steuerberater bzw. aus dem Vorjahr übernommen."))
    if c["beteiligungen"]:
        cl.append(("Beteiligungen", f"Anschaffungskosten ({eur(c['beteiligungen'])} EUR) stimmen mit Kaufverträgen/Überweisungen überein; keine Hinweise auf dauerhaft gesunkenen Wert."))
    if c["vges"]:
        cl.append(("Gesellschafterdarlehen", f"Darlehenssumme und aufgelaufene Zinsen (zusammen {eur(c['vges'])} EUR) entsprechen deinen Verträgen und tatsächlichen Überweisungen."))
    if c["rueck"] or c["vll"]:
        cl.append(("Rückstellungen und offene Rechnungen", f"Rückstellungen ({eur(c['rueck'])} EUR) und offene Rechnungen zum Stichtag ({eur(c['vll'])} EUR) sind vollständig und plausibel."))
    cl += [
        ("Vollständigkeit", "Es gab im Jahr keine weiteren Konten, Depots, Einnahmen, Ausgaben, Kredite oder Verträge, die hier fehlen."),
        ("Annahmen", f"Du hast alle {len(annahmen)} Annahmen in Abschnitt 6 gelesen und bestätigt oder korrigiert."),
        ("Offene Fragen", f"Alle {len(fragen)} Fragen in Abschnitt 7 sind beantwortet."),
        ("Steuer", "Verlustvortrag und Einlagekonto am Jahresanfang entsprechen den letzten Bescheiden des Finanzamts."),
    ]
    if c["fehlbetrag"]:
        cl.append(("Überschuldung",
                   "Die Bilanz zeigt einen nicht gedeckten Fehlbetrag. Prüfe (ggf. mit Steuerberater/Anwalt), ob Rangrücktritt für die "
                   "Gesellschafterdarlehen vorliegt und die Fortführung gesichert ist (§ 19 InsO), und ob die Pflicht zur Einberufung "
                   "der Gesellschafterversammlung nach § 49 Abs. 3 GmbHG besteht (Verlust in Höhe der Hälfte des Stammkapitals)."))
    cl.append(("Freigabe", "Erst nach diesen Punkten den Feststellungsbeschluss unterschreiben."))
    checkliste = [{"punkt": p, "hinweis": h} for p, h in cl]

    saldenliste = [[kk, konto_name(kk), eur(v)] for kk, v in sorted(salden.items(), key=lambda kv: int(kv[0]))]
    jr = [[r["datum"][8:10] + "." + r["datum"][5:7] + "." + r["datum"][:4], r["soll"], r["haben"], eur(float(r["betrag"])), r["text"], r["beleg"]] for r in journal]

    report = dict(
        firma=pr["firma"], jahr=jahr, stichtag=stichtag, stichtag_vj=stichtag_vj, erstellt=dt(date.today()),
        summary=summary, has_vj=bool(vj), vj_quelle=vj_quelle or "", aktiva=akt, passiva=pas, fehlbetrag_note=fnote,
        guv=guv, steuer=steuer, steuer_intro=steuer_intro, checks=checks, annahmen=annahmen, fragen=fragen,
        checkliste=checkliste, saldenliste=saldenliste, journal=jr,
        ueberschuldung=bool(c["fehlbetrag"]), eigenkapital_text=eur(-c["fehlbetrag"]),
        guv_vj_note=("Vorjahr: Es liegt nur das Jahresergebnis vor, keine Aufgliederung der GuV." if vj else ""),
    )

    # Beschluss
    ug = bool(re.search(r"\bUG\b|haftungsbeschr", pr["firma"]))
    vv = c["vortrag"] * -1  # positiver Verlustvortrag Beginn
    verwend = []
    if guv_ergebnis <= 0:
        fb = -guv_ergebnis
        verwend.append(f"Der Jahresfehlbetrag des Geschäftsjahres {jahr} in Höhe von {eur(fb)} EUR wird auf neue Rechnung vorgetragen. "
                       f"Zusammen mit dem Verlustvortrag aus dem Vorjahr von {eur(vv)} EUR beträgt der Verlustvortrag damit {eur(vv + fb)} EUR.")
        verwend.append("Eine Gewinnausschüttung findet nicht statt.")
    else:
        net = guv_ergebnis - vv
        if net <= 0:
            verwend.append(f"Der Jahresüberschuss von {eur(guv_ergebnis)} EUR wird mit dem Verlustvortrag von {eur(vv)} EUR verrechnet. "
                           f"Der verbleibende Verlustvortrag von {eur(-net)} EUR wird auf neue Rechnung vorgetragen.")
        else:
            rest = net
            t = (f"Der Jahresüberschuss von {eur(guv_ergebnis)} EUR wird zunächst mit dem Verlustvortrag von {eur(vv)} EUR verrechnet "
                 f"(verbleibend {eur(net)} EUR). ")
            if ug:
                rl = round(net * 0.25 + 1e-9, 2)
                rest = net - rl
                t += (f"Gemäß § 5a Abs. 3 GmbHG werden {eur(rl)} EUR (ein Viertel) in die gesetzliche Rücklage eingestellt. ")
            t += f"Der Rest von {eur(rest)} EUR wird auf neue Rechnung vorgetragen."
            verwend.append(t)
        verwend.append("Eine Gewinnausschüttung findet nicht statt.")

    frist_est = f"30.11.{jahr + 1}"
    hinweise = [
        "Rechtsgrundlagen: § 46 Nr. 1 GmbHG weist Feststellung des Jahresabschlusses und Ergebnisverwendung der Gesellschafterversammlung zu; "
        "die Geschäftsführung stellt auf, stellt aber nicht fest (außer der Gesellschaftsvertrag sieht es vor).",
        "§ 48 Abs. 3 GmbHG: Hält ein Gesellschafter alle Anteile, muss er unverzüglich nach der Beschlussfassung eine Niederschrift aufnehmen und "
        "unterschreiben. Das gilt auch, wenn er zugleich Geschäftsführer ist. Eine Versammlung ist nicht nötig. Ohne unterschriebene Niederschrift ist der Beschluss kaum nachweisbar.",
        f"Frist: Nach § 42a Abs. 2 GmbHG ist bei kleinen Gesellschaften (§ 267 Abs. 1 HGB, dazu zählen Kleinstkapitalgesellschaften) bis zum Ablauf der ersten elf Monate des "
        f"Folgejahres zu beschließen, hier also bis {frist_est} (bei größeren: acht Monate).",
        "Bitte im Entwurf ergänzen: Datum und Ort der Unterschrift. Das Datum ist der Tag, an dem du den Beschluss tatsächlich fasst und unterschreibst. "
        "Original bei den Geschäftsunterlagen aufbewahren, eine Kopie kommt zur Bilanz-Ablage.",
        f"Hinterlegung: Die Bilanz ist nach § 326 Abs. 2 HGB zu hinterlegen; Frist nach § 325 Abs. 1 HGB: zwölf Monate nach dem Stichtag (hier {('31.12.' + str(jahr + 1))}). "
        "Den aktuellen Weg und die Anforderungen (Erklärung zur Größenklasse) recherchiert Claude vor dem Einreichen neu.",
        "Optional (hier bewusst nicht enthalten): Entlastung des Geschäftsführers (§ 46 Nr. 5 GmbHG). Bei einer Ein-Personen-Gesellschaft ohne praktische Wirkung; auf Wunsch als Ziffer ergänzen.",
        "Der Entwurf geht davon aus, dass Haftungsverhältnisse (§ 251 HGB) und Vorschüsse/Kredite an Organmitglieder nicht bestehen. Falls doch, müssen sie unter der Bilanz angegeben werden.",
        "Quellen zum Nachlesen: gesetze-im-internet.de/gmbhg/__46.html, /__48.html, /__42a.html, /__5a.html sowie /hgb/__267a.html und /hgb/__326.html. Das ist ein Entwurf, keine Rechtsberatung.",
    ]
    if c["fehlbetrag"]:
        hinweise.insert(3, f"Der Jahresabschluss weist einen nicht durch Eigenkapital gedeckten Fehlbetrag aus. Prüfe vor dem Unterschreiben: Rangrücktritt der Gesellschafterdarlehen, "
                           f"Fortbestehensprognose (§ 19 InsO) und Einberufungspflicht bei Verlust in Höhe des halben Stammkapitals (§ 49 Abs. 3 GmbHG). Bei Zweifeln Rechtsrat einholen.")
    beschluss = dict(
        firma=pr["firma"], jahr=jahr, stichtag=stichtag, stichtag_vj=stichtag_vj, beginn=f"01.01.{jahr}",
        sitz=pr["sitz"], sitz_kurz=pr["sitz_kurz"] or PLATZHALTER, register=pr["register"], stammkapital=pr["stammkapital"],
        gesellschafter=pr["gesellschafter"], gf_gleich=pr["gf_gleich"], bilanzsumme=eur(c["aktiva"]),
        ergebnis_wort=erg_w, ergebnis_betrag=eur(abs(guv_ergebnis)), verwendung=verwend,
        frist_offenlegung=f"31.12.{jahr + 1}", has_vj=bool(vj), aktiva=akt, passiva=pas, fehlbetrag_note=fnote, guv=guv,
        angaben_unter_bilanz="Haftungsverhältnisse und Vorschüsse/Kredite an Organmitglieder bestehen nicht (vom Gesellschafter zu bestätigen).",
        hinweise=hinweise,
    )

    # Kompilieren
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for f in (HERE / "templates").glob("*.typ"):
            shutil.copy(f, tmp / f.name)
        for name, data, pdf in (("report", report, "pruefbericht.pdf"), ("beschluss", beschluss, "beschluss_feststellung.pdf")):
            (tmp / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            typst.compile(str(tmp / f"{name}.typ"), output=str(out / pdf), root=str(tmp))
            print(out / pdf)
    for w in warnungen:
        print("WARNUNG:", w, file=sys.stderr)
    if any(not x["ok"] for x in checks):
        print("ACHTUNG: Plausibilitätsprüfung mit Abweichungen, siehe Abschnitt 5 im Prüfbericht.", file=sys.stderr)


if __name__ == "__main__":
    main()
