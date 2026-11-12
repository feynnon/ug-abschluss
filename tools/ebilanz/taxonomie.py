"""Hilfsfunktionen rund um die HGB-Taxonomie (XBRL Deutschland e.V. / esteuer.de).

Die Taxonomie selbst liegt NICHT im Repo (Copyright XBRL Deutschland e.V., keine freie Lizenz).
Sie wird von www.esteuer.de geladen, entpackt und hier als Verzeichnis übergeben.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

XBRL_DE = "http://www.xbrl.de/taxonomies/"


def wurzel(tax_dir: Path) -> Path:
    """Verzeichnis, das de-gcd-*/ und de-gaap-ci-*/ enthält (Zip-Strukturen unterscheiden sich je Version)."""
    tax_dir = Path(tax_dir)
    for p in [tax_dir, *tax_dir.rglob("*")]:
        if p.is_dir() and any(c.name.startswith("de-gcd-") for c in p.iterdir() if c.is_dir()):
            return p
    raise SystemExit(f"Keine Taxonomie (de-gcd-*/) unter {tax_dir} gefunden")


def datum(tax_dir: Path) -> str:
    """Taxonomie-Datum, z. B. '2025-04-01' (= Version 6.9)."""
    for c in wurzel(tax_dir).iterdir():
        m = re.fullmatch(r"de-gcd-(\d{4}-\d{2}-\d{2})", c.name)
        if m:
            return m.group(1)
    raise SystemExit("Taxonomie-Datum nicht erkennbar")


def paket(tax_dir: Path, ziel: Path) -> Path:
    """Baut ein Taxonomie-Paket (Zip mit META-INF/catalog.xml), damit Arelle die offiziellen
    http://www.xbrl.de/taxonomies/...-URLs aus der Instanz offline auf die lokalen Dateien abbildet."""
    root = wurzel(tax_dir)
    d = datum(tax_dir)
    ziel = Path(ziel)
    if ziel.exists():
        return ziel
    ziel.parent.mkdir(parents=True, exist_ok=True)
    tp = f"""<?xml version="1.0" encoding="UTF-8"?>
<tp:taxonomyPackage xmlns:tp="http://xbrl.org/2016/taxonomy-package" xml:lang="de">
  <tp:identifier>{XBRL_DE}{d}</tp:identifier>
  <tp:name>HGB-Taxonomie {d} (lokal gepackt)</tp:name>
  <tp:version>{d}</tp:version>
</tp:taxonomyPackage>"""
    cat = f"""<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
  <rewriteURI uriStartString="{XBRL_DE}" rewritePrefix="../"/>
</catalog>"""
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pkg/META-INF/taxonomyPackage.xml", tp)
        z.writestr("pkg/META-INF/catalog.xml", cat)
        for f in root.rglob("*"):
            if f.is_file() and f.parts[len(root.parts)].startswith("de-"):
                z.write(f, "pkg/" + str(f.relative_to(root)))
    return ziel
