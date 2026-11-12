"""Formular, Zeile und Wert aus ELSTER-Ausdrucken eines Steuerberaters ziehen (Sollwerte für Evals).

  pdftotext -bbox erklaerung.pdf erklaerung.html && python3 tools/elster/felder_aus_pdf.py erklaerung.html > felder.yaml

Heuristisch: Formularerkennung über Seitentext, Zeilennummer links, Wert rechts. Ergebnis immer
von Hand sichten – Ankreuz-Codes und gedruckte Kennzahlen können als Werte erscheinen.
"""
import re,sys,html,yaml
FORMS=[("GewSt 1 A","Gewerbesteuererklärung"),("Anlage GK","Anlage GK"),("Anlage Verluste","Verbleibender Verlustvortrag"),
       ("Anlage ZVE","Anlage ZVE"),("KSt 1 F","Einlagekonto"),("Anlage WA","Anlage WA"),("KSt 1","Körperschaftsteuererklärung")]
src=open(sys.argv[1]).read(); res=[]
for pi,p in enumerate(src.split('<page ')[1:],1):
    ws=[(float(a),float(b),html.unescape(w)) for a,b,w in re.findall(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="[\d.]+" yMax="[\d.]+">([^<]*)</word>',p)]
    text=" ".join(w for _,_,w in ws[:200])
    form=next((f for f,key in FORMS if key in text),"?")
    for x,y,w in ws:
        if x<400 or not re.fullmatch(r'-?\d{1,3}(\.\d{3})*(,\d{2})?',w): continue
        if re.fullmatch(r'\d{2}\.\d{3}',w): continue  # Kennzahl
        row=[(x2,w2) for x2,y2,w2 in ws if abs(y2-y)<5 and x2<x]
        zl=[w2 for x2,w2 in row if x2<95 and re.fullmatch(r'\d{1,3}[a-z]?',w2)]
        label=" ".join(w2 for x2,w2 in row if x2>=95)[:70]
        if zl: res.append({"seite":pi,"formular":form,"zeile":zl[0],"wert":w,"text":label})
yaml.safe_dump(res,sys.stdout,allow_unicode=True,sort_keys=False,width=200)
