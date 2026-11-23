#!/usr/bin/env python3
"""Is Mega Golisopod worth its slot? Test an exact one-slot counterfactual.
Paired field sampling: both teams face the same opponent/seat/seed distribution.
Neither team uses guessed moves: both are explicit Showdown imports.
"""
import json, os, subprocess, hashlib, sys, traceback
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/"champions-lab"
OUT=ROOT/"reports/golisopod-audit"
CASES={"Golisopod":"sneasler.txt","No Golisopod":"no_golisopod.txt"}

def cli(args):
    run=subprocess.run(["node","src/cli/lab.ts",*map(str,args)],cwd=LAB,text=True,
                       capture_output=True)
    if run.returncode:
        raise RuntimeError("CLI returned "+str(run.returncode)+"\n"+run.stderr[-3000:]+"\n"+run.stdout[-1000:])
    try: result=json.loads(run.stdout)
    except Exception as e: raise RuntimeError("Invalid simulator JSON "+run.stdout[:500]) from e
    if isinstance(result,dict) and result.get("error"):raise RuntimeError(str(result["error"]))
    return result

def save(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")

def percent(v):return f"{v*100:.1f}%"

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    n=200
    seed="golivalue-nov23-01"
    manifest={"date":datetime.now(timezone.utc).isoformat(),"seed":seed,"player":"heuristic",
              "gamesPerFieldArm":n,"gamesHeadToHead":100,
              "engine":"joshuamatalon/champions-lab@09d59984631dd2a45fb21700970c65ee24cf7d0f",
              "comparisons":{}}
    try:
        for key,file in CASES.items():
            p=ROOT/"teams"/file
            manifest["comparisons"][key]={"path":str(p.relative_to(ROOT)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
            v=cli(["validate",p])
            save("validate_"+file.replace(".txt",".json"),v)
            if not v.get("ok"):raise RuntimeError("Illegal team "+key+": "+str(v.get("problems")))
        results={}
        for key,file in CASES.items():
            r=cli(["field",ROOT/"teams"/file,"--n",n,"--player","heuristic","--seed",seed])
            if r.get("winRate",{}).get("n")!=n:raise RuntimeError("Invalid sample size "+key)
            save(("goli_field" if key=="Golisopod" else "nogoli_field")+".json",r)
            results[key]=r
        h=cli(["sim",ROOT/"teams"/CASES["Golisopod"],ROOT/"teams"/CASES["No Golisopod"],
              "--n",100,"--player","heuristic","--seed",seed,"--logs",3])
        if h.get("winRateA",{}).get("n")!=100:raise RuntimeError("Head-to-head sample mismatch")
        save("headtohead.json",h)
        field=results["Golisopod"]["provenance"].get("field",{})
        manifest["field"]=field
        manifest["status"]="completed"
        save("manifest.json",manifest)
        lines=[
            "# Mega Golisopod versus no-Golisopod controlled comparison", "",
            "Both teams share Mega Raichu X, Pelipper, Archaludon, Basculegion-F and Electric Seed Sneasler.",
            "**Only the sixth slot differs**: Mega Golisopod versus Incineroar (Sitrus Berry).",
            f"**Simulation:** {n} battles per field arm (same field seed \`{seed}\`, opponent distribution and alternate seats), 100 head-to-head battles, heuristic players.",
            f"**Field:** {field.get('teams','?')} teams, {field.get('events','?')} events, built {field.get('builtAt','unknown')}.",
            "",
            "| Test | Wins | Losses | Rate | 95% CI |",
            "|---|---:|---:|---:|---|",
        ]
        for k in CASES:
            w=results[k]["winRate"]
            lines.append(f"| {k} vs field | {w['wins']} | {w['losses']} | {percent(w['rate'])} | {percent(w['ci95'][0])}–{percent(w['ci95'][1])} |")
        w=h["winRateA"]
        lines.append(f"| Golisopod vs no Golisopod directly | {w['wins']} | {w['losses']} | {percent(w['rate'])} | {percent(w['ci95'][0])}–{percent(w['ci95'][1])} |")
        lines+=["",
            "**Interpretation limits:** This is bot-vs-bot, not tournament results. The field comparison is more informative than direct mirrors for broad viability. Repeating with a stronger search agent, newer regulation engine and multiple plausible Golisopod replacements is necessary before retiring a championship-proven Pokémon.",
            "",
            "The comparison team drops our second Mega option. This is an explicit tradeoff, not a claim to identify the universally best replacement.",
            ""]
        (OUT/"summary.md").write_text("\n".join(lines),encoding="utf-8")
        print("SUCCESS",json.dumps({k:v["winRate"] for k,v in results.items()}),json.dumps(h["winRateA"]))
    except Exception as e:
        manifest["status"]="failed";manifest["error"]=str(e)
        save("manifest.json",manifest)
        (OUT/"summary.md").write_text("### Golisopod test failed\n\nNo battle win rates are claimed.\n\n"+str(e)[:2000],encoding="utf-8")
        traceback.print_exc()
        sys.exit(1)

if __name__=="__main__":
    main()
