#!/usr/bin/env python3
"""Last move-slot audit for the frozen Tyranitar/Golisopod champion.

Uses the weather-corrected preview policy, never upstream preview. All four
variants differ ONLY in Archaludon's first move. Selection uses predeclared
training score; independent final holdout is never used to reselect.
"""
from __future__ import annotations
import json
import sys
import traceback
from datetime import datetime,timezone
from pathlib import Path
from evolve import ROOT,ENGINE,run_cli,checked_rate,parse_team,stringify,locked,registered_set

OUT=ROOT/"reports/final-arch-move"
ROOT_TEAM=ROOT/"teams/evolution-best-nov27.txt"
LAIC=ROOT/"teams/benchmark-laic-champion-published-proxy.txt"
SECOND=ROOT/"data/latest-teams.json"
MOVES=("Electro Shot","Flash Cannon","Thunderbolt","Snarl")
FIELD_SEEDS=("final-arch-2026-A","final-arch-2026-B")
FIELD_GAMES=180
MATCH_GAMES=80
STRONG_GAMES=16
HOLDOUT_GAMES=320
MARKER="POKEPROTOCOL_WEATHER_PREVIEW_V2"

def save(n,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/n).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf8")

def pct(x):
    return f"{100*x:.1f}%"

def r(result,key,n):
    w=checked_rate(result,key,n)
    return {k:w.get(k) for k in ("wins","losses","ties","n","rate","ci95")}

def bring(result,name):
    side=result.get("side",result.get("a",{}))
    return next((x["brought"] for x in side.get("bringRate",[])
                 if x.get("species")==name),0)

def replace_electro(team,move):
    parts=list(parse_team(team))
    idx=next(i for i,x in enumerate(parts) if x.species=="Archaludon")
    s=parts[idx].text
    if s.count("- Electro Shot")!=1: raise RuntimeError("No unique Electro Shot")
    parts[idx]=type(parts[idx])(s.replace("- Electro Shot","- "+move))
    return stringify(tuple(parts))

