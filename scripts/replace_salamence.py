#!/usr/bin/env python3
"""Replace non-Mega Salamence on Mega Golisopod M-C sand.

User does not want ordinary Salamence on the six. This experiment compares
fully legal, one-Mega alternatives against the inherited baseline, plus an
optional dual-Mega Salamencite benchmark. Competition entries MUST keep
Golisopite as the only Mega Stone. All battle results are bot simulations.

Run candidate training, then freeze winner before fresh holdout. Never
claim matchup proxies are exact championship sheets if spreads inferred.
"""
from __future__ import annotations
import json, re, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
from evolve import ROOT, ENGINE, SetBlock, parse_team, stringify, exclusive_mega_golisopod, locked, registered_set, run_cli, checked_rate

OUT=ROOT/"reports/replace-salamence"
TEAM=ROOT/"teams/golisopod-salamence-replacement-baseline.txt"
LAIC=ROOT/"teams/benchmark-laic-champion-published-proxy.txt"
REG=ROOT/"data/latest-teams.json"
POLICY="POKEPROTOCOL_WEATHER_PREVIEW_V2"
FIELD_N=160
MATCH_N=80
LOOKAHEAD_N=16
HOLDOUT_N=320
# Empirical candidate sets sourced from current tournament usage and legal learnsets.
# Each set is still checked by the pinned M-C Showdown validator.
SETS={
"Staraptor | balanced Intimidate/Tailwind": """Staraptor @ Sitrus Berry
Ability: Intimidate
Level: 50
EVs: 2 HP / 32 Atk / 32 Spe
Jolly Nature
- Brave Bird
- Close Combat
- Tailwind
- Protect""",
"Staraptor | Choice Scarf Final Gambit": """Staraptor @ Choice Scarf
Ability: Intimidate
Level: 50
EVs: 32 HP / 2 Atk / 32 Spe
Jolly Nature
- Final Gambit
- Brave Bird
- Close Combat
- U-turn""",
"Incineroar | defensive pivot": """Incineroar @ Sitrus Berry
Ability: Intimidate
Level: 50
EVs: 32 HP / 1 Def / 10 SpD / 23 Spe
Careful Nature
- Fake Out
- Parting Shot
- Flare Blitz
- Throat Chop""",
"Whimsicott | priority Tailwind": """Whimsicott @ Mental Herb
Ability: Prankster
Level: 50
EVs: 2 HP / 32 SpA / 32 Spe
Timid Nature
- Moonblast
- Tailwind
- Encore
- Protect""",
"Talonflame | Gale Wings Tailwind": """Talonflame @ Sharp Beak
Ability: Gale Wings
Level: 50
EVs: 2 HP / 32 Atk / 32 Spe
Jolly Nature
- Brave Bird
- Flare Blitz
- Tailwind
- Protect""",
"Corviknight | sand-proof Tailwind": """Corviknight @ Sitrus Berry
Ability: Mirror Armor
Level: 50
EVs: 32 HP / 1 Atk / 1 Def / 15 SpD / 17 Spe
Careful Nature
- Brave Bird
- Roost
- Tailwind
- Protect""",
"Farigiraf | Armor Tail semiroom": """Farigiraf @ Sitrus Berry
Ability: Armor Tail
Level: 50
EVs: 32 HP / 2 SpA / 32 SpD
Modest Nature
- Psychic
- Trick Room
- Helping Hand
- Protect""",
"Salamence | Salamencite flex Mega (reference)": """Salamence @ Salamencite
Ability: Intimidate
Level: 50
EVs: 2 HP / 32 SpA / 32 Spe
Timid Nature
- Hyper Voice
- Draco Meteor
- Tailwind
- Protect"""
}
REFERENCE="Salamence | Salamencite flex Mega (reference)"
BASELINE="Salamence | old base reference"
SEEDS=("goli-sala-replace-field-A","goli-sala-replace-field-B")

def save(path,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/path).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf8")

def pct(v):return f"{v*100:.1f}%"

