#!/usr/bin/env python3
"""Base Salamence correction on the validated sole-Golisopite sand roster.

The old set is an Aerilate Mega Salamence carryover with Focus Sash vulnerable
to allied Tyranitar's sand. Compare two one-factor controls and four legal
coherent base-Salamence sets on pinned weather-aware M-C Champions Lab. Freeze
a training winner before fresh holdout. These are BOT simulated games.
"""
from __future__ import annotations
import json, sys, traceback
from pathlib import Path
from datetime import datetime,timezone
from evolve import ROOT,ENGINE,run_cli,checked_rate,parse_team,stringify,locked,exclusive_mega_golisopod

OUT=ROOT/"reports/base-salamence-audit"
TEAM=ROOT/"teams/golisopod-current.txt"
LAIC=ROOT/"teams/benchmark-laic-champion-published-proxy.txt"
SOURCE=ROOT/"data/latest-teams.json"
POLICY="POKEPROTOCOL_WEATHER_PREVIEW_V2"
FIELD_SEEDS=("salamence-base-2026-field-A","salamence-base-2026-field-B")
FIELD_PER_SEED=100
MATCH_N=70
LOOKAHEAD_N=16
HOLDOUT_N=280
CONFIGS={
    "legacy sash hyper voice":("Focus Sash","Hyper Voice"),
    "sash heat wave control":("Focus Sash","Heat Wave"),
    "sitrus heat wave":("Sitrus Berry","Heat Wave"),
    "haban heat wave":("Haban Berry","Heat Wave"),
    "sitrus air slash":("Sitrus Berry","Air Slash"),
    "haban air slash":("Haban Berry","Air Slash"),
}
ELIGIBLE=tuple(name for name in CONFIGS if name.startswith(("sitrus","haban")))

def save(path,data):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/path).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf8")

def pct(v):
    return f"{100*v:.1f}%"

def summarize(obj,key,n):
    result=checked_rate(obj,key,n)
    return {k:result.get(k) for k in ("wins","losses","ties","n","rate","ci95")}

def brought(result,species):
    side=result.get("side",result.get("a",{}))
    return next((r.get("brought",0) for r in side.get("bringRate",[]) if r.get("species")==species),0)

def revise(original,item,move):
    parts=list(parse_team(original))
    idx=next(i for i,x in enumerate(parts) if x.species=="Salamence")
    raw=parts[idx].text
    if "@ Focus Sash" not in raw or raw.count("- Hyper Voice")!=1:
        raise RuntimeError("Canonical Salamence anchor changed; inspect active team")
    raw=raw.replace("@ Focus Sash","@ "+item)
    raw=raw.replace("- Hyper Voice","- "+move)
    parts[idx]=type(parts[idx])(raw)
    team=tuple(parts)
    if not exclusive_mega_golisopod(team):
        raise RuntimeError("Variant violates sole-Mega-Golisopod theme")
    if len(team)!=6: raise RuntimeError("Invalid team length")
    return stringify(team)

