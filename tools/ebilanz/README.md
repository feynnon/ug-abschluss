# E-Bilanz (Prototyp)

Erzeugt aus den Ergebnisdateien des Skills `ug-abschluss` (`kontensalden.csv`, `journal.csv`,
`ergebnis.yaml`) eine XBRL-Instanz nach § 5b EStG und prüft sie mit Arelle gegen die HGB-Taxonomie.
Gedacht für Kleinstkapitalgesellschaften (UG/GmbH) mit SKR03, Wirtschaftsjahr = Kalenderjahr.

## Was erzeugt wird
- GCD-Stammdaten aus einer YAML-Datei außerhalb des Repos (Beispiel-Felder: siehe `build.py`, `gcd_teil`).
- Bilanz und GuV (Kerntaxonomie, steuerlich, GKV, Einzelabschluss, „Einheitsbilanz“ = HB entspricht StB,
  daher keine Überleitungsrechnung). Oberpositionen werden aus den Rechenregeln der Taxonomie summiert,
  Vorzeichen aus Soll/Haben des Journals; negatives Eigenkapital → nicht gedeckter Fehlbetrag.
- Leere Mussfelder als NIL – ausgewählt aus den Taxonomie-Referenzen (Mussfeld/Summenmussfeld,
  zulässig für Körperschaften, GKV), also ohne fest verdrahtete Liste.
- Anlagenspiegel (brutto) aus dem Journal: Anfangsbestand, Zugänge, Endbestand.
- Unverdichteter Kontennachweis (Position, Kontonummer, Bezeichnung, Saldo) für jedes Konto mit Saldo –
  Pflicht für Wirtschaftsjahre ab 2025 (§ 5b Abs. 1 EStG i. d. F. JStG 2024).
- Abgleich mit `ergebnis.yaml` (Bilanzsumme, Jahresergebnis, Fehlbetrag); bei Abweichung Abbruch.

## Aufruf
Taxonomie (XBRL-Paket) von esteuer.de laden und entpacken – **nicht ins Repo**: Copyright XBRL Deutschland
e.V., ohne freie Lizenz. Welche Version für welches Wirtschaftsjahr gilt, steht im jeweiligen BMF-Schreiben
(jedes Jahr neu recherchieren). Abhängigkeiten: `pip install arelle-release pyyaml`.

```
python tools/ebilanz/build.py --lauf <out-Ordner> --jahr 2025 \
  --taxonomie <entpackte Taxonomie> \
  --mapping tools/ebilanz/mapping_skr03.yaml daten/ebilanz/mapping.yaml \
  --stammdaten daten/ebilanz/stammdaten.yaml --aus daten/ebilanz/2025/ebilanz.xbrl
python tools/ebilanz/validate.py --taxonomie <entpackte Taxonomie> --instanz daten/ebilanz/2025/ebilanz.xbrl
```
`mapping_skr03.yaml` ist generisch; firmenspezifische Abweichungen in eine zweite Datei (spätere gewinnt).
Ein Konto mit Saldo ohne Mapping bricht den Lauf ab.

## Grenzen
- Arelle prüft XBRL-Technik (Schema, Tupel, Dimensionen, Rechenregeln). Die **ERiC-Prüfungen der
  Finanzverwaltung** (Mussfeld-Vollständigkeit, Kontennachweis-Regeln, Steuernummer, Plausibilitäten
  zwischen Positionen) laufen erst mit ERiC; erst danach ist eine Instanz versandfähig.
- Die Instanz ist der XBRL-Teil; den ELSTER-Rahmen und den Versand übernimmt die ERiC-Anbindung.
- Nicht umgesetzt: Abschreibungen/Abgänge im Anlagenspiegel, Überleitungsrechnung (HB ≠ StB),
  Ergebnisverwendung, Umsatzkostenverfahren, abweichendes Wirtschaftsjahr, Personengesellschaften,
  negative Bank-/Forderungssalden als Umgliederung.
- Mapping-Positionen und Kontenbezeichnungen vor dem ersten Echtversand gegen die E-Bilanz des
  Steuerberaters (Vorjahr) abgleichen.
