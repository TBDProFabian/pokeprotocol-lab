#!/usr/bin/env python3
"""Item-only Salamence audit, with explicit allied Sand Stream exposure.

The previous six-way experiment changed Salamence's *move and item* together,
so it could not isolate Focus Sash from coverage differences. This study
preserves all six Pokemon and all 24 moves and changes ONLY Salamence's item.
Tests current M-C legality and saves representative full logs to diagnose
sash activation, sand-chip failures, and whether Salamence/Tyranitar were
actually selected. The tournament-field holdout is strictly independent.
"""
from __future__ import annotations
import json
import re
import sys
import traceback
from datetime import datetime,timezone
from pathlib import Path
from evolve import ROOT,ENGINE,SetBlock,parse_team,stringify,exclusive_mega_golisopod,run_cli,checked_rate,registered_set

OUT=ROOT/"reports/salamence-item-only"
SEED_TEAM=ROOT/"teams/golisopod-current.txt"
LAIC=ROOT/"teams/benchmark-laic-champion-published-proxy.txt"
RECENT=ROOT/"data/latest-teams.json"
POLICY="POKEPROTOCOL_WEATHER_PREVIEW_V2"
ITEMS=("Focus Sash","Sitrus Berry","Haban Berry","Yache Berry")
SEEDS=("sash-sand-isolation-1","sash-sand-isolation-2")
FIELD_PER_SEED=180
TARGETED_N=140
LOOKAHEAD_N=16
HOLDOUT_N=320