def selected_rate(result,species):
    side=result.get("side",result.get("a",{}))
    return next((p.get("brought",0) for p in side.get("bringRate",[]) if p.get("species")==species),0.0)

def mega_rate(result):
    return result.get("side",result.get("a",{})).get("megaEvolvedIn",0)

def rate(result,key,n):
    x=checked_rate(result,key,n)
    return {k:x.get(k) for k in ("wins","losses","ties","n","rate","ci95")}

def variant(original,name):
    if name==BASELINE:
        return original
    team=list(parse_team(original))
    i=next(i for i,p in enumerate(team) if p.species=="Salamence")
    team[i]=SetBlock(SETS[name])
    return stringify(tuple(team))

def recent_opponent():
    data=json.loads(REG.read_text(encoding="utf8"))
    records=data["teams"][1]["sets"]
    sets=[registered_set(s) for s in records]
    if len(sets)!=6 or any(s is None for s in sets):
        raise RuntimeError("Full registered winner #2 is unavailable")
    p=OUT/"registered-recent-winner-2.txt"
    p.write_text(stringify(tuple(sets)),encoding="utf8")
    return p

def log_mega_distribution(result):
    """Optional evidence from protocol replay logs for the dual Mega roster.

    Logs are separate from population megaEvolvedIn: the latter is any Mega,
    not necessarily Golisopod. Count only if protocol reveals the species.
    """
    out={"retained":len(result.get("logs",[])),"mega_golisopod":0,"mega_salamence":0,"other":0}
    for row in result.get("logs",[]):
        lines=row.get("log",[])
        hay="\n".join(str(x) for x in lines)
        for line in hay.splitlines():
            if "|-mega|" in line or "|-formechange|" in line:
                if re.search("Golisopod",line,re.I):out["mega_golisopod"]+=1
                elif re.search("Salamence",line,re.I):out["mega_salamence"]+=1
                else:out["other"]+=1
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={"status":"running","started_at":datetime.now(timezone.utc).isoformat(),
      "engine":"09d59984631dd2a45fb21700970c65ee24cf7d0f","policy":POLICY,
      "field_per_seed":FIELD_N,"seeds":SEEDS,"matchup_games":MATCH_N,"lookahead_games":LOOKAHEAD_N,
      "holdout_games":HOLDOUT_N,
      "user_requirement":"No base Salamence; Mega Golisopod remains the primary Mega"}
    save("manifest.json",manifest)
    try:
        preview=ENGINE/"src/engine/policy/preview.ts"
        if not preview.is_file() or POLICY not in preview.read_text(encoding="utf8"):
            raise RuntimeError("Refusing engine without versioned weather-aware preview")
        policyfile=ROOT/"reports/evolution/weather-preview-policy.json"
        if not policyfile.is_file():raise RuntimeError("Missing source-hash policy manifest")
        original=TEAM.read_text(encoding="utf8")
        if not exclusive_mega_golisopod(parse_team(original)):
            raise RuntimeError("Current team no longer locked to Mega Golisopod")
        opponents={"LAIC published-set champion proxy":LAIC,"Recent registered winner #2":recent_opponent()}
        for name,path in opponents.items():
            v=run_cli("validate",path)
            if v.get("ok") is not True:
                raise RuntimeError("Invalid opponent "+name+": "+str(v.get("problems")))
        candidates={}
        rejected={}
        for name in [BASELINE,*SETS.keys()]:
            paste=variant(original,name)
            path=OUT/("team-"+re.sub("[^a-z0-9]+","-",name.lower()).strip("-")+".txt")
            path.write_text(paste,encoding="utf8")
            v=run_cli("validate",path)
            save("validate-"+path.stem+".json",v)
            eligible=(name!=BASELINE and name!=REFERENCE and exclusive_mega_golisopod(parse_team(paste)))
            if v.get("ok") is True and (name in (BASELINE,REFERENCE) or eligible):
                candidates[name]={"path":path,"eligible":eligible}
            else:
                rejected[name]=v.get("problems",v) if v.get("ok") is not True else "Additional Mega Stone or theme violation"
        manifest["rejected"]=rejected
        manifest["valid"]={n:x["eligible"] for n,x in candidates.items()}
        save("manifest.json",manifest)
        eligible=[name for name,x in candidates.items() if x["eligible"]]
        if len(eligible)<3 or "Staraptor | balanced Intimidate/Tailwind" not in eligible or "Incineroar | defensive pivot" not in eligible:
            raise RuntimeError("Not enough independent legal candidate roles: "+str(rejected))
        training={}
        for i,(name,desc) in enumerate(candidates.items()):
            path=desc["path"]
            wins=losses=ties=0
            salbring=[];goli=[];mega=[]
            for seed in SEEDS:
                print("FIELD",name,seed,flush=True)
                sim=run_cli("field",path,"--n",FIELD_N,"--player","heuristic","--seed",seed)
                rr=rate(sim,"winRate",FIELD_N)
                wins+=rr["wins"];losses+=rr["losses"];ties+=rr["ties"]
                salbring.append(selected_rate(sim,"Salamence"))
                goli.append(selected_rate(sim,"Golisopod"))
                mega.append(mega_rate(sim))
                save("field-"+str(i)+"-"+seed+".json",sim)
            matches={}
            for j,(oname,op) in enumerate(opponents.items()):
                print("VS",name,oname,flush=True)
                sim=run_cli("sim",path,op,"--n",MATCH_N,
                            "--player","heuristic","--seed","goli-sala-replace|"+oname,"--logs",12)
                rr=rate(sim,"winRateA",MATCH_N)
                matches[oname]={**rr,
                    "goli_brought":selected_rate(sim,"Golisopod"),
                    "mega_rate":mega_rate(sim),
                    "observed_mega":log_mega_distribution(sim)}
                save("vs-"+str(i)+"-"+str(j)+".json",sim)
            n=wins+losses+ties
            score=0.60*(wins+ties/2)/n+0.20*matches["LAIC published-set champion proxy"]["rate"]+0.20*matches["Recent registered winner #2"]["rate"]
            training[name]={"field":{"wins":wins,"losses":losses,"ties":ties,"n":n,
                                     "rate":(wins+ties/2)/n},
                            "goli_brought":sum(goli)/len(goli),
                            "mega_activated":sum(mega)/len(mega),
                            "sal_brought":sum(salbring)/len(salbring),
                            "matchups":matches,"score":score,
                            "eligible":desc["eligible"]}
            save("training.json",training)
            print("TRAINING",name,pct(score),flush=True)
        # References are NEVER eligible: user specifically does not want base Salamence,
        # and two Mega Stones make Golisopod's actual Mega usage non-guaranteed.
        ranked=sorted(eligible,key=lambda n:(-training[n]["score"],n))
        winner=ranked[0]
        runner=ranked[1]
        manifest["frozen_winner"]=winner
        manifest["eligible_order"]=ranked
        save("manifest.json",manifest)
        (OUT/"best.txt").write_text(candidates[winner]["path"].read_text(encoding="utf8"),encoding="utf8")
        lookahead={}
        for name in (winner,runner):
            lookahead[name]={}
            for j,(oname,op) in enumerate(opponents.items()):
                print("SEARCH",name,oname,flush=True)
                sim=run_cli("sim",candidates[name]["path"],op,
                            "--n",LOOKAHEAD_N,"--player","search",
                            "--seed","goli-sala-replace|lookahead|"+oname,"--logs",4)
                lookahead[name][oname]=rate(sim,"winRateA",LOOKAHEAD_N)
                save("search-"+str(ranked.index(name))+"-"+str(j)+".json",sim)
        save("lookahead.json",lookahead)
        holdout={}
        for name in dict.fromkeys([winner,runner,BASELINE,REFERENCE]):
            if name not in candidates:continue
            print("HOLDOUT",name,flush=True)
            sim=run_cli("field",candidates[name]["path"],"--n",HOLDOUT_N,
                        "--player","heuristic","--seed","goli-sala-replace|reserved-holdout")
            holdout[name]={**rate(sim,"winRate",HOLDOUT_N),
                           "goli_brought":selected_rate(sim,"Golisopod"),
                           "mega_activated":mega_rate(sim)}
            save("holdout-"+re.sub("[^a-z0-9]+","-",name.lower()).strip("-")+".json",sim)
        save("holdout.json",holdout)
        lines=["# Mega Golisopod without base Salamence","",
          "**User requirement:** no ordinary Salamence. Either Mega Salamence or a different Pokémon.",
          "Eligible final teams have Golisopite as their **only** Mega Stone.",
          "The Mega Salamence two-stone version and inherited base-Salamence version",
          "were tested as **references only**, never eligible to win.",
          "**Results are pinned weather-aware M-C bot simulations, not human win rates.**",
          "LAIC champion opponent has published moves/items/natures but inferred Stat Points.",
          "Composite selection before holdout: 60% tournament field + 20% LAIC proxy + 20% registered winner #2.",
          "", "## Training and actual Mega activation","",
          "| Variant | Eligible | Field W/N | Rate | LAIC | Winner #2 | Golisopod brought | Mega activated | Composite |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for name,row in sorted(training.items(),key=lambda a:-a[1]["score"]):
            f=row["field"]
            lines.append(f"| {name} | {'yes' if row['eligible'] else 'reference'} | "+
                         f"{f['wins']}/{f['n']} | {pct(f['rate'])} | "+
                         f"{pct(row['matchups']['LAIC published-set champion proxy']['rate'])} | "+
                         f"{pct(row['matchups']['Recent registered winner #2']['rate'])} | "+
                         f"{pct(row['goli_brought'])} | "+
                         (pct(row['mega_activated']) if row['eligible'] else 'any Mega, cannot isolate Goli')+
                         f" | {pct(row['score'])} |")
        lines.extend(["", "**Frozen winner before holdout:** "+winner,"",
                      "## Independent 320-game holdout","",
                      "| Variant | Wins/N | Rate | Golisopod brought | Mega activated |",
                      "|---|---:|---:|---:|---:|"])
        for name,row in holdout.items():
            lines.append(f"| {name} | {row['wins']}/{row['n']} | {pct(row['rate'])} | "+
                         f"{pct(row['goli_brought'])} | "+
                         (pct(row['mega_activated']) if name not in (BASELINE,REFERENCE) else 'Goli only' if name==BASELINE else 'any Mega')+" |")
        lines.extend(["", "## Lookahead AI (small samples)","",
                      "| Variant | Opponent | Wins/N | Rate |",
                      "|---|---|---:|---:|"])
        for name,items in lookahead.items():
            for opp,rr in items.items():
                lines.append(f"| {name} | {opp} | {rr['wins']}/{rr['n']} | {pct(rr['rate'])} |")
        lines.extend(["", "## Full legal Showdown paste", "", "~~~",
                      candidates[winner]["path"].read_text(encoding="utf8").rstrip(),
                      "~~~", "", "## Rejected sets", "~~~json",json.dumps(rejected,indent=2),"~~~",
                      "", "Scope: M-C bot simulated, not a promise of M-D legality or tournament success.",
                      "Other five species, items, moves and Stat Points were unchanged.",""])
        (OUT/"summary.md").write_text("\n".join(lines),encoding="utf8")
        manifest["status"]="completed"
        manifest["completed_at"]=datetime.now(timezone.utc).isoformat()
        save("manifest.json",manifest)
        print("\n".join(lines),flush=True)
    except Exception as exc:
        manifest["status"]="failed";manifest["error"]=str(exc)
        save("manifest.json",manifest)
        (OUT/"summary.md").write_text("# Salamence replacement audit failed\n\nNo results claimed.\n"+str(exc),encoding="utf8")
        traceback.print_exc()
        sys.exit(1)

if __name__=="__main__":
    main()