def second_ots():
    from evolve import registered_set
    data=json.loads(SOURCE.read_text(encoding="utf8"))
    if len(data.get("teams",[]))<2: raise RuntimeError("Missing second complete registered tournament winner")
    sets=[registered_set(x) for x in data["teams"][1]["sets"]]
    if len(sets)!=6 or any(x is None for x in sets):
        raise RuntimeError("Incomplete second tournament winner")
    path=OUT/"registered-opponent.txt"
    path.write_text(stringify(tuple(sets)),encoding="utf8")
    return path

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    meta={"status":"running","started_at":datetime.now(timezone.utc).isoformat(),
          "engine":"09d59984631dd2a45fb21700970c65ee24cf7d0f",
          "policy":POLICY,"seed_source":str(TEAM),"seeds":FIELD_SEEDS,
          "field_per_seed":FIELD_PER_SEED,"match_games":MATCH_N,
          "lookahead_games":LOOKAHEAD_N,"holdout_games":HOLDOUT_N,
          "eligible":ELIGIBLE}
    save("manifest.json",meta)
    try:
        source=ENGINE/"src/engine/policy/preview.ts"
        if not source.exists() or POLICY not in source.read_text(encoding="utf8"):
            raise RuntimeError("Refusing uncorrected simulator preview model")
        if not (ROOT/"reports/evolution/weather-preview-policy.json").is_file():
            raise RuntimeError("Missing pinned preview policy provenance")
        original=TEAM.read_text(encoding="utf8")
        if not exclusive_mega_golisopod(parse_team(original)):
            raise RuntimeError("Canonical team is not sole-Mega-Golisopod")
        from_evolution = {}
        for name,(item,move) in CONFIGS.items():
            path=OUT/("team-"+name.replace(" ","-")+".txt")
            paste=revise(original,item,move)
            path.write_text(paste,encoding="utf8")
            verdict=run_cli("validate",path)
            save("validate-"+name.replace(" ","-")+".json",verdict)
            if verdict.get("ok") is not True:
                raise RuntimeError("Illegal Salamence variant "+name+": "+str(verdict.get("problems")))
            from_evolution[name]=path
        opponents={"LAIC champion published-set proxy":LAIC,
                   "Recent tournament winner #2":second_ots()}
        for name,path in opponents.items():
            verdict=run_cli("validate",path)
            if verdict.get("ok") is not True:
                raise RuntimeError("Illegal benchmark "+name+": "+str(verdict.get("problems")))
        training={}
        for i,(name,path) in enumerate(from_evolution.items()):
            print("EVAL",name,flush=True)
            wins=losses=ties=0;sal_bring=[];goli_bring=[];mega=[]
            for seed in FIELD_SEEDS:
                res=run_cli("field",path,"--n",FIELD_PER_SEED,
                            "--player","heuristic","--seed",seed)
                w=summarize(res,"winRate",FIELD_PER_SEED)
                wins+=w["wins"];losses+=w["losses"];ties+=w["ties"]
                sal_bring.append(brought(res,"Salamence"))
                goli_bring.append(brought(res,"Golisopod"))
                mega.append(res.get("side",{}).get("megaEvolvedIn",0))
                save("field-"+str(i)+"-"+seed+".json",res)
            n=wins+losses+ties
            field=(wins+0.5*ties)/n
            against={}
            for j,(opname,opp) in enumerate(opponents.items()):
                res=run_cli("sim",path,opp,"--n",MATCH_N,
                            "--player","heuristic","--seed","base-salamence-2026|"+opname,"--logs",3)
                against[opname]=summarize(res,"winRateA",MATCH_N)
                save("match-"+str(i)+"-"+str(j)+".json",res)
            score=0.70*field+0.15*against["LAIC champion published-set proxy"]["rate"]+0.15*against["Recent tournament winner #2"]["rate"]
            training[name]={"wins":wins,"losses":losses,"ties":ties,"n":n,
                            "field_rate":field,"score":score,
                            "sal_bring":sum(sal_bring)/len(sal_bring),
                            "goli_bring":sum(goli_bring)/len(goli_bring),
                            "goli_mega":sum(mega)/len(mega),
                            "matchups":against}
            save("training.json",training)
            print("SCORE",name,pct(score),flush=True)
        ranked=sorted(ELIGIBLE,key=lambda name:(-training[name]["score"],name))
        # Tie threshold avoids over-reading a few lucky battles: prioritize
        # a more broadly helpful Fire spread move when within 1 percentage point.
        best=ranked[0]
        heat=[name for name in ranked if name.endswith("heat wave")]
        if heat and training[heat[0]]["score"]>=training[best]["score"]-0.01:
            best=heat[0]
        frozen=best
        challenger=ranked[0] if ranked[0]!=frozen else ranked[1]
        meta.update({"frozen_winner":frozen,"eligible_ranking":ranked})
        save("manifest.json",meta)
        (OUT/"best.txt").write_text(from_evolution[frozen].read_text(encoding="utf8"),encoding="utf8")
        # Lookahead is a diagnostic performed AFTER selection and cannot
        # affect chosen finalist.
        advanced={}
        for name in dict.fromkeys([frozen,challenger]):
            advanced[name]={}
            for j,(opname,opp) in enumerate(opponents.items()):
                r=run_cli("sim",from_evolution[name],opp,"--n",LOOKAHEAD_N,
                          "--player","search","--seed","base-salamence-2026|search|"+opname,"--logs",3)
                advanced[name][opname]=summarize(r,"winRateA",LOOKAHEAD_N)
                save("strong-"+name.replace(" ","-")+"-"+str(j)+".json",r)
        save("lookahead.json",advanced)
        holdout={}
        for name in dict.fromkeys([frozen,"legacy sash hyper voice"]):
            r=run_cli("field",from_evolution[name],"--n",HOLDOUT_N,
                      "--player","heuristic","--seed","base-salamence-2026|HOLDOUT")
            holdout[name]={**summarize(r,"winRate",HOLDOUT_N),
                           "sal_bring":brought(r,"Salamence"),
                           "goli_bring":brought(r,"Golisopod"),
                           "goli_mega":r.get("side",{}).get("megaEvolvedIn")}
            save("holdout-"+name.replace(" ","-")+".json",r)
        save("holdout.json",holdout)
        lines=["# Correcting inherited Mega Salamence moves and item on base Salamence","",
               "**M-C weather-aware pinned simulator. Bot battles, not tournament performance.**",
               "Reason: no Aerilate without Mega, so Hyper Voice loses Flying STAB and boost.",
               "Tyranitar Sand Stream can also remove a Focus Sash's full-HP protection.",
               "All six candidate rosters passed actual Champions Lab M-C legality checks.",
               "Original and Focus Sash + Heat Wave are diagnostics only; selection is",
               "restricted to non-Sash Salamence with STAB Air Slash or Fire Heat Wave.",
               "Selection is 70% field plus 15% each two full-six benchmark structures.",
               "LAIC published move/item/nature proxy uses inferred Stat Point spreads.",
               "Winner frozen before new holdout. Equal-ish 1pp training scores prefer",
               "Fire spread coverage over Air Slash. Golisopite remains the ONLY Mega Stone.",
               "", "## Training comparisons", "",
               "| Base Salamence set | Field W/N | Rate | LAIC proxy | Recent winner #2 | Sal brought | Mega Goli used | Selection score |",
               "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for name,row in sorted(training.items(),key=lambda v:-v[1]["score"]):
            lines.append(f"| {name} | {row['wins']}/{row['n']} | {pct(row['field_rate'])} | "+
                         f"{pct(row['matchups']['LAIC champion published-set proxy']['rate'])} | "+
                         f"{pct(row['matchups']['Recent tournament winner #2']['rate'])} | "+
                         f"{pct(row['sal_bring'])} | {pct(row['goli_mega'])} | {pct(row['score'])} |")
        lines+=["","**Final pre-holdout choice: "+frozen+"**","",
                "## Lookahead check (small samples)","",
                "| Set | Opponent | W/N | Rate |","|---|---|---:|---:|"]
        for name,match in advanced.items():
            for opp,w in match.items():
                lines.append(f"| {name} | {opp} | {w['wins']}/{w['n']} | {pct(w['rate'])} |")
        lines+=["","## Independent holdout","",
                "| Set | W/N | Win rate | Salamence brought | Mega Goli activated |",
                "|---|---:|---:|---:|---:|"]
        for name,w in holdout.items():
            lines.append(f"| {name} | {w['wins']}/{w['n']} | {pct(w['rate'])} | "+
                         f"{pct(w['sal_bring'])} | {pct(w['goli_mega'] or 0)} |")
        lines+=["","## Final full Showdown paste","",
                "~~~",from_evolution[frozen].read_text(encoding="utf8").rstrip(),"~~~","",
                "All non-Salamence Pokémon, items, spreads and moves were unchanged;",
                "the Mega Golisopod-only constraint remained enforced.",
                "All conclusions are provisional under M-C; M-D remains unverified.",""]
        (OUT/"summary.md").write_text("\n".join(lines),encoding="utf8")
        meta.update({"status":"completed","completed_at":datetime.now(timezone.utc).isoformat()})
        save("manifest.json",meta)
        print("\n".join(lines),flush=True)
    except Exception as exc:
        meta.update({"status":"failed","error":str(exc)})
        save("manifest.json",meta)
        (OUT/"summary.md").write_text("# Salamence correction failed\n\nNo results claimed.\n"+str(exc),encoding="utf8")
        traceback.print_exc()
        sys.exit(1)

if __name__=="__main__":
    main()
