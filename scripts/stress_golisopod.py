#!/usr/bin/env python3
"""Poképrotocol final validation against full registered sixes and archetype proxies.

Only pinned, weather-preview-corrected M-C simulations. The decision rule is
fixed before the independent holdout. All teams are validated by Showdown.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import traceback
from evolve import ROOT, ENGINE, run_cli, checked_rate, registered_set, parse_team, stringify, locked

OUT = ROOT / "reports" / "golisopod-final"
CHALLENGERS = {
    "V2 evolved": ROOT / "teams" / "golisopod-finalist-v2.txt",
    "V1 Incineroar": ROOT / "teams" / "golisopod-incineroar-nov27.txt",
    "V1 Tyranitar": ROOT / "teams" / "evolution-best-nov27.txt",
    "Original baseline": ROOT / "teams" / "golisopod-current.txt"
}
ARCHETYPES = {
    "LAIC rain-six proxy": ROOT / "teams" / "benchmark-laic-rain-proxy.txt",
    "Gdansk sand-six proxy": ROOT / "teams" / "benchmark-gdansk-sand-proxy.txt"
}
FAST_FIELD = 240
FAST_MATCH = 80
LOOKAHEAD_MATCH = 16
HOLDOUT = 320
FIX = "POKEPROTOCOL_WEATHER_PREVIEW_V2"

def save(name:str, obj) -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf8")

def winner_ots() -> dict[str,Path]:
    data=json.loads((ROOT/"data/latest-teams.json").read_text(encoding="utf8"))
    out={}
    for i, record in enumerate(data.get("teams",[])[:2]):
        sets=[registered_set(s) for s in record.get("sets",[])]
        if len(sets)!=6 or any(s is None for s in sets):
            raise RuntimeError("Latest tournament winner missing complete registered sets")
        name="Recent tournament winner "+str(i+1)
        path=OUT/("registered-winner-"+str(i+1)+".txt")
        path.write_text(stringify(tuple(sets)),encoding="utf8")
        out[name]=path
    if len(out)<2:
        raise RuntimeError("Need two complete recent tournament winners")
    return out

def percent(x:float) -> str:
    return f"{100*x:.1f}%"

def bring(result, species):
    side=result.get("side") or result.get("a") or {}
    return next((row.get("brought") for row in side.get("bringRate",[])
                 if row.get("species")==species),None)

def rate(result, key, n):
    data=checked_rate(result,key,n)
    return {"rate":data["rate"],"wins":data.get("wins"),
            "losses":data.get("losses"),"ties":data.get("ties"),
            "n":data["n"],"ci95":data.get("ci95")}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={"status":"running","started_at":datetime.now(timezone.utc).isoformat(),
              "format":"gen9championsvgc2026regmc",
              "policy":FIX,"field_training":FAST_FIELD,"archetype_games":FAST_MATCH,
              "lookahead_games":LOOKAHEAD_MATCH,"holdout_games":HOLDOUT}
    save("manifest.json",manifest)
    try:
        source=ENGINE/"src/engine/policy/preview.ts"
        if not source.exists() or FIX not in source.read_text(encoding="utf8"):
            raise RuntimeError("Fail closed: corrected preview policy not installed")
        raw_manifest=ROOT/"reports/evolution/weather-preview-policy.json"
        if not raw_manifest.is_file():
            raise RuntimeError("Fail closed: missing pinned preview source hash manifest")
        manifest["weather_policy"]=json.loads(raw_manifest.read_text())
        opponents={**winner_ots(),**ARCHETYPES}
        for name,path in opponents.items():
            v=run_cli("validate",path)
            if v.get("ok") is not True:
                raise RuntimeError("Opponent "+name+" failed legal M-C validation: "+str(v.get("problems")))
        contenders={}
        from_evolution={}
        for name,path in CHALLENGERS.items():
            if not path.exists():
                raise RuntimeError("Missing candidate paste: "+str(path))
            team=parse_team(path.read_text(encoding="utf8"))
            if not locked(team):
                raise RuntimeError(name+" lacks locked Mega Golisopod or unique species")
            verdict=run_cli("validate",path)
            if verdict.get("ok") is not True:
                raise RuntimeError(name+" failed Showdown M-C legality: "+str(verdict.get("problems")))
            from_evolution[name]=team
            key=stringify(team)
            if key not in contenders:
                contenders[key]={"name":name,"path":path,"aliases":[name],"team":team}
            else:
                contenders[key]["aliases"].append(name)
        contenders_list=list(contenders.values())
        print("VALIDATED",len(contenders_list),"unique legal teams",flush=True)
        manifest["contenders"]=[{k:x[k] for k in ("name","aliases")} for x in contenders_list]
        save("manifest.json",manifest)
        training={}
        for i,x in enumerate(contenders_list):
            name=x["name"]
            path=x["path"]
            print("FIELD",name,flush=True)
            f=run_cli("field",path,"--n",FAST_FIELD,"--player","heuristic",
                      "--seed","final-golisopod-2026|FIELD-A")
            fast=rate(f,"winRate",FAST_FIELD)
            save("field-"+str(i)+".json",f)
            fast["golisopod_bring"]=bring(f,"Golisopod")
            fast["archaludon_bring"]=bring(f,"Archaludon")
            matches={}
            for j,(oname,op) in enumerate(opponents.items()):
                print("OPPONENT",name,oname,flush=True)
                m=run_cli("sim",path,op,"--n",FAST_MATCH,"--player","heuristic",
                          "--seed","final-golisopod-2026|MATCH|"+oname,"--logs",2)
                matches[oname]={**rate(m,"winRateA",FAST_MATCH),
                                 "golisopod_bring":bring(m,"Golisopod")}
                save("fast-"+str(i)+"-"+str(j)+".json",m)
            winner_rates=[matches[y]["rate"] for y in opponents if y.startswith("Recent tournament")]
            proxy_rates=[matches[y]["rate"] for y in ARCHETYPES]
            # Premarked training objective; no use of holdout data.
            score=0.60*fast["rate"]+0.25*sum(winner_rates)/len(winner_rates)+0.15*sum(proxy_rates)/len(proxy_rates)
            training[name]={"field":fast,"matches":matches,"score":score,
                            "aliases":x["aliases"],"species":[p.species for p in x["team"]]}
            save("training.json",training)
            print("TRAINING",name,percent(score),flush=True)
        ranked=sorted(training,key=lambda x:(-training[x]["score"],x))
        champion_name=ranked[0]
        finalist_names=ranked[:2]
        manifest["frozen_champion"]=champion_name
        manifest["ranking"]=ranked
        save("manifest.json",manifest)
        champion=next(x for x in contenders_list if x["name"]==champion_name)
        (OUT/"best.txt").write_text(stringify(champion["team"]),encoding="utf8")
        # Strong AI is diagnostic, not an opportunity to reselect the champion.
        lookahead={}
        for name in finalist_names:
            x=next(c for c in contenders_list if c["name"]==name)
            lookahead[name]={}
            for j,(opname,op) in enumerate(opponents.items()):
                print("LOOKAHEAD",name,opname,flush=True)
                m=run_cli("sim",x["path"],op,"--n",LOOKAHEAD_MATCH,
                          "--player","search",
                          "--seed","final-golisopod-2026|STRONG|"+opname,"--logs",3)
                lookahead[name][opname]=rate(m,"winRateA",LOOKAHEAD_MATCH)
                save("strong-"+str(ranked.index(name))+"-"+str(j)+".json",m)
        save("lookahead.json",lookahead)
        # Additional untouched seed, after winner frozen.
        holdout={}
        for name in dict.fromkeys([champion_name,"Original baseline"]):
            x=next((c for c in contenders_list if c["name"]==name),
                   next(c for c in contenders_list if "Original baseline" in c["aliases"]))
            print("HOLDOUT",name,flush=True)
            f=run_cli("field",x["path"],"--n",HOLDOUT,"--player","heuristic",
                      "--seed","final-golisopod-2026|HOLDOUT-B")
            holdout[name]=rate(f,"winRate",HOLDOUT)
            holdout[name]["golisopod_bring"]=bring(f,"Golisopod")
            save("holdout-"+name.replace(" ","-").lower()+".json",f)
        save("holdout.json",holdout)
        summary=["# Poképrotocol Golisopod: final corrected-preview stress audit","",
                 "**Bot simulations under the versioned weather-aware M-C preview policy. Not tournament win rates.**",
                 "All teams, complete recent tournament opponents and both six-species proxies passed Showdown legality.",
                 "Unlike proxies, recent tournament teams reproduce registered full six-Pokémon sets.",
                 "The training winner was chosen before the fresh 320-battle holdout; lookahead results are diagnostic.",
                 "", "## Ranking on fresh training seed","",
                 "| Team | Training score | Field wins/N | Field rate | Golisopod brought |",
                 "|---|---:|---:|---:|---:|"]
        for name in ranked:
            row=training[name]
            f=row["field"]
            summary.append(f"| {name} | {percent(row['score'])} | {f['wins']}/{f['n']} | {percent(f['rate'])} | {percent(f['golisopod_bring'])} |")
        summary += ["","**Frozen final champion: "+champion_name+"**","",
                    "## Matchups versus complete registered teams and proxies","",
                    "| Candidate | Opposing six | Fast W/N | Fast rate |",
                    "|---|---|---:|---:|"]
        for name in ranked[:2]:
            for opp,r in training[name]["matches"].items():
                summary.append(f"| {name} | {opp} | {r['wins']}/{r['n']} | {percent(r['rate'])} |")
        summary += ["","## Lookahead-AI stress tests (small samples)","",
                    "| Candidate | Opponent | Wins/N | Rate |",
                    "|---|---|---:|---:|"]
        for name,vals in lookahead.items():
            for opp,r in vals.items():
                summary.append(f"| {name} | {opp} | {r['wins']}/{r['n']} | {percent(r['rate'])} |")
        summary += ["","## Independent final holdout","",
                    "| Team | Wins/N | Rate | 95% CI | Golisopod brought |",
                    "|---|---:|---:|---|---:|"]
        for name,r in holdout.items():
            ci=r["ci95"] or [0,1]
            summary.append(f"| {name} | {r['wins']}/{r['n']} | {percent(r['rate'])} | {percent(ci[0])}–{percent(ci[1])} | {percent(r['golisopod_bring'])} |")
        summary += ["", "## Interpretation limits","",
                    "- Tournament field is sampled from accessible public OTS; it does not represent every tournament.",
                    "- Battle policies are bots. Even lookahead AI cannot validate predictions about human play.",
                    "- CIs overlap in small samples. Small score differences are inconclusive.",
                    "- Team-preview weather probabilities remain approximate; turn mechanics are unmodified.",
                    "- Proxy teams reproduce registered archetypes but NOT champions' exact unreleased sets.",
                    "- All published scores are tied to pinned M-C mechanics and the versioned preview patch.",
                    "", "## Final Showdown team", "",
                    "~~~", stringify(champion["team"]).rstrip(),"~~~",""]
        (OUT/"summary.md").write_text("\n".join(summary),encoding="utf8")
        manifest["status"]="completed"
        manifest["completed_at"]=datetime.now(timezone.utc).isoformat()
        manifest["holdout"]=holdout
        save("manifest.json",manifest)
        print("\n".join(summary),flush=True)
    except Exception as e:
        manifest["status"]="failed"
        manifest["error"]=str(e)
        save("manifest.json",manifest)
        (OUT/"summary.md").write_text("# Golisopod final audit FAILED\n\nNo claims.\n"+str(e))
        traceback.print_exc()
        sys.exit(1)

if __name__=="__main__":
    main()
