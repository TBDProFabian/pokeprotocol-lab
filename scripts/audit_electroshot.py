#!/usr/bin/env python3
"""Controlled, reproducible move ablation with pinned Champions Lab (Reg M-C)."""
from __future__ import annotations
import json
import traceback
from pathlib import Path
from datetime import datetime, timezone
from evolve import ROOT, parse_team, stringify, run_cli, checked_rate

OUT = ROOT / "reports/electroshot-audit"
WINNER = ROOT / "teams/evolution-best-nov27.txt"
ORIGINAL = ROOT / "teams/golisopod-current.txt"
MOVES = ("Electro Shot", "Flash Cannon", "Thunderbolt", "Snarl", "Body Press")
SEEDS = ("electro-ablation-2026-A", "electro-ablation-2026-B")
PROXIES = {
 "LAIC rain (six-species proxy)": ROOT / "teams/benchmark-laic-rain-proxy.txt",
 "Gdansk sand (six-species proxy)": ROOT / "teams/benchmark-gdansk-sand-proxy.txt"
}

def edit_move(paste: str, move: str) -> str:
    team = list(parse_team(paste))
    for i,p in enumerate(team):
        if p.species == "Archaludon":
            lines = p.text.splitlines()
            assert lines.count("- Electro Shot") == 1
            lines[lines.index("- Electro Shot")] = "- " + move
            team[i] = type(p)("\n".join(lines))
            return stringify(tuple(team))
    raise ValueError("No Archaludon in team")

def swap_weather(paste: str) -> str:
    team = list(parse_team(paste))
    pelipper = next(s for s in parse_team(ORIGINAL.read_text()) if s.species=="Pelipper")
    i = next(i for i,p in enumerate(team) if p.species=="Tyranitar")
    team[i] = pelipper
    return stringify(tuple(team))

def save(name: str, obj) -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf8")

def rate(wins, ties, n):
    return (wins+ties/2)/n

