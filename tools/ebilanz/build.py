#!/usr/bin/env python3
"""E-Bilanz (§ 5b EStG) als XBRL-Instanz aus den Ergebnisdateien des Skills ug-abschluss.

Eingaben:  <lauf>/kontensalden.csv, <lauf>/journal.csv, <lauf>/ergebnis.yaml (Format: Skill ug-abschluss),
           Mapping-Datei(en) Konto -> Taxonomie-Position, Stammdaten-YAML, entpackte HGB-Taxonomie.
Ausgabe:   XBRL-Instanz (Kerntaxonomie, steuerlich, Einzelabschluss, GKV, Einheitsbilanz) mit
           Bilanz, GuV, Anlagenspiegel (brutto), Kontennachweis und NIL für leere Mussfelder.

Was der Code exakt macht (und deshalb Code ist): Vorzeichen aus Soll/Haben, Summen über die
Rechenregeln (calculation linkbase) der Taxonomie, nicht gedeckter Fehlbetrag (§ 268 Abs. 3 HGB),
Mussfeld-Liste aus den Taxonomie-Referenzen (fiscalRequirement, Rechtsform), Abgleich mit ergebnis.yaml.
Nicht abgedeckt: siehe README.md.
"""
from __future__ import annotations

import argparse
import csv
import re
import datetime as dt
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import yaml
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import taxonomie  # noqa: E402

CENT = Decimal("0.01")
ROLE = "http://www.xbrl.de/taxonomies/de-gaap-ci/role/"
ROLE_ANLAGENSPIEGEL = ROLE + "notesTableStatementOfChangesInFixedAssetsGross"
NS = {
    "xbrli": "http://www.xbrl.org/2003/instance",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xlink": "http://www.w3.org/1999/xlink",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xbrldi": "http://xbrl.org/2006/xbrldi",
    "iso4217": "http://www.xbrl.org/2003/iso4217",
}
# Gesamtkostenverfahren, Handels-/Einheitsbilanz einer Kapitalgesellschaft
ERLAUBTE_ERGEBNISART = {"", "neutral", "GKV"}
AUSGESCHLOSSEN = {"steuerlich", "handelsrechtlich", "Einreichung an Finanzverwaltung"}
MUSS = {"Mussfeld", "Summenmussfeld", "Mussfeld, Kontennachweis erwünscht"}


def fehler(msg: str) -> None:
    raise SystemExit("FEHLER: " + msg)


def d2(x) -> Decimal:
    return Decimal(str(x)).quantize(CENT)


# ---------------------------------------------------------------- Eingaben


def lade_mapping(pfade: list[Path]) -> tuple[dict, list, list]:
    exakt, bereiche, ohne = {}, [], []
    for p in pfade:
        m = yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}
        for k in m.get("ohne_position", []):
            a, _, b = str(k).partition("-")
            ohne.append((int(a), int(b or a)))
        for k, v in (m.get("konten") or {}).items():
            a, _, b = str(k).partition("-")
            if b:
                bereiche.insert(0, (int(a), int(b), v))  # spätere Datei zuerst prüfen
            else:
                exakt[int(a)] = v
    return exakt, bereiche, ohne


def finde(konto: int, exakt, bereiche):
    if konto in exakt:
        return exakt[konto]
    for a, b, v in bereiche:
        if a <= konto <= b:
            return v
    return None


