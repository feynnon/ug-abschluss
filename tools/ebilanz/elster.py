"""Packt eine E-Bilanz-XBRL-Instanz in den ELSTER-Rahmen (Datenart Bilanz) für tools/elster/eric.py.

  python3 tools/ebilanz/elster.py <instanz.xbrl> <stammdaten.yaml> <ausgabe.xml>

Empfänger ist die Bundesfinanzamtsnummer aus den Stammdaten; der Stichtag kommt aus der Instanz.
Hersteller-ID und Testmerker setzt eric.py beim Prüfen/Senden.
"""
import re
import sys
from pathlib import Path

RAHMEN = """<?xml version="1.0" encoding="UTF-8"?>
<Elster xmlns="http://www.elster.de/elsterxml/schema/v11">
  <TransferHeader version="11">
    <Verfahren>ElsterBilanz</Verfahren>
    <DatenArt>Bilanz</DatenArt>
    <Vorgang>send-Auth</Vorgang>
    <HerstellerID>0</HerstellerID>
    <DatenLieferant>{firma}</DatenLieferant>
    <Datei>
      <Verschluesselung>CMSEncryptedData</Verschluesselung>
      <Kompression>GZIP</Kompression>
      <TransportSchluessel/>
    </Datei>
  </TransferHeader>
  <DatenTeil>
    <Nutzdatenblock>
      <NutzdatenHeader version="11">
        <NutzdatenTicket>1</NutzdatenTicket>
        <Empfaenger id="F">{bufa}</Empfaenger>
        <Hersteller>
          <ProduktName>ug-abschluss</ProduktName>
          <ProduktVersion>0.1</ProduktVersion>
        </Hersteller>
        <DatenLieferant>{firma}</DatenLieferant>
      </NutzdatenHeader>
      <Nutzdaten>
        <ebilanz:EBilanz version="000002" xmlns:ebilanz="http://rzf.fin-nrw.de/RMS/EBilanz/2016/XMLSchema">
          <ebilanz:stichtag>{stichtag}</ebilanz:stichtag>
{xbrl}
        </ebilanz:EBilanz>
      </Nutzdaten>
    </Nutzdatenblock>
  </DatenTeil>
</Elster>
"""


def main() -> None:
    instanz, stammdaten, aus = map(Path, sys.argv[1:4])
    s = dict(re.findall(r'^(\w+):\s*"?([^"#\n]*?)"?\s*(?:#.*)?$', stammdaten.read_text(), re.M))
    xbrl = re.sub(r"^<\?xml[^>]*\?>\s*", "", instanz.read_text(encoding="utf-8"))
    stichtag = re.search(r"<xbrli:instant>(\d{4})-(\d\d)-(\d\d)</xbrli:instant>", xbrl).groups()
    firma = s["firma"].replace("&", "&amp;")
    aus.write_text(RAHMEN.format(firma=firma, bufa=s["bundesfinanzamtsnummer"], stichtag="".join(stichtag),
                                 xbrl=xbrl), encoding="utf-8")
    print(f"-> {aus}")


if __name__ == "__main__":
    main()