def brought(result, species):
    return next((r.get("brought",0) for r in result.get("side",{}).get("bringRate",[])
                 if r["species"]==species), 0)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest = {"status":"running","started_at":datetime.now(timezone.utc).isoformat(),
                "field_games_per_variant":400,"seeds":SEEDS,"proxy_games":80,
                "search_games":16,"format":"gen9championsvgc2026regmc"}
    save("manifest.json",manifest)
    try:
        main_team=WINNER.read_text()
        rain_team=swap_weather(main_team)
        candidates = {"Sand | "+m:edit_move(main_team,m) for m in MOVES}
        for m in ("Electro Shot","Flash Cannon"):
            candidates["Rain | "+m]=edit_move(rain_team,m)
        paths={}
        rejected={}
        for name,paste in candidates.items():
            short=name.replace(" | ","-").replace(" ","-").lower()
            path=OUT/("team-"+short+".txt")
            path.write_text(paste,encoding="utf8")
            verdict=run_cli("validate",path)
            save("validate-"+short+".json",verdict)
            if verdict.get("ok") is True:
                paths[name]=path
            else:
                rejected[name]=verdict.get("problems",verdict)
        assert "Sand | Electro Shot" in paths and "Sand | Flash Cannon" in paths, "Essential versions failed legality"
        rows={}
        for name,path in paths.items():
            wins=losses=ties=0
            arch=[]
            ttar=[]
            for seed in SEEDS:
                print("FIELD",name,seed,flush=True)
                result=run_cli("field",path,"--n",200,"--player","heuristic","--seed",seed)
                wr=checked_rate(result,"winRate",200)
                wins+=wr["wins"];losses+=wr["losses"];ties+=wr["ties"]
                arch.append(brought(result,"Archaludon"))
                ttar.append(brought(result,"Tyranitar"))
                save("field-"+name.replace(" | ","-").replace(" ","-").lower()+"-"+seed+".json",result)
            n=wins+losses+ties
            rows[name]={"wins":wins,"losses":losses,"ties":ties,"n":n,
                        "rate":rate(wins,ties,n),"arch_bring":sum(arch)/len(arch),
                        "ttar_bring":sum(ttar)/len(ttar)}
            save("field-summary.json",rows)
            print("RESULT",name,rows[name],flush=True)
        alternative=max((n for n in rows if n.startswith("Sand | ") and n!="Sand | Electro Shot"),
                        key=lambda n:rows[n]["rate"])
        selected=["Sand | Electro Shot",alternative]
        if "Rain | Electro Shot" in paths and "Rain | Flash Cannon" in paths:
            selected.extend(["Rain | Electro Shot","Rain | Flash Cannon"])
        proxy_results={}
        for name in selected:
            proxy_results[name]={}
            for opp,p in PROXIES.items():
                print("PROXY",name,opp,flush=True)
                x=run_cli("sim",paths[name],p,"--n",80,"--player","heuristic",
                          "--seed","electro-ablation-proxy|"+opp,"--logs",6)
                proxy_results[name][opp]=checked_rate(x,"winRateA",80)
                save("proxy-"+name.replace(" | ","-").replace(" ","-").lower()+"-"+
                     ("rain" if "rain" in opp else "sand")+".json",x)
        save("proxy-summary.json",proxy_results)
        strong={}
        for name in selected[:2]:
            print("SEARCH",name,flush=True)
            x=run_cli("sim",paths[name],PROXIES["LAIC rain (six-species proxy)"],
                      "--n",16,"--player","search",
                      "--seed","electro-ablation-lookahead-rain","--logs",4)
            strong[name]=checked_rate(x,"winRateA",16)
            save("search-"+name.replace(" | ","-").replace(" ","-").lower()+".json",x)
        save("lookahead-summary.json",strong)
        p=lambda x:f"{100*x:.1f}%"
        summary=["# Electro Shot audit: Mega Golisopod Evolution V1","",
                 "Real pinned M-C simulator games, NOT real-player tournament results.","",
                 "Change only Archaludon's first move; all other sets stay constant",
                 "within each weather context. Sand is the original evolved winner.",
                 "Rain replaces its Tyranitar with the original team's Pelipper.",
                 "Field games use two independent 200-game seeds, matched across variants.",
                 "Small differences are inconclusive. Opponent teams in targeted tests",
                 "are plausible six-species proxies, NOT champions' verified full sets.","",
                 "## Matched-seed field results","",
                 "| Variant | Wins/N | Rate | Archaludon brought | Tyranitar brought |",
                 "|---|---:|---:|---:|---:|"]
        for name in sorted(rows, key=lambda n:(n.split(" | ")[0],-rows[n]["rate"])):
            r=rows[name]
            summary.append(f"| {name} | {r['wins']}/{r['n']} | {p(r['rate'])} | {p(r['arch_bring'])} | {p(r['ttar_bring'])} |")
        summary.extend(["",f"Post-hoc leading non-Electro Shot alternative: {alternative}.",
                        "This comparison is exploratory and was not selected on an independent holdout.","",
                        "## Weather archetype proxies","",
                        "| Variant | Opponent | Wins/N | Rate |","|---|---|---:|---:|"])
        for name,d in proxy_results.items():
            for opp,wr in d.items():
                summary.append(f"| {name} | {opp} | {wr['wins']}/{wr['n']} | {p(wr['rate'])} |")
        summary.extend(["","## Lookahead AI spot check","",
                        "| Variant | Rain proxy | Rate |","|---|---:|---:|"])
        for name,wr in strong.items():
            summary.append(f"| {name} | {wr['wins']}/{wr['n']} | {p(wr['rate'])} |")
        summary.extend(["","## What this can and cannot tell us","",
                        "- The V1 donor registry has no alternative Archaludon set.",
                        "  Electro Shot persisted through restricted mutation, not demonstrated optimization.",
                        "- Opposing Pelipper rain may activate one-turn Electro Shot even on a sand team.",
                        "- Tyranitar's Sand Stream can switch rain off; actual team preview matters.",
                        "- Changing a move can affect simulated player decisions, including which four are brought.",
                        "- Heuristic and lookahead AI are not evidence of tournament success.",
                        "- Full raw JSON, move logs and legal Showdown pastes are included in the artifact.","",
                        "## Rejected alternatives","",
                        json.dumps(rejected,ensure_ascii=False,indent=2),""])
        (OUT/"summary.md").write_text("\n".join(summary),encoding="utf8")
        manifest.update({"status":"completed","finished_at":datetime.now(timezone.utc).isoformat(),
                         "selected_non_electro_alternative":alternative,"rejected":rejected})
        save("manifest.json",manifest)
        print("\n".join(summary),flush=True)
    except Exception as exc:
        manifest.update({"status":"failed","error":str(exc)})
        save("manifest.json",manifest)
        (OUT/"summary.md").write_text("# Electro Shot audit failed\n\nNo results claimed.\n"+str(exc))
        traceback.print_exc()
        raise

if __name__=="__main__":
    main()