def salden(lauf: Path, ohne) -> tuple[dict[int, Decimal], dict]:
    """Vorzeichenbehaftete Salden (Soll positiv) aus journal.csv, abgeglichen mit kontensalden.csv."""
    soll_minus_haben: dict[int, Decimal] = defaultdict(Decimal)
    bewegungen: dict[int, list] = defaultdict(list)
    ist_ohne = lambda k: any(a <= k <= b for a, b in ohne)  # noqa: E731
    with open(lauf / "journal.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            s, h, betrag = int(r["soll"]), int(r["haben"]), d2(r["betrag"])
            soll_minus_haben[s] += betrag
            soll_minus_haben[h] -= betrag
            bewegungen[s].append(("S", betrag, h))
            bewegungen[h].append(("H", betrag, s))
    with open(lauf / "kontensalden.csv", encoding="utf-8") as f:
        liste = {int(r["konto"]): d2(r["saldo"]) for r in csv.DictReader(f)}
    for k, v in soll_minus_haben.items():
        if ist_ohne(k):
            if v != 0:
                fehler(f"Konto {k} (ohne Position) hat Saldo {v} – Eröffnung/Abschluss unvollständig")
            continue
        if abs(v) != liste.get(k, Decimal(0)):
            fehler(f"Konto {k}: Journal ergibt {v}, kontensalden.csv {liste.get(k)}")
    for k in liste:
        if k not in soll_minus_haben and liste[k] != 0:
            fehler(f"Konto {k} steht in kontensalden.csv, aber nicht im Journal")
    return {k: v for k, v in soll_minus_haben.items() if v != 0 and not ist_ohne(k)}, bewegungen


# ---------------------------------------------------------------- Taxonomie


class Tax:
    def __init__(self, tax_dir: Path):
        from arelle import Cntlr, XbrlConst

        self.X = XbrlConst
        self.datum = taxonomie.datum(tax_dir)
        root = taxonomie.wurzel(tax_dir)
        self.ns_gaap = f"http://www.xbrl.de/taxonomies/de-gaap-ci-{self.datum}"
        self.ns_gcd = f"http://www.xbrl.de/taxonomies/de-gcd-{self.datum}"
        c = Cntlr.Cntlr(logFileName="logToBuffer")
        self.m = c.modelManager.load(str(root / f"de-gaap-ci-{self.datum}/de-gaap-ci-{self.datum}-shell-fiscal.xsd"))
        self.c = {k.qname.localName: k for k in self.m.qnameConcepts.values() if k.qname.namespaceURI == self.ns_gaap}
        self._ref = {}
        gcd_xsd = (root / f"de-gcd-{self.datum}/de-gcd-{self.datum}.xsd").read_text(encoding="utf-8")
        self.gcd_namen = set(re.findall(r'<xs:element[^>]*\sname="([^"]+)"', gcd_xsd))

    def konzept(self, name):
        if name not in self.c:
            fehler(f"Position {name} gibt es in Taxonomie {self.datum} nicht")
        return self.c[name]

    def ref(self, name) -> dict:
        if name not in self._ref:
            out: dict = {}
            for r in self.m.relationshipSet(self.X.conceptReference).fromModelObject(self.c[name]):
                for e in r.toModelObject.iterchildren():
                    out.setdefault(e.localName, []).append((e.text or "").strip())
            self._ref[name] = out
        return self._ref[name]

    def mussfeld_kapg(self, name) -> bool:
        r = self.ref(name)
        return (
            r.get("fiscalRequirement", [""])[0] in MUSS
            and "true" in r.get("legalFormKSt", [])
            and not AUSGESCHLOSSEN & set(r.get("notPermittedFor", []))
            and set(r.get("typeOperatingResult", [""])) <= ERLAUBTE_ERGEBNISART
        )

    def summiere(self, rolle: str, werte: dict[str, Decimal]) -> dict[str, Decimal]:
        """Rollup über summation-item-Arcs der Rolle: Oberpositionen = gewichtete Summe der Kinder."""
        rs = self.m.relationshipSet(self.X.summationItem, ROLE + rolle)
        alle = set()
        offen = list(werte)
        while offen:
            n = offen.pop()
            for rel in rs.toModelObject(self.c[n]):
                p = rel.fromModelObject.qname.localName
                if p not in alle:
                    alle.add(p)
                    offen.append(p)
        erg = dict(werte)

        def wert(n):
            if n in erg:
                return erg[n]
            s = Decimal(0)
            for rel in rs.fromModelObject(self.c[n]):
                k = rel.toModelObject.qname.localName
                if k in erg or k in alle:
                    s += Decimal(str(rel.weight)) * wert(k)
            erg[n] = s
            return s

        for n in alle:
            if n in werte:
                kinder = [r.toModelObject.qname.localName for r in rs.fromModelObject(self.c[n])]
                if any(k in werte or k in alle for k in kinder):
                    fehler(f"{n} hat eigenen Wert und Unterpositionen mit Werten – Mapping auf Blattebene legen")
            wert(n)
        return erg

    def praesentation(self, rolle: str) -> list[str]:
        rs = self.m.relationshipSet(self.X.parentChild, ROLE + rolle)
        out, gesehen = [], set()

        def lauf(k):
            n = k.qname.localName
            if n in gesehen:
                return
            gesehen.add(n)
            if k.qname.namespaceURI == self.ns_gaap and not k.isAbstract:
                out.append(n)
            for rel in rs.fromModelObject(k):
                lauf(rel.toModelObject)

        for r in rs.rootConcepts:
            lauf(r)
        return out

    def anlagenspiegel(self):
        """(Dimension, Domänen-Hierarchie Kind->Eltern, Primärelemente) des Brutto-Anlagenspiegels."""
        rs = self.m.relationshipSet("XBRL-dimensions", ROLE_ANLAGENSPIEGEL)
        eltern, prim = {}, []
        for rel in rs.modelRelationships:
            a = rel.arcrole.rsplit("/", 1)[-1]
            f, t = rel.fromModelObject.qname.localName, rel.toModelObject.qname.localName
            if a == "domain-member" and f.startswith("bs.ass.fixAss"):
                eltern[t] = f
            elif a == "domain-member" and not t.startswith(("bs.", "dim_")):
                prim.append(t)
        return eltern, prim


# ---------------------------------------------------------------- Instanz


class Instanz:
    def __init__(self, tax: Tax, st13: str, beginn, ende):
        self.t = tax
        self.gaap, self.gcd = tax.ns_gaap, tax.ns_gcd
        nsmap = dict(NS, **{"de-gaap-ci": self.gaap, "de-gcd": self.gcd})
        self.root = etree.Element(f"{{{NS['xbrli']}}}xbrl", nsmap=nsmap)
        d = tax.datum
        for href in (
            f"http://www.xbrl.de/taxonomies/de-gcd-{d}/de-gcd-{d}-shell.xsd",
            f"http://www.xbrl.de/taxonomies/de-gaap-ci-{d}/de-gaap-ci-{d}-shell-fiscal.xsd",
        ):
            etree.SubElement(self.root, f"{{{NS['link']}}}schemaRef",
                             {f"{{{NS['xlink']}}}type": "simple", f"{{{NS['xlink']}}}href": href})
        self.st13, self.beginn, self.ende = st13, beginn, ende
        self.kontext("I", instant=ende)
        self.kontext("D", start=beginn, end=ende)
        u = etree.SubElement(self.root, f"{{{NS['xbrli']}}}unit", id="EUR")
        etree.SubElement(u, f"{{{NS['xbrli']}}}measure").text = "iso4217:EUR"
        self.gefuellt: set[tuple] = set()

    def kontext(self, cid, instant=None, start=None, end=None, member=None):
        x = NS["xbrli"]
        c = etree.Element(f"{{{x}}}context", id=cid)
        e = etree.SubElement(c, f"{{{x}}}entity")
        etree.SubElement(e, f"{{{x}}}identifier", scheme="http://www.rzf-nrw.de/Steuernummer").text = self.st13
        p = etree.SubElement(c, f"{{{x}}}period")
        if instant:
            etree.SubElement(p, f"{{{x}}}instant").text = str(instant)
        else:
            etree.SubElement(p, f"{{{x}}}startDate").text = str(start)
            etree.SubElement(p, f"{{{x}}}endDate").text = str(end)
        if member:
            s = etree.SubElement(c, f"{{{x}}}scenario")
            for dim, mem in member:
                etree.SubElement(s, f"{{{NS['xbrldi']}}}explicitMember", dimension=dim).text = mem
        # Kontexte/Units vor die Fakten
        idx = len([k for k in self.root if k.tag in (f"{{{NS['link']}}}schemaRef", f"{{{x}}}context")])
        self.root.insert(idx, c)

    def fakt(self, ns, name, wert=None, ctx="D", parent=None, monetaer=False):
        el = etree.SubElement(self.root if parent is None else parent, f"{{{ns}}}{name}", contextRef=ctx)
        if monetaer:
            el.set("unitRef", "EUR")
        if wert is None:
            el.set(f"{{{NS['xsi']}}}nil", "true")
        else:
            if monetaer:
                el.set("decimals", "2")
                wert = f"{d2(wert):.2f}"
            el.text = str(wert)
        self.gefuellt.add((name, ctx))
        return el

    def tupel(self, ns, name, parent=None):
        return etree.SubElement(self.root if parent is None else parent, f"{{{ns}}}{name}")

    def gaap_wert(self, name, wert):
        k = self.t.c[name]
        ctx = "I" if k.periodType == "instant" else "D"
        if (name, ctx) not in self.gefuellt:
            self.fakt(self.gaap, name, wert, ctx, monetaer=True)


def gcd_teil(x: Instanz, st: dict, jahr: dict, berichtsteile: dict, status: str):
    g = x.gcd
    namen = x.t.gcd_namen

    def F(n, v=None, p=None):
        if n not in namen:
            fehler(f"Stammdaten-Feld {n} gibt es in Taxonomie {x.t.datum} nicht")
        return x.fakt(g, n, v, "D", p)

    T = lambda n, p=None: x.tupel(g, n, p)  # noqa: E731
    F("genInfo.doc.id.generationDate", dt.date.today().isoformat())
    t = T("genInfo.report.id.reportStatus")
    F("genInfo.report.id.reportStatus.reportStatus." + status, {"E": "endgültig", "V": "vorläufig"}[status], t)
    t = T("genInfo.report.id.revisionStatus")
    F("genInfo.report.id.revisionStatus.revisionStatus.E", "erstmalig", t)
    t = T("genInfo.report.id.reportElement")
    for k, text in berichtsteile.items():
        F("genInfo.report.id.reportElement.reportElements." + k, text, t)
    if "genInfo.report.id.reportElement.reportElements.transmissionNotYetPossible" in namen:  # ab 6.9
        F("genInfo.report.id.reportElement.reportElements.transmissionNotYetPossible")
    t = T("genInfo.report.id.statementType")
    F("genInfo.report.id.statementType.statementType.E", "Jahresabschluss", t)
    F("genInfo.report.id.incomeStatementendswithBalProfit", "false")
    t = T("genInfo.report.id.accountingStandard")
    F("genInfo.report.id.accountingStandard.accountingStandard.HAOE", "deutsches Handelsrecht (sog. Einheitsbilanz)", t)
    t = T("genInfo.report.id.specialAccountingStandard")
    F("genInfo.report.id.specialAccountingStandard.K", "Kerntaxonomie", t)
    t = T("genInfo.report.id.incomeStatementFormat")
    F("genInfo.report.id.incomeStatementFormat.incomeStatementFormat.GKV", "Gesamtkostenverfahren", t)
    t = T("genInfo.report.id.consolidationRange")
    F("genInfo.report.id.consolidationRange.consolidationRange.EA", "nicht konsolidiert/ Einzelabschluss", t)
    t = T("genInfo.report.id.accordingTo")
    F("genInfo.report.id.accordingTo.name", None, t)
    t2 = T("genInfo.report.id.accordingTo.idNo", t)
    F("genInfo.company.id.idNo.type.companyId.ST13", None, t2)
    F("genInfo.company.id.idNo.type.companyId.STWID", None, t2)
    F("genInfo.company.id.idNo.type.companyId.BF4", None, t2)
    F("genInfo.report.id.accordingTo.yearEnd", None, t)
    for k in ("fiscalYearBegin", "fiscalYearEnd", "balSheetClosingDate", "fiscalPreviousYearBegin",
              "fiscalPreviousYearEnd", "balSheetClosingDatePreviousYear"):
        F("genInfo.report.period." + k, jahr[k].isoformat())
    F("genInfo.company.id.name", st["firma"])
    t = T("genInfo.company.id.legalStatus")
    F("genInfo.company.id.legalStatus.legalStatus." + st["rechtsform"], st.get("rechtsform_text", st["rechtsform"]), t)
    F("genInfo.company.id.location", "Firmensitz")
    F("genInfo.company.id.location.street", st["strasse"])
    F("genInfo.company.id.location.houseNo", str(st["hausnummer"]))
    F("genInfo.company.id.location.zipCode", str(st["plz"]))
    F("genInfo.company.id.location.city", st["ort"])
    F("genInfo.company.id.location.country", st["land"])
    t = T("genInfo.company.id.idNo")
    F("genInfo.company.id.idNo.type.companyId.ST13", str(st["steuernummer_elster"]), t)
    F("genInfo.company.id.idNo.type.companyId.STID", None, t)
    F("genInfo.company.id.idNo.type.companyId.STWID", None, t)
    F("genInfo.company.id.idNo.type.companyId.BF4", str(st["bundesfinanzamtsnummer"]), t)
    F("genInfo.company.id.business", st.get("geschaeftstaetigkeit"))
    t = T("genInfo.company.id.incomeClassification")
    F("genInfo.company.id.incomeClassification." + st.get("einkunftsart", "trade"), None, t).attrib.pop(
        f"{{{NS['xsi']}}}nil")
    t = T("genInfo.company.id.entityWithTaxablePurposeBusiness")
    F("genInfo.company.id.entityWithTaxablePurposeBusiness.normal", None, t)
    t = T("genInfo.company.id.domesticBranchOfForeignCompany")
    F("genInfo.company.id.domesticBranchOfForeignCompany.other", None, t)
    t = T("genInfo.company.id.shareholder")
    for n in ("name", "id", "taxnumber", "taxid", "WID"):
        F("genInfo.company.id.shareholder." + n, None, t)
    t2 = T("genInfo.company.id.shareholder.legalStatus", t)
    F("genInfo.company.id.shareholder.legalStatus.legalStatus.NPP", None, t2)
    t2 = T("genInfo.company.id.shareholder.ShareDivideKey", t)
    F("genInfo.company.id.shareholder.ShareDivideKey.numerator", None, t2)
    F("genInfo.company.id.shareholder.ShareDivideKey.denominator", None, t2)


# ---------------------------------------------------------------- Ablauf


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lauf", required=True, type=Path, help="Ordner mit kontensalden.csv, journal.csv, ergebnis.yaml")
    ap.add_argument("--taxonomie", required=True, type=Path, help="entpackte HGB-Taxonomie (esteuer.de)")
    ap.add_argument("--mapping", required=True, type=Path, nargs="+", help="Mapping-Dateien, spätere gewinnen")
    ap.add_argument("--stammdaten", required=True, type=Path)
    ap.add_argument("--jahr", required=True, type=int)
    ap.add_argument("--status", choices=["E", "V"], default="E", help="E endgültig, V vorläufig")
    ap.add_argument("--eroeffnung", default="9000-9009", help="Gegenkonten der Eröffnungsbuchungen")
    ap.add_argument("--aus", required=True, type=Path)
    a = ap.parse_args(argv)

    st = yaml.safe_load(a.stammdaten.read_text(encoding="utf-8"))
    ergebnis = yaml.safe_load((a.lauf / "ergebnis.yaml").read_text(encoding="utf-8"))
    if st.get("wirtschaftsjahr", "kalenderjahr") != "kalenderjahr":
        fehler("nur Wirtschaftsjahr = Kalenderjahr umgesetzt")
    gruendung = st.get("gruendung") or dt.date(1900, 1, 1)
    jahr = {
        "fiscalYearBegin": max(dt.date(a.jahr, 1, 1), gruendung),
        "fiscalYearEnd": dt.date(a.jahr, 12, 31),
        "balSheetClosingDate": dt.date(a.jahr, 12, 31),
        "fiscalPreviousYearBegin": max(dt.date(a.jahr - 1, 1, 1), gruendung),
        "fiscalPreviousYearEnd": dt.date(a.jahr - 1, 12, 31),
        "balSheetClosingDatePreviousYear": dt.date(a.jahr - 1, 12, 31),
    }

    tax = Tax(a.taxonomie)
    exakt, bereiche, ohne = lade_mapping(a.mapping)
    for v in list(exakt.values()) + [b[2] for b in bereiche]:
        tax.konzept(v["position"])
    s, bewegungen = salden(a.lauf, ohne)

    # 1. Konten -> Positionen (Vorzeichen: Soll positiv, gedreht für Haben-Positionen)
    werte: dict[str, Decimal] = defaultdict(Decimal)
    nachweis: list[tuple[str, int, str, Decimal]] = []
    for konto in sorted(s):
        m = finde(konto, exakt, bereiche)
        if not m:
            fehler(f"Konto {konto} (Saldo {s[konto]}) hat kein Mapping")
        pos = m["position"]
        k = tax.c[pos]
        if k.balance not in ("debit", "credit"):
            fehler(f"{pos} hat kein balance-Attribut")
        betrag = s[konto] if k.balance == "debit" else -s[konto]
        werte[pos] += betrag
        nachweis.append((pos, konto, m.get("name", ""), betrag))

    bs_pos = {p: v for p, v in werte.items() if p.startswith("bs.")}
    is_pos = {p: v for p, v in werte.items() if p.startswith("is.")}

    # 2. GuV-Summen, Jahresergebnis in die Bilanz
    guv = tax.summiere("incomeStatement", is_pos)
    ergebnis_jahr = guv.get("is.netIncome", Decimal(0))
    bs_pos["bs.eqLiab.equity.netIncome"] = ergebnis_jahr

    # 3. Negatives Eigenkapital: nicht durch EK gedeckter Fehlbetrag (§ 268 Abs. 3 HGB)
    ek = tax.summiere("balanceSheet", bs_pos).get("bs.eqLiab.equity", Decimal(0))
    if ek < 0:
        bs_pos["bs.eqLiab.equity.deficitNotCoveredByCapital"] = -ek
        bs_pos["bs.ass.deficitNotCoveredByCapital"] = -ek
    bil = tax.summiere("balanceSheet", bs_pos)

    # 4. Abgleich mit ergebnis.yaml
    aktiva, passiva = bil.get("bs.ass", 0), bil.get("bs.eqLiab", 0)
    pruef = [("Aktiva = Passiva", aktiva, passiva)]
    eb, eg = ergebnis.get("bilanz", {}), ergebnis.get("guv", {})
    if "bilanzsumme" in eb:
        pruef.append(("Bilanzsumme", aktiva, d2(eb["bilanzsumme"])))
    jf = d2(eg.get("jahresueberschuss", 0)) - d2(eg.get("jahresfehlbetrag", 0))
    pruef.append(("Jahresergebnis", ergebnis_jahr, jf))
    if "nicht_gedeckter_fehlbetrag" in eb:
        pruef.append(("nicht gedeckter Fehlbetrag", bil.get("bs.ass.deficitNotCoveredByCapital", 0),
                      d2(eb["nicht_gedeckter_fehlbetrag"])))
    for name, x1, x2 in pruef:
        if d2(x1) != d2(x2):
            fehler(f"Abgleich {name}: {x1} != {x2}")
        print(f"ok  {name}: {d2(x1)}")

    # 5. Anlagenspiegel (brutto) aus dem Journal: Anfangsbestand = Eröffnung, Zugänge = übrige Soll,
    #    Abgänge = Haben. Abschreibungen werden nicht unterstützt.
    ea, _, eb_ = a.eroeffnung.partition("-")
    ist_eb = lambda k: int(ea) <= k <= int(eb_ or ea)  # noqa: E731
    eltern, prim = tax.anlagenspiegel()
    spiegel: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for pos, konto, _, _ in nachweis:
        if not pos.startswith("bs.ass.fixAss"):
            continue
        anf = sum((b for sh, b, g in bewegungen[konto] if sh == "S" and ist_eb(g)), Decimal(0))
        zu = sum((b for sh, b, g in bewegungen[konto] if sh == "S" and not ist_eb(g)), Decimal(0))
        ab = sum((b for sh, b, g in bewegungen[konto] if sh == "H"), Decimal(0))
        if ab:
            fehler(f"Anlagekonto {konto} hat Haben-Buchungen (Abgang/Abschreibung) – im Prototyp nicht umgesetzt")
        if pos not in eltern:
            fehler(f"{pos} ist kein Element des Anlagenspiegels")
        m = pos
        while m:
            for k, v in (("grossCost.beginning", anf), ("gross.addition", zu), ("gross", anf + zu),
                         ("all", anf + zu), ("all_Prev_period", anf)):
                spiegel[m][k] += v
            m = eltern.get(m)

    # 6. Instanz schreiben
    x = Instanz(tax, str(st["steuernummer_elster"]), jahr["fiscalYearBegin"], jahr["fiscalYearEnd"])
    teile = {"B": "Bilanz", "GuV": "GuV", "KS": "Kontensalden zu einer oder mehreren Positionen"}
    if spiegel:
        teile["BAL"] = "Anlagenspiegel (brutto)"
    leer = ["BVV", "EB", "EV", "STU"] + ([] if spiegel else ["BAL"])
    gcd_teil(x, st, jahr, {**teile, **{k: None for k in leer}}, a.status)

    for p, v in sorted(bil.items()):
        x.gaap_wert(p, v)
    for p, v in sorted(guv.items()):
        x.gaap_wert(p, v)
    for rolle in ("balanceSheet", "incomeStatement"):
        for p in tax.praesentation(rolle):
            if tax.mussfeld_kapg(p):
                x.gaap_wert(p, None)

    muss_spiegel = [p for p in prim if tax.mussfeld_kapg(p)]
    for i, (member, w) in enumerate(sorted(spiegel.items())):
        cid = f"D-BAL-{i}"
        x.kontext(cid, start=jahr["fiscalYearBegin"], end=jahr["fiscalYearEnd"],
                  member=[("de-gaap-ci:dim_changes.nt.ass.gross", f"de-gaap-ci:{member}"),
                          ("de-gaap-ci:dim_taxTrans", "de-gaap-ci:dim_taxBal")])
        for k, v in w.items():
            x.fakt(x.gaap, k, v, cid, monetaer=True)
        for k in muss_spiegel:
            if k not in w:
                x.fakt(x.gaap, k, None, cid, monetaer=True)

    for pos, konto, name, betrag in nachweis:
        t = x.tupel(x.gaap, "detailedInformation.accountBalances")
        x.fakt(x.gaap, "detailedInformation.accountbalances.positionName", f"de-gaap-ci:{pos}", "D", t)
        x.fakt(x.gaap, "detailedInformation.accountbalances.accountNumber", str(konto), "D", t)
        x.fakt(x.gaap, "detailedInformation.accountbalances.accountDescription", name, "D", t)
        x.fakt(x.gaap, "detailedInformation.accountbalances.amount", betrag, "D", t, monetaer=True)

    a.aus.parent.mkdir(parents=True, exist_ok=True)
    etree.ElementTree(x.root).write(str(a.aus), xml_declaration=True, encoding="UTF-8", pretty_print=True)
    werte_n = sum(1 for e in x.root.iter() if e.get("contextRef") and e.get(f"{{{NS['xsi']}}}nil") is None)
    nil_n = sum(1 for e in x.root.iter() if e.get(f"{{{NS['xsi']}}}nil"))
    print(f"Taxonomie {tax.datum}: {werte_n} Fakten mit Wert, {nil_n} NIL, {len(nachweis)} Konten im Kontennachweis")
    print(f"-> {a.aus}")


if __name__ == "__main__":
    main()
