"""ERiC-Anbindung: ELSTER-Datensätze prüfen und versenden.

  python3 tools/elster/eric.py pruefen <datensatz.xml> <Datenartversion> [--pdf vorschau.pdf]
  python3 tools/elster/eric.py senden  <datensatz.xml> <Datenartversion> --zertifikat <datei.pfx> [--pdf protokoll.pdf]
  python3 tools/elster/eric.py senden  <datensatz.xml> <Datenartversion> --test   (Testsystem, Testzertifikat)

Datenartversion z. B. KSt_30_2025, GewSt_2025, Bilanz_6.8 (Namen stehen in der ERiC-Doku,
Datenartversionmatrix). ERiC wird nicht mitgeliefert (Lizenz): Jeder lädt es nach der Registrierung im
ELSTER-Entwicklerbereich selbst herunter; `ERIC_PFAD` in `.env` zeigt auf den Ordner `Linux-x86_64`.
Auf macOS/Windows läuft das Skript automatisch im Docker-Container `ug-eric` (docker/eric.Dockerfile).

Das Skript setzt die Hersteller-ID (`ELSTER_HERSTELLER_ID` aus `.env`) und den Testmerker selbst:
--test → Testmerker 700000004 (ELSTER verarbeitet nichts), sonst wird ein Testmerker entfernt.
Die PIN des Zertifikats gibt immer der Mensch ein (verdeckte Eingabe); nur beim öffentlichen
Testzertifikat aus dem ERiC-Paket wird dessen dokumentierte Test-PIN verwendet.
"""
import argparse
import ctypes as C
import getpass
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TESTMERKER = "700000004"
TEST_ZERTIFIKAT = "Beispiel/ericdemo-python/test-softidnr-pse.pfx"
TEST_PIN = "123456"  # öffentlich dokumentierte PIN des ERiC-Testzertifikats
VALIDIERE, SENDE, DRUCKE = 1 << 1, 1 << 2, 1 << 5


def env() -> dict:
    werte = {}
    datei = REPO / ".env"
    if datei.exists():
        for zeile in datei.read_text().splitlines():
            if "=" in zeile and not zeile.lstrip().startswith("#"):
                k, v = zeile.split("=", 1)
                werte[k.strip()] = v.strip()
    return {**werte, **os.environ}


def im_container(args, e) -> int:
    """Startet dieses Skript im Linux-Container; Arbeitsdateien werden unter /work eingebunden."""
    eric = Path(os.path.expanduser(e.get("ERIC_PFAD", ""))).resolve()
    if not (eric / "lib" / "libericapi.so").exists():
        sys.exit("ERIC_PFAD in .env zeigt nicht auf den ERiC-Ordner Linux-x86_64.")
    mounts, neu = [], {}
    for i, a in enumerate(p for p in (args.datensatz, args.pdf, args.zertifikat) if p):
        p = Path(a).resolve()
        mounts += ["-v", f"{p.parent}:/work/{i}"]
        neu[a] = f"/work/{i}/{p.name}"
    argv = [neu.get(a, a) for a in sys.argv[1:]]
    cmd = ["docker", "run", "--rm", "-i", "--platform", "linux/amd64", "-v", f"{eric}:/eric:ro",
           "-v", f"{Path(__file__).resolve()}:/app/tools/elster/eric.py:ro", *mounts,
           "-e", f"ELSTER_HERSTELLER_ID={e.get('ELSTER_HERSTELLER_ID', '')}"]
    if sys.stdin.isatty():
        cmd.insert(3, "-t")
    return subprocess.call(cmd + ["ug-eric", "python3", "/app/tools/elster/eric.py", *argv])


