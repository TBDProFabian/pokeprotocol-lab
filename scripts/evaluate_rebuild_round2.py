#!/usr/bin/env python3
"""Run reproducible Golisopod-centered team search on the pinned Champions simulator.

This is not a prediction of human tournament results. "Official champion" teams
are *proxies* using the most common registered sets for the six species, not
those champions' unreleased/unknown exact sets.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/"champions-lab"
OUT=ROOT/"reports"/"golisopod-round2"
OUT.mkdir(parents=True,exist_ok=True)
CANDIDATES={
  "Balance Pivot":"build-balance-pivot.txt",
  "Balance Defiant":"build-balance-defiant.txt",
  "Rain Wings":"build-rain-wings.txt",
  "Rain Armor":"build-rain-armor.txt",
  "Original Rain Semiroom":"build-rain-semiroom.txt",
}
OPPONENTS={
  "LAIC winning-six proxy":"benchmark-laic-rain-proxy.txt",
  "Gdansk winning-six proxy":"benchmark-gdansk-sand-proxy.txt",
}
FIELD_N=200
PROXY_N=80
SEARCH_N=20
H2H_N=100
SEED="goli-nov23-2026-round2"

def path(fname:str) -> Path:
    p=ROOT/"teams"/fname
    if not p.is_file(): raise RuntimeError("Missing team file "+str(p))
    return p

def cli(args:list[str], label:str) -> dict:
    result=subprocess.run(["node","src/cli/lab.ts",*map(str,args)],cwd=LAB,
                          capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(f"{label} exited {result.returncode}. STDOUT: {result.stdout[-1800:]} STDERR: {result.stderr[-2400:]}")
    try:
        obj=json.loads(result.stdout)
    except Exception as e:
        raise RuntimeError(f"{label} emitted invalid JSON: {result.stdout[-1400:]}") from e
    if not isinstance(obj,dict) or "error" in obj:raise RuntimeError(f"{label}: {obj}")
    return obj

def save_json(name:str,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf8")

def percent(p):
    return f"{100*p:.1f}%" if p is not None else "?"

def br(result):
    obj=result.get("side",result.get("a",{}))
    r=obj.get("bringRate",[])
    for x in r:
        if x.get("species")=="Golisopod":
            return x
    return {"brought":0,"led":0}

def wline(name,win):
    ci=win["ci95"]
    return f"| {name} | {win['wins']} | {win['losses']} | {win['ties']} | {win['n']} | {percent(win['rate'])} | {percent(ci[0])}–{percent(ci[1])} |"

manifest={
  "createdAt":datetime.now(timezone.utc).isoformat(),
  "format":"gen9championsvgc2026regmc",
  "engineRepo":"joshuamatalon/champions-lab",
  "engineCommit":"09d59984631dd2a45fb21700970c65ee24cf7d0f",
  "playerFast":"heuristic",
  "playerStrong":"search",
  "fieldGamesPerTeam":FIELD_N,
  "proxyGamesPerMatchup":PROXY_N,
  "strongGamesPerMatchup":SEARCH_N,
  "finalistHeadToHead":H2H_N,
  "seed":SEED,
  "sets":{k:hashlib.sha256(path(v).read_bytes()).hexdigest() for k,v in {**CANDIDATES,**OPPONENTS}.items()}
}
try:
    for name, file in {**CANDIDATES, **OPPONENTS}.items():
        verdict=cli(["validate",path(file)],"validate "+name)
        save_json("validate-"+file.replace(".txt",".json"),verdict)
        if verdict.get("ok") is not True:
            raise RuntimeError(f"Illegal {name}: {verdict.get('problems')}")
    rounds={}
    for i,(name,file) in enumerate(CANDIDATES.items()):
        res=cli(["field",path(file),"--n",FIELD_N,"--player","heuristic","--seed",SEED],"field "+name)
        if res.get("winRate",{}).get("n")!=FIELD_N:raise RuntimeError("Field sample count mismatch")
        rounds[name]=res
        save_json(f"field-{i}.json",res)
    ranked=sorted(rounds,key=lambda n:rounds[n]["winRate"]["rate"],reverse=True)
    finalists=ranked[:2]
    preview={}
    for name in finalists:
        for oname, ofile in OPPONENTS.items():
            afile=CANDIDATES[name]
            prefix=f"{list(CANDIDATES).index(name)}-{list(OPPONENTS).index(oname)}"
            preview[(name,oname,"heuristic")]=cli(
                ["sim",path(afile),path(ofile),"--n",PROXY_N,"--player","heuristic","--seed",SEED+"|"+oname,
                "--logs","1"],"proxy "+prefix)
            save_json("proxy-"+prefix+".json",preview[(name,oname,"heuristic")])
            preview[(name,oname,"search")]=cli(
                ["sim",path(afile),path(ofile),"--n",SEARCH_N,"--player","search","--seed",SEED+"|"+oname,
                 "--logs","1"],"search "+prefix)
            save_json("strong-"+prefix+".json",preview[(name,oname,"search")])
    face=cli(["sim",path(CANDIDATES[finalists[0]]),path(CANDIDATES[finalists[1]]),
              "--n",H2H_N,"--player","heuristic","--seed",SEED+"|finalists",
              "--logs","2"],"finalist head-to-head")
    save_json("finalist-headtohead.json",face)
    manifest["status"]="completed"
    manifest["field"]=rounds[ranked[0]].get("provenance",{}).get("field",{})
    manifest["ranking"]=ranked
    manifest["finalists"]=finalists
    save_json("manifest.json",manifest)
    summary=[
        "# Poképrotocol Golisopod rebuild: simulator tournament",
        "",
        "**Every candidate contains Mega Golisopod.** This experiment compares different cores, not the value of dropping Golisopod.",
        f"**Simulator:** {manifest['format']}, pinned engine \`{manifest['engineCommit'][:12]}\`.",
        f"**Field:** {manifest['field'].get('teams','?')} recent validated online teams, {manifest['field'].get('events','?')} events, assembled {manifest['field'].get('builtAt','unknown')}.",
        f"**Method:** {FIELD_N} battles per candidate versus same sampled field distribution/seed, 50% each seat, heuristic opponent AI.",
        "",
        "| Candidate | W | L | T | N | Rate | 95% CI |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for name in ranked:
        summary.append(wline(name,rounds[name]["winRate"]))
    summary += ["","### Golisopod usage (field runs)",
       "| Candidate | Brought | Led | Any Mega evolved | Mean turns |",
       "|---|---:|---:|---:|---:|"]
    for name in ranked:
        v=rounds[name]; b=br(v)
        summary.append(f"| {name} | {percent(b['brought'])} | {percent(b['led'])} | {percent(v['side'].get('megaEvolvedIn',0))} | {v['side'].get('meanTurns','?')} |")
    summary += ["","### Leading two vs complete winning-six proxies",
         "These are **not exact champions' Open Team Sheets**. Each proxy uses common complete M-C registered sets for the six species; their matchups indicate archetype coverage, not verified championship-team outcomes.","",
        "| Candidate | Proxy | Fast AI | 95% CI | Lookahead AI | 95% CI |",
        "|---|---|---:|---|---:|---|"]
    for name in finalists:
        for oname in OPPONENTS:
            a=preview[(name,oname,"heuristic")]["winRateA"]
            b=preview[(name,oname,"search")]["winRateA"]
            summary.append(f"| {name} | {oname} | {percent(a['rate'])} ({a['n']} games) | {percent(a['ci95'][0])}–{percent(a['ci95'][1])} | {percent(b['rate'])} ({b['n']} games) | {percent(b['ci95'][0])}–{percent(b['ci95'][1])} |")
    h=face["winRateA"]
    summary += ["","### Head-to-head finalists",
                f"{finalists[0]} beats {finalists[1]} in **{h['wins']} of {h['n']}** simulated battles ({percent(h['rate'])}); 95% CI {percent(h['ci95'][0])}–{percent(h['ci95'][1])}.",
                "",
        "### Important qualifications",
        "- Five tested teams were built from combinations of legal moves and items observed in recent tournament registrations, with one intentionally adjusted bulky Golisopod Stat Point spread.",
        "- All simulations use a pinned M-C mechanics engine, not unreleased M-D changes.",
        "- Field differences need confidence intervals, and the 20-game lookahead results are *qualitative stress tests*, not precision rankings.",
        "- Stat Points of many tournament opponents are inferred from priors, not observed.",
        "- Best team is not necessarily the one with the highest single 200-game field average; consider bring rates and matchup coverage.",
        ""]
    (OUT/"summary.md").write_text("\n".join(summary),encoding="utf8")
    print(json.dumps({"success":True,"ranked":ranked,"field":{k:v["winRate"] for k,v in rounds.items()},
                     "finalists":finalists,"headtohead":h},indent=2))
except Exception as e:
    manifest["status"]="failed"
    manifest["error"]=str(e)
    save_json("manifest.json",manifest)
    (OUT/"summary.md").write_text("# Golisopod rebuild experiment failed\n\nNo win rates claimed.\n\n"+str(e),encoding="utf8")
    traceback.print_exc()
    sys.exit(1)
