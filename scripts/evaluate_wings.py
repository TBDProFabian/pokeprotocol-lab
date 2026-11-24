#!/usr/bin/env python3
"""Final move/slot tune for the Golisopod Rain Wings contender. All real simulations."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,sys,traceback
ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/"champions-lab"
OUT=ROOT/"reports/golisopod-wings"
OUT.mkdir(parents=True,exist_ok=True)
ARM={
  "Wings Snarl":"build-rain-wings.txt",
  "Wings Aura Sphere":"build-rain-wings-aura.txt",
  "Wings Kingambit":"build-rain-wings-king.txt",
  "Wings Incineroar":"build-rain-wings-incin.txt",
}
OPP={
  "LAIC rain proxy":"benchmark-laic-rain-proxy.txt",
  "Gdansk sand proxy":"benchmark-gdansk-sand-proxy.txt",
}
SEED="nov23-wings-final-1"
def p(f):return ROOT/"teams"/f
def run(args):
    r=subprocess.run(["node","src/cli/lab.ts",*map(str,args)],cwd=LAB,text=True,capture_output=True)
    if r.returncode:raise RuntimeError(r.stdout[-1200:]+r.stderr[-2400:])
    try:j=json.loads(r.stdout)
    except Exception: raise RuntimeError("invalid JSON: "+r.stdout[-900:])
    if isinstance(j,dict) and j.get("error"):raise RuntimeError(str(j["error"]))
    return j
def store(f,obj):(OUT/f).write_text(json.dumps(obj,indent=2),encoding="utf8")
def fmt(v):return f"{v*100:.1f}%"
def wline(v):
    w=v["winRateA"] if "winRateA" in v else v["winRate"]
    return f"{fmt(w['rate'])} ({w['wins']}/{w['n']})"
meta={"created":datetime.now(timezone.utc).isoformat(),"seed":SEED,"fieldN":200,"proxyN":80}
try:
    for n,file in {**ARM,**OPP}.items():
        d=run(["validate",p(file)])
        if not d.get("ok"):raise RuntimeError(f"{n} is illegal: {d.get('problems')}")
    field={}
    for i,(n,file) in enumerate(ARM.items()):
        d=run(["field",p(file),"--n","200","--player","heuristic","--seed",SEED])
        if d["winRate"]["n"]!=200:raise RuntimeError("field sample count mismatch")
        field[n]=d
        store("field-"+str(i)+".json",d)
    proxy={}
    for i,(n,file) in enumerate(ARM.items()):
        for j,(opp,oppfile) in enumerate(OPP.items()):
            d=run(["sim",p(file),p(oppfile),"--n","80","--player","heuristic",
                   "--seed",SEED+"|"+opp,"--logs","1"])
            if d["winRateA"]["n"]!=80:raise RuntimeError("proxy sample count mismatch")
            proxy[(n,opp)]=d
            store(f"proxy-{i}-{j}.json",d)
    ranking=sorted(ARM,key=lambda n:field[n]["winRate"]["rate"],reverse=True)
    meta["status"]="completed"
    meta["field"]=field[ranking[0]]["provenance"]["field"]
    meta["ranking"]=ranking
    store("manifest.json",meta)
    md=["# Poképrotocol: Mega Golisopod Rain Wings final tuning","",
        "All four versions use Golisopod, Salamence, Rillaboom, Pelipper and Basculegion-F.",
        "The sixth is Archaludon (Snarl or Aura Sphere), Kingambit, or Incineroar.",
        "**Method:** 200 battles per build versus the same 35-day Limitless field seed, plus 80 battles per build against each championship-winning-six *proxy*. No proxy uses a champion's verified full Open Team Sheet.",
        f"**Field:** {meta['field'].get('teams')} teams; dated {meta['field'].get('builtAt')}.","",
        "| Version | vs field | LAIC rain proxy | Gdansk sand proxy | Golisopod brought |",
        "|---|---:|---:|---:|---:|"]
    for n in ranking:
        b=next(x for x in field[n]["side"]["bringRate"] if x["species"]=="Golisopod")
        md.append(f"| {n} | {wline(field[n])} | {wline(proxy[(n,'LAIC rain proxy')])} | {wline(proxy[(n,'Gdansk sand proxy')])} | {fmt(b['brought'])} |")
    md+=["","**Caution:** n=80 per proxy is still noisy. Bot-versus-bot results are not human tournament forecasts. Do not overfit the selected team to proxy sets or assert differences are significant without sufficient samples."]
    (OUT/"summary.md").write_text("\n".join(md),encoding="utf8")
    print("\n".join(md))
except Exception as e:
    meta["status"]="failed";meta["error"]=str(e)
    store("manifest.json",meta)
    (OUT/"summary.md").write_text("Experiment failed: "+str(e),encoding="utf8")
    traceback.print_exc()
    sys.exit(1)