def datensatz_vorbereiten(xml: str, hersteller: str, test: bool) -> str:
    if not hersteller:
        sys.exit("ELSTER_HERSTELLER_ID fehlt in .env.")
    xml = re.sub(r"<HerstellerID>.*?</HerstellerID>", f"<HerstellerID>{hersteller}</HerstellerID>", xml, flags=re.S)
    xml = re.sub(r"\s*<Testmerker>.*?</Testmerker>", "", xml, flags=re.S)
    if test:
        xml = xml.replace("</Vorgang>", f"</Vorgang>\n        <Testmerker>{TESTMERKER}</Testmerker>", 1)
    return xml


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("aktion", choices=["pruefen", "senden"])
    ap.add_argument("datensatz")
    ap.add_argument("datenartversion")
    ap.add_argument("--pdf")
    ap.add_argument("--zertifikat")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()
    e = env()
    if not Path("/eric/lib/libericapi.so").exists():
        return im_container(args, e)

    senden = args.aktion == "senden"
    if senden and not (args.test or args.zertifikat):
        sys.exit("Zum Senden --zertifikat <datei.pfx> angeben (oder --test).")
    test = args.test or not senden and "<Testmerker>" in Path(args.datensatz).read_text()
    xml = datensatz_vorbereiten(Path(args.datensatz).read_text(encoding="utf-8"), e.get("ELSTER_HERSTELLER_ID"), test)

    lib = C.CDLL("/eric/lib/libericapi.so")
    lib.EricRueckgabepufferErzeugen.restype = C.c_void_p
    lib.EricRueckgabepufferInhalt.restype = C.c_char_p
    lib.EricRueckgabepufferInhalt.argtypes = lib.EricRueckgabepufferFreigeben.argtypes = [C.c_void_p]
    lib.EricHoleFehlerText.argtypes = [C.c_int, C.c_void_p]
    os.makedirs("/tmp/ericlog", exist_ok=True)
    if lib.EricInitialisiere(b"/eric/lib/plugins", b"/tmp/ericlog"):
        sys.exit("ERiC ließ sich nicht initialisieren.")

    class Krypto(C.Structure):
        _fields_ = [("version", C.c_uint32), ("zertifikatHandle", C.c_uint32), ("pin", C.c_char_p)]

    class Druck(C.Structure):
        _fields_ = [("version", C.c_uint32), ("vorschau", C.c_uint32), ("duplexDruck", C.c_uint32),
                    ("pdfName", C.c_char_p), ("fussText", C.c_char_p), ("pdfCallback", C.c_void_p),
                    ("pdfCallbackBenutzerdaten", C.c_void_p)]

    flags, krypto, handle = VALIDIERE, None, C.c_uint32()
    druck = None
    if args.pdf:
        flags |= DRUCKE
        druck = Druck(4, 0 if senden else 1, 0, args.pdf.encode(), None, None, None)
    if senden:
        flags |= SENDE
        pfx = args.zertifikat or f"/eric/{TEST_ZERTIFIKAT}"
        pin = TEST_PIN if args.test and not args.zertifikat else getpass.getpass("PIN des Zertifikats: ")
        if lib.EricGetHandleToCertificate(C.byref(handle), C.byref(C.c_uint32()), pfx.encode()):
            sys.exit(f"Zertifikat nicht lesbar: {pfx}")
        krypto = Krypto(3, handle.value, pin.encode())

    rueck, server = lib.EricRueckgabepufferErzeugen(), lib.EricRueckgabepufferErzeugen()
    rc = lib.EricBearbeiteVorgang(xml.encode("utf-8"), args.datenartversion.encode(), flags,
                                  C.byref(druck) if druck else None, C.byref(krypto) if krypto else None,
                                  C.c_void_p(rueck), C.c_void_p(server))
    antwort = (lib.EricRueckgabepufferInhalt(rueck) or b"").decode("utf-8", "replace")
    serverantwort = (lib.EricRueckgabepufferInhalt(server) or b"").decode("utf-8", "replace")
    text = lib.EricRueckgabepufferErzeugen()
    lib.EricHoleFehlerText(rc, C.c_void_p(text))
    print(f"ERiC: {rc} {(lib.EricRueckgabepufferInhalt(text) or b'').decode('utf-8', 'replace')}")
    print(antwort)
    if serverantwort:
        print(serverantwort)
    for p in (rueck, server, text):
        lib.EricRueckgabepufferFreigeben(C.c_void_p(p))
    if handle.value:
        lib.EricCloseHandleToCertificate(handle)
    lib.EricBeende()
    if rc == 0 and senden:
        print("\nVersand erfolgreich" + (" (Testsystem – ELSTER verarbeitet nichts)." if test else "."))
        if not test:
            print("ug-abschluss ist Open Source und kostenlos. Wenn es dir Arbeit oder Kosten erspart hat, "
                  "kannst du die Weiterentwicklung unterstützen: https://github.com/sponsors/feynnon")
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