def save(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf8")

def pct(x):
    return f"{100*x:.1f}%"

def rate(output,key,n):
    x=checked_rate(output,key,n)
    return {k:x.get(k) for k in ("wins","losses","ties","n","rate","ci95")}

def bring(output,species,key="a"):
    x=output.get(key,output.get("side",{}))
    return next((y.get("brought") for y in x.get("bringRate",[]) if y.get("species")==species),0)

def change_item(paste,item):
    xs=list(parse_team(paste))
    idx=next(i for i,x in enumerate(xs) if x.species=="Salamence")
    lines=xs[idx].text.splitlines()
    if lines[0]!="Salamence @ Focus Sash":
        raise RuntimeError("Canonical team changed; refusing item-only audit")
    lines[0]="Salamence @ "+item
    xs[idx]=SetBlock("\n".join(lines))
    team=tuple(xs)
    if not exclusive_mega_golisopod(team):
        raise RuntimeError("Only-Golisopite theme broken")
    return stringify(team)

def second_opponent():
    data=json.loads(RECENT.read_text(encoding="utf8"))
    if len(data.get("teams",[]))<2:raise RuntimeError("Missing second OTS registered opponent")
    sets=[registered_set(s) for s in data["teams"][1]["sets"]]
    if len(sets)!=6 or any(s is None for s in sets):raise RuntimeError("Incomplete recent registered winner")
    path=OUT/"registered-opponent-2.txt"
    path.write_text(stringify(tuple(sets)),encoding="utf8")
    return path

def inspect_logs(output):
    """Count game-level evidence, not every perspective-duplicated protocol row."""
    logs=output.get("logs",[])
    evidence={"retained_game_logs":len(logs),
              "sash_activation_games":0,
              "our_salamence_sand_damage_games":0,
              "our_tyranitar_sand_starts":0,
              "our_salamence_visible_games":0,
              "our_tyranitar_visible_games":0}
    for i,game in enumerate(logs):
        side="p1" if i%2==0 else "p2"
        events=[str(row) for row in game.get("log",[])]
        def any_line(regex):
            return any(re.search(regex,row,re.I) for row in events)
        if any_line(r"\|-enditem\|"+side+r"[ab]: Salamence\|Focus Sash"):
            evidence["sash_activation_games"]+=1
        if any_line(r"\|-damage\|"+side+r"[ab]: Salamence\|.*\[from\] Sandstorm"):
            evidence["our_salamence_sand_damage_games"]+=1
        if any_line(r"\|-weather\|Sandstorm\|\[from\] ability: Sand Stream\|\[of\] "+side+r"[ab]: Tyranitar"):
            evidence["our_tyranitar_sand_starts"]+=1
        if any_line(r"\|(switch|drag)\|"+side+r"[ab]: Salamence"):
            evidence["our_salamence_visible_games"]+=1
        if any_line(r"\|(switch|drag)\|"+side+r"[ab]: Tyranitar"):
            evidence["our_tyranitar_visible_games"]+=1
    return evidence

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={"status":"running","started_at":datetime.now(timezone.utc).isoformat(),
      "engine_sha":"09d59984631dd2a45fb21700970c65ee24cf7d0f",
      "policy":POLICY,"changed_variable":"Salamence held item ONLY; 24 moves and all Stat Points identical",
      "items":ITEMS,"field_seeds":SEEDS,"field_games_per_seed":FIELD_PER_SEED,
      "targeted_games":TARGETED_N,"holdout_games":HOLDOUT_N}
    save("manifest.json",manifest)
    try:
        policy=ENGINE/"src/engine/policy/preview.ts"
        if not policy.is_file() or POLICY not in policy.read_text(encoding="utf8"):
            raise RuntimeError("Missing versioned weather-aware M-C preview")
        if not (ROOT/"reports/evolution/weather-preview-policy.json").is_file():
            raise RuntimeError("Missing preview policy manifest")
        original=SEED_TEAM.read_text(encoding="utf8")
        contenders={}
        for item in ITEMS:
            paste=change_item(original,item)
            path=OUT/("item-"+item.replace(" ","-").lower()+".txt")
            path.write_text(paste,encoding="utf8")
            q=run_cli("validate",path)
            save("validation-"+item.replace(" ","-").lower()+".json",q)
            if q.get("ok") is not True:
                raise RuntimeError("M-C legality failed for "+item+": "+str(q.get("problems")))
            contenders[item]=path
        opponents={"LAIC published-set proxy (Tyranitar plus Salamence benchmark)":LAIC,
                   "Recent registered tournament winner #2":second_opponent()}
        for name,p in opponents.items():
            q=run_cli("validate",p)
            if q.get("ok") is not True:
                raise RuntimeError("Opponent invalid "+name+": "+str(q.get("problems")))
        results={}
        for item,path in contenders.items():
            print("FIELD",item,flush=True)
            wins=losses=ties=0
            brought_s=[]
            brought_t=[]
            for seed in SEEDS:
                f=run_cli("field",path,"--n",FIELD_PER_SEED,"--player","heuristic","--seed",seed)
                w=rate(f,"winRate",FIELD_PER_SEED)
                wins+=w["wins"];losses+=w["losses"];ties+=w["ties"]
                brought_s.append(bring(f,"Salamence","side"))
                brought_t.append(bring(f,"Tyranitar","side"))
                save("field-"+item.replace(" ","-").lower()+"-"+seed+".json",f)
            n=wins+losses+ties
            matches={}
            for j,(opname,opp) in enumerate(opponents.items()):
                print("VS",item,opname,flush=True)
                s=run_cli("sim",path,opp,"--n",TARGETED_N,"--player","heuristic",
                          "--seed","sash-sand-item-only|"+str(j),"--logs",60)
                w=rate(s,"winRateA",TARGETED_N)
                broughtS=bring(s,"Salamence")
                broughtT=bring(s,"Tyranitar")
                matches[opname]={**w,"sal_bring":broughtS,"ttar_bring":broughtT,
                    "both_brought_confirmed":broughtS==1 and broughtT==1,
                    "representative_log_events":inspect_logs(s)}
                save("versus-"+item.replace(" ","-").lower()+"-"+str(j)+".json",s)
            # The LAIC pair is an explicit stress environment for simultaneous
            # Salamence/Tyranitar. We only describe it as guaranteed pair if
            # BOTH bring rates are 1.0, otherwise we report marginals honestly.
            score=(0.55*(wins+ties/2)/n +
                   0.30*matches[next(iter(opponents))]["rate"]+
                   0.15*matches[list(opponents)[1]]["rate"])
            results[item]={"wins":wins,"losses":losses,"ties":ties,"n":n,
               "field_rate":(wins+ties/2)/n,
               "sal_bring":sum(brought_s)/len(brought_s),
               "ttar_bring":sum(brought_t)/len(brought_t),
               "targeted":matches,"score":score}
            save("training.json",results)
            print("SCORE",item,pct(score),flush=True)
        order=sorted(ITEMS,key=lambda x:(-results[x]["score"],ITEMS.index(x)))
        chosen=order[0]
        manifest["training_winner"]=chosen
        save("manifest.json",manifest)
        (OUT/"best.txt").write_text(contenders[chosen].read_text(encoding="utf8"),encoding="utf8")
        strong={}
        for item in list(dict.fromkeys([chosen,"Focus Sash"])):
            strong[item]={}
            for j,(oname,op) in enumerate(opponents.items()):
                s=run_cli("sim",contenders[item],op,"--n",LOOKAHEAD_N,
                          "--player","search","--seed","sash-sand|lookahead|"+str(j),"--logs",4)
                strong[item][oname]=rate(s,"winRateA",LOOKAHEAD_N)
                save("lookahead-"+item.replace(" ","-").lower()+"-"+str(j)+".json",s)
        save("lookahead.json",strong)
        held={}
        for item in list(dict.fromkeys([chosen,"Focus Sash"])):
            f=run_cli("field",contenders[item],"--n",HOLDOUT_N,"--player","heuristic",
                      "--seed","sash-sand|reserved-HOLDOUT-2026")
            held[item]={**rate(f,"winRate",HOLDOUT_N),
                "sal_bring":bring(f,"Salamence","side"),
                "ttar_bring":bring(f,"Tyranitar","side")}
            save("holdout-"+item.replace(" ","-").lower()+".json",f)
        save("holdout.json",held)
        lines=["# Focus Sash versus allied Sand Stream: one-variable analysis","",
          "Corrected-preview pinned M-C bot-vs-bot simulator, not human tournament performance.",
          "Every set and benchmark opponent passed the actual M-C team validator.",
          "**Only Salamence's held item was changed. Hyper Voice, Draco Meteor, Tailwind and Protect remain unchanged.**",
          "The previous combined item-and-move ablation could not isolate the Focus Sash choice.",
          "Training score fixed in advance: 55% tournament field, 30% LAIC champion published-set proxy, 15% registered winner #2.",
          "The LAIC proxy has inferred Stat Points, not an exact official OTS.",
          "All variants use the same opponent-sampling seeds and weather-preview policy.",
          "", "## Item-only results","",
          "| Salamence item | Field W/N | Field rate | LAIC win rate | Both pair brought vs LAIC? | Winner #2 | Composite |",
          "|---|---:|---:|---:|---|---:|---:|"]
        first=list(opponents)[0];second=list(opponents)[1]
        for item in order:
            d=results[item];match=d["targeted"]
            pair=match[first]
            lines.append(f"| {item} | {d['wins']}/{d['n']} | {pct(d['field_rate'])} | "+
               f"{pct(pair['rate'])} | {('yes' if pair['both_brought_confirmed'] else 'not guaranteed')} "+
               f"(Sal {pct(pair['sal_bring'])}, Ttar {pct(pair['ttar_bring'])}) | "+
               f"{pct(match[second]['rate'])} | {pct(d['score'])} |")
        lines += ["","## Visible weather and Sash activation in logged games","",
          "**Game-level evidence from the first 60 games per item/benchmark.**",
          "When both bring rates are less than 100%, these logs do NOT establish full joint selected-four rates.",
          "| Item | Benchmark | Logs | Sash triggered | Salamence sand-chip observed | Our Tyranitar activated sand |",
          "|---|---|---:|---:|---:|---:|"]
        for item in order:
            for opp,match in results[item]["targeted"].items():
                e=match["representative_log_events"]
                lines.append(f"| {item} | {opp} | {e['retained_game_logs']} | "+
                  f"{e['sash_activation_games']} | {e['our_salamence_sand_damage_games']} | "+
                  f"{e['our_tyranitar_sand_starts']} |")
        lines += ["","**Training winner fixed before holdout:** "+chosen,"",
          "## Lookahead-AI check (small samples)","",
          "| Item | Opponent | W/N | Rate |","|---|---|---:|---:|"]
        for item,opps in strong.items():
            for opp,w in opps.items():
                lines.append(f"| {item} | {opp} | {w['wins']}/{w['n']} | {pct(w['rate'])} |")
        lines += ["","## Independent 320-battle field holdout","",
          "| Item | W/N | Rate | Salamence brought | Tyranitar brought |",
          "|---|---:|---:|---:|---:|"]
        for item,d in held.items():
            lines.append(f"| {item} | {d['wins']}/{d['n']} | {pct(d['rate'])} | "+
               f"{pct(d['sal_bring'])} | {pct(d['ttar_bring'])} |")
        lines += ["","## Tactical interpretation","",
          "- Focus Sash activates only if Salamence is at full HP when hit by a potentially fatal direct attack.",
          "- Sandstorm end-turn damage removes the full-HP prerequisite for future turns, even if the item is still held.",
          "- It may still activate on the first turn before sand chip, or when Tyranitar is not brought.",
          "- A better overall win rate is not proof that Focus Sash works well *during sand*.",
          "- Compare the item-only controls above; do not confound item and attack changes again.",
          "- The champion is frozen from the training set and the holdout is diagnostic only.",
          "", "## Training-selected full Showdown paste", "",
          "~~~",contenders[chosen].read_text(encoding="utf8").rstrip(),"~~~",""]
        (OUT/"summary.md").write_text("\n".join(lines),encoding="utf8")
        manifest["status"]="completed"
        manifest["completed_at"]=datetime.now(timezone.utc).isoformat()
        save("manifest.json",manifest)
        print("\n".join(lines),flush=True)
    except Exception as ex:
        manifest["status"]="failed"
        manifest["error"]=str(ex)
        save("manifest.json",manifest)
        (OUT/"summary.md").write_text("# Focus Sash / sand item-only audit failed\n\nNo results claimed.\n"+str(ex))
        traceback.print_exc()
        sys.exit(1)

if __name__=="__main__":
    main()