def second_winner():
    data=json.loads(SECOND.read_text(encoding="utf8"))
    row=data["teams"][1]
    sets=[registered_set(x) for x in row["sets"]]
    if len(sets)!=6 or any(x is None for x in sets):
        raise RuntimeError("Recent winner 2 incomplete registered set")
    p=OUT/"second-registered-winner.txt"
    p.write_text(stringify(tuple(sets)),encoding="utf8")
    return p

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={"status":"running","started_at":datetime.now(timezone.utc).isoformat(),
              "engine":"09d59984631dd2a45fb21700970c65ee24cf7d0f",
              "policy":MARKER,"field_games_per_seed":FIELD_GAMES,
              "field_seeds":FIELD_SEEDS,"targeted_games":MATCH_GAMES,
              "strong_games":STRONG_GAMES,"holdout":HOLDOUT_GAMES}
    save("manifest.json",manifest)
    try:
        preview=ENGINE/"src/engine/policy/preview.ts"
        if not preview.exists() or MARKER not in preview.read_text(encoding="utf8"):
            raise RuntimeError("Corrected team preview not installed")
        original=ROOT_TEAM.read_text(encoding="utf8")
        if not locked(parse_team(original)):
            raise RuntimeError("Frozen champion lacks Mega Golisopod")
        opponents={"LAIC published-set proxy":LAIC,
                   "Recent tournament winner 2":second_winner()}
        for name,path in opponents.items():
            verdict=run_cli("validate",path)
            if verdict.get("ok") is not True:
                raise RuntimeError("Invalid benchmark "+name+": "+str(verdict.get("problems")))
        variants={}
        for move in MOVES:
            path=OUT/("arch-"+move.replace(" ","-").lower()+".txt")
            path.write_text(replace_electro(original,move),encoding="utf8")
            v=run_cli("validate",path)
            save("validate-"+move.replace(" ","-").lower()+".json",v)
            if v.get("ok") is not True:
                raise RuntimeError("Move option "+move+" illegal: "+str(v.get("problems")))
            variants[move]=path
        scored={}
        for move,path in variants.items():
            nw=nl=nt=0
            bring_arch=[]
            bring_goli=[]
            for seed in FIELD_SEEDS:
                print("FIELD",move,seed,flush=True)
                f=run_cli("field",path,"--n",FIELD_GAMES,
                          "--player","heuristic","--seed",seed)
                w=r(f,"winRate",FIELD_GAMES)
                nw+=w["wins"];nl+=w["losses"];nt+=w["ties"]
                bring_arch.append(bring(f,"Archaludon"))
                bring_goli.append(bring(f,"Golisopod"))
                save("field-"+move.replace(" ","-")+"-"+seed+".json",f)
            field_rate=(nw+0.5*nt)/(nw+nl+nt)
            mresults={}
            for oname,opp in opponents.items():
                print("MATCHUP",move,oname,flush=True)
                sim=run_cli("sim",path,opp,"--n",MATCH_GAMES,
                            "--player","heuristic","--seed","arch-final|"+oname,"--logs",3)
                mresults[oname]=r(sim,"winRateA",MATCH_GAMES)
                save("match-"+move.replace(" ","-")+"-"+oname.replace(" ","-")+".json",sim)
            score=(0.70*field_rate+
                   0.15*mresults["LAIC published-set proxy"]["rate"]+
                   0.15*mresults["Recent tournament winner 2"]["rate"])
            scored[move]={"score":score,"field_rate":field_rate,"wins":nw,
                          "losses":nl,"ties":nt,"n":nw+nl+nt,
                          "archaludon_bring":sum(bring_arch)/len(bring_arch),
                          "golisopod_bring":sum(bring_goli)/len(bring_goli),
                          "matches":mresults}
            save("training.json",scored)
            print("SCORE",move,pct(score),flush=True)
        ranked=sorted(scored,key=lambda m:(-scored[m]["score"],MOVES.index(m)))
        # Predeclared uncertainty guard: if an alternative is within two
        # points of Electro Shot on the training composite, retain Electro Shot.
        winner=ranked[0]
        if scored["Electro Shot"]["score"] >= scored[winner]["score"]-0.02:
            winner="Electro Shot"
        manifest["selected_move"]=winner
        manifest["ranked"]=ranked
        save("manifest.json",manifest)
        (OUT/"best.txt").write_text(variants[winner].read_text(encoding="utf8"),encoding="utf8")
        strong={}
        for move in list(dict.fromkeys([winner, "Electro Shot"])):
            strong[move]={}
            for name,opp in opponents.items():
                print("LOOKAHEAD",move,name,flush=True)
                sim=run_cli("sim",variants[move],opp,"--n",STRONG_GAMES,
                            "--player","search","--seed","arch-final-strong|"+name,"--logs",3)
                strong[move][name]=r(sim,"winRateA",STRONG_GAMES)
                save("strong-"+move.replace(" ","-")+"-"+name.replace(" ","-")+".json",sim)
        save("lookahead.json",strong)
        holdout={}
        for move in list(dict.fromkeys([winner,"Electro Shot"])):
            print("HOLDOUT",move,flush=True)
            f=run_cli("field",variants[move],"--n",HOLDOUT_GAMES,
                      "--player","heuristic","--seed","final-arch-HOLDOUT-C")
            holdout[move]={**r(f,"winRate",HOLDOUT_GAMES),
                           "golisopod_bring":bring(f,"Golisopod"),
                           "archaludon_bring":bring(f,"Archaludon")}
            save("holdout-"+move.replace(" ","-")+".json",f)
        save("holdout.json",holdout)
        lines=["# Archaludon move-slot final validation","",
               "Four legal alternatives; the other five Pokémon and every stat, item and",
               "ability are unchanged. Uses pinned corrected M-C simulator.",
               "Data are bot simulations, NOT human tournament results.",
               "Training score is preregistered as 70% field + 15% LAIC published-set",
               "proxy + 15% recent full-OTS winner #2. The LAIC Stat Points remain inferred.",
               "Move selected before a different holdout seed; a 2pp score tie",
               "defaults to the original Electro Shot as a conservative guard.","",
               "## Matched-seed move comparison","",
               "| Move | Field W/N | Field rate | Arch brought | Golisopod brought | Composite score |",
               "|---|---:|---:|---:|---:|---:|"]
        for move in ranked:
            row=scored[move]
            lines.append(f"| {move} | {row['wins']}/{row['n']} | {pct(row['field_rate'])} | "+
                         f"{pct(row['archaludon_bring'])} | {pct(row['golisopod_bring'])} | {pct(row['score'])} |")
        lines.extend(["","**Selected first move: "+winner+"**","",
                      "## Major full-six matchup comparisons","",
                      "| Move | Opponent | Fast W/N | Win rate |","|---|---|---:|---:|"])
        for move in ranked:
            for oname,q in scored[move]["matches"].items():
                lines.append(f"| {move} | {oname} | {q['wins']}/{q['n']} | {pct(q['rate'])} |")
        lines.extend(["","## Lookahead (small sample, diagnostic)","",
                      "| Move | Opponent | W/N | Rate |","|---|---|---:|---:|"])
        for move,records in strong.items():
            for oname,q in records.items():
                lines.append(f"| {move} | {oname} | {q['wins']}/{q['n']} | {pct(q['rate'])} |")
        lines.extend(["","## Fresh independent holdout","",
                      "| Move | W/N | Rate | 95% CI |","|---|---:|---:|---|"])
        for move,q in holdout.items():
            ci=q["ci95"] or [0,1]
            lines.append(f"| {move} | {q['wins']}/{q['n']} | {pct(q['rate'])} | {pct(ci[0])}–{pct(ci[1])} |")
        lines.extend(["","## Final Showdown paste","",
                      "~~~",variants[winner].read_text(encoding="utf8").rstrip(),"~~~","",
                      "## Limitations","",
                      "- All move changes alter the preview policy's bring-four choices too;",
                      "  Archaludon's modest usage may make overall ratings insensitive to its fourth move.",
                      "- Opponent win rates, especially 16-game lookahead tests, are uncertain.",
                      "- No claim of human-tournament win rate or M-D legality.",
                      "- Team selected before fresh holdout, not post hoc.",""])
        (OUT/"summary.md").write_text("\n".join(lines),encoding="utf8")
        manifest["status"]="completed"
        manifest["completed_at"]=datetime.now(timezone.utc).isoformat()
        save("manifest.json",manifest)
        print("\n".join(lines),flush=True)
    except Exception as exc:
        manifest["status"]="failed"
        manifest["error"]=str(exc)
        save("manifest.json",manifest)
        (OUT/"summary.md").write_text("# Final Archaludon move check failed\n\nNo results claimed.\n"+str(exc))
        traceback.print_exc()
        sys.exit(1)

if __name__=="__main__":
    main()
