#!/usr/bin/env python3
"""Fix the Mega Golisopod theme at the battle-behavior level.

Compare legal Golisopod-only Mega teams with the unconstrained high-scoring
three-Mega roster. Selection eligible only for teams where Golisopite is the
sole Mega Stone. An independent holdout is evaluated after selection.
"""
from __future__ import annotations
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime,timezone
from evolve import ROOT,ENGINE,parse_team,stringify,locked,registered_set,run_cli,checked_rate,SetBlock

OUT=ROOT/"reports/mega-golisopod-only"
SAND=ROOT/"teams/evolution-best-nov27.txt"
RAIN=ROOT/"teams/golisopod-incineroar-nov27.txt"
LAIC=ROOT/"teams/benchmark-laic-champion-published-proxy.txt"
SECOND=ROOT/"data/latest-teams.json"
POLICY="POKEPROTOCOL_WEATHER_PREVIEW_V2"
WEATHER_ROOT=ROOT/"reports/evolution/weather-preview-policy.json"
FIELD_N=240
MATCH_N=80
SEARCH_N=16
HOLDOUT_N=320

WHIMSICOTT=SetBlock("""Whimsicott @ Focus Sash
Ability: Prankster
Level: 50
EVs: 2 HP / 32 SpA / 32 Spe
Timid Nature
- Moonblast
- Tailwind
- Encore
- Protect""")

def save(path,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/path).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf8")

def p(x):
    return f"{100*x:.1f}%"

def change_to_goli_only(text,whimsicott=False):
    team=list(parse_team(text))
    new=[]
    for pokemon in team:
        name=pokemon.species
        raw=pokemon.text
        if name=="Salamence":
            if raw.count("@ Salamencite")!=1: raise ValueError("Expected Salamencite")
            if whimsicott:
                new.append(WHIMSICOTT)
                continue
            raw=raw.replace("@ Salamencite","@ Focus Sash")
        elif name=="Tyranitar":
            if raw.count("@ Tyranitarite")!=1: raise ValueError("Expected Tyranitarite")
            raw=raw.replace("@ Tyranitarite","@ Chople Berry")
        new.append(SetBlock(raw))
    result=tuple(new)
    if not locked(result): raise ValueError("Golisopod must be locked and species unique")
    if sum(s.item.lower().endswith(("ite","ite x","ite y","ite z")) for s in result)!=1:
        raise ValueError("More than one Mega Stone remains")
    if sum(s.item=="Golisopite" for s in result)!=1:
        raise ValueError("Mega Golisopod not the only Mega")
    return stringify(result)

def rate(result,key,expected):
    q=checked_rate(result,key,expected)
    return {k:q.get(k) for k in ("rate","wins","losses","ties","n","ci95")}

def info(result):
    side=result.get("side",result.get("a",{}))
    def bring(species):
        return next((x["brought"] for x in side.get("bringRate",[])
                     if x["species"]==species),0)
    return {"mega_evolved_rate":side.get("megaEvolvedIn"),
            "golisopod_bring":bring("Golisopod"),
            "archaludon_bring":bring("Archaludon")}

def build_opponent():
    data=json.loads(SECOND.read_text(encoding="utf8"))
    sets=[registered_set(s) for s in data["teams"][1]["sets"]]
    if len(sets)!=6 or any(s is None for s in sets):
        raise RuntimeError("Recent registered winner #2 incomplete")
    path=OUT/"recent-winner-2.txt"
    path.write_text(stringify(tuple(sets)),encoding="utf8")
    return path

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={"status":"running","started_at":datetime.now(timezone.utc).isoformat(),
              "policy":POLICY,"format":"gen9championsvgc2026regmc",
              "field":FIELD_N,"match":MATCH_N,"search":SEARCH_N,"holdout":HOLDOUT_N}
    save("manifest.json",manifest)
    try:
        preview=ENGINE/"src/engine/policy/preview.ts"
        if not preview.exists() or POLICY not in preview.read_text(encoding="utf8"):
            raise RuntimeError("Fail closed: weather-aware preview not installed")
        if not WEATHER_ROOT.exists():
            raise RuntimeError("Fail closed: policy manifest missing")
        original=SAND.read_text(encoding="utf8")
        rain=RAIN.read_text(encoding="utf8")
        variants={
            "Sand / base Salamence":change_to_goli_only(original),
            "Sand / Whimsicott":change_to_goli_only(original,True),
            "Rain / base Salamence":change_to_goli_only(rain),
            "Unrestricted three-Mega reference":original
        }
        paths={}
        rejected={}
        for name,text in variants.items():
            path=OUT/("team-"+name.replace(" / ","-").replace(" ","-").lower()+".txt")
            path.write_text(text,encoding="utf8")
            verdict=run_cli("validate",path)
            save("validate-"+path.stem+".json",verdict)
            if verdict.get("ok") is True:
                paths[name]=path
            else:
                rejected[name]=verdict.get("problems")
        manifest["rejected"]=rejected
        if "Sand / base Salamence" not in paths or "Rain / base Salamence" not in paths:
            raise RuntimeError("Essential only-Golisopite candidates are not legal: "+str(rejected))
        opponents={"LAIC champion published-set proxy":LAIC,
                   "Recent winner 2 full OTS":build_opponent()}
        for name,path in opponents.items():
            q=run_cli("validate",path)
            if q.get("ok") is not True:
                raise RuntimeError("Invalid opponent "+name+": "+str(q.get("problems")))
        results={}
        for name,path in paths.items():
            print("FIELD",name,flush=True)
            f=run_cli("field",path,"--n",FIELD_N,
                      "--player","heuristic","--seed","goli-mega-only-2026|TRAIN")
            win=rate(f,"winRate",FIELD_N)
            save("field-"+name.replace(" / ","-").replace(" ","-").lower()+".json",f)
            meta=info(f)
            match={}
            for oname,op in opponents.items():
                print("MATCHUP",name,oname,flush=True)
                sim=run_cli("sim",path,op,"--n",MATCH_N,"--player","heuristic",
                            "--seed","goli-mega-only-2026|"+oname,"--logs",4)
                match[oname]=rate(sim,"winRateA",MATCH_N)
                save("fast-"+name.replace(" / ","-").replace(" ","-").lower()+
                     "-"+oname.replace(" ","-")+".json",sim)
            score=0.70*win["rate"]+0.20*match["LAIC champion published-set proxy"]["rate"]+0.10*match["Recent winner 2 full OTS"]["rate"]
            results[name]={"field":win,"bring":meta,"matches":match,"training_score":score}
            save("training.json",results)
            print("SCORE",name,p(score),"Goli Mega",p(meta["mega_evolved_rate"] or 0),flush=True)
        eligible=[name for name in paths if not name.startswith("Unrestricted")]
        eligible.sort(key=lambda name:(-results[name]["training_score"],name))
        frozen=eligible[0]
        runner_up=eligible[1] if len(eligible)>1 else eligible[0]
        manifest["winner"]=frozen
        manifest["eligible_rank"]=eligible
        save("manifest.json",manifest)
        (OUT/"best.txt").write_text(paths[frozen].read_text(encoding="utf8"),encoding="utf8")
        strong={}
        for name in dict.fromkeys([frozen,runner_up]):
            strong[name]={}
            for oname,op in opponents.items():
                print("LOOKAHEAD",name,oname,flush=True)
                s=run_cli("sim",paths[name],op,"--n",SEARCH_N,"--player","search",
                          "--seed","goli-mega-only-2026|STRONG|"+oname,"--logs",4)
                strong[name][oname]=rate(s,"winRateA",SEARCH_N)
                save("strong-"+name.replace(" / ","-").replace(" ","-").lower()+
                     "-"+oname.replace(" ","-")+".json",s)
        save("lookahead.json",strong)
        holdout={}
        for name in dict.fromkeys([frozen,"Unrestricted three-Mega reference"]):
            print("HOLDOUT",name,flush=True)
            f=run_cli("field",paths[name],"--n",HOLDOUT_N,"--player","heuristic",
                      "--seed","goli-mega-only-2026|HOLDOUT")
            holdout[name]={**rate(f,"winRate",HOLDOUT_N),**info(f)}
            save("holdout-"+name.replace(" / ","-").replace(" ","-").lower()+".json",f)
        save("holdout.json",holdout)
        lines=["# Mega Golisopod actual-use validation","",
               "Corrected-preview M-C bot-versus-bot simulations, not real tournament wins.",
               "The key objective is Mega Golisopod **actually used**, not just brought.",
               "All eligible teams have only Golisopite: their simulator megaEvolvedIn",
               "rate therefore measures Mega Golisopod usage. Unrestricted reference",
               "can Mega Salamence or Tyranitar and is NOT eligible for selection.",
               "Selection before the independent holdout: 70% field, 20% published",
               "LAIC champion proxy, 10% recent exact registered winner six.",
               "The LAIC proxy has inferred Stat Points.",
               "","## Comparison of candidate teams","",
               "| Variant | Field wins/N | Field rate | Goli brought | Goli Mega-used | Score |",
               "|---|---:|---:|---:|---:|---:|"]
        for name,rr in sorted(results.items(),key=lambda kv:-kv[1]["training_score"]):
            win,meta=rr["field"],rr["bring"]
            label=name+(" (reference only)" if name.startswith("Unrestricted") else "")
            lines.append(f"| {label} | {win['wins']}/{win['n']} | {p(win['rate'])} | "+
                         f"{p(meta['golisopod_bring'])} | "+
                         (p(meta['mega_evolved_rate']) if not name.startswith("Unrestricted") else "not isolated")+
                         f" | {p(rr['training_score'])} |")
        lines+=["","**Frozen Golisopod-only Mega champion: "+frozen+"**","",
                "## Published champion and recent winner matchups","",
                "| Variant | Opponent | Wins/N | Rate |","|---|---|---:|---:|"]
        for name,rr in results.items():
            for oname,rec in rr["matches"].items():
                lines.append(f"| {name} | {oname} | {rec['wins']}/{rec['n']} | {p(rec['rate'])} |")
        lines+=["","## Lookahead checks (small samples)","",
                "| Variant | Opponent | Wins/N | Rate |","|---|---|---:|---:|"]
        for name,records in strong.items():
            for oname,rec in records.items():
                lines.append(f"| {name} | {oname} | {rec['wins']}/{rec['n']} | {p(rec['rate'])} |")
        lines+=["","## Fresh independent holdout","",
                "| Variant | Wins/N | Rate | 95% CI | Goli brought | Goli Mega used |",
                "|---|---:|---:|---|---:|---:|"]
        for name,rec in holdout.items():
            ci=rec["ci95"] or [0,1]
            used=p(rec["mega_evolved_rate"]) if not name.startswith("Unrestricted") else "not isolated"
            lines.append(f"| {name} | {rec['wins']}/{rec['n']} | {p(rec['rate'])} | "+
                         f"{p(ci[0])}–{p(ci[1])} | {p(rec['golisopod_bring'])} | {used} |")
        lines+=["","## Final Mega Golisopod Showdown paste","",
                "~~~",paths[frozen].read_text(encoding="utf8").rstrip(),"~~~",
                "","## Qualifications","",
                "- Removing Salamencite and Tyranitarite is necessary to isolate Mega Golisopod usage.",
                "- Lookahead samples and holdout are bot simulations, not estimates of tournament performance.",
                "- Differences between policies must not be compared as if measured under the same preview algorithm.",
                "- No M-D legal claims; current evaluation applies to M-C only.",
                "- If the eligible final champion struggles on holdout, report that honestly and consider broader future searches.",
                "", "## Rejected candidates",json.dumps(rejected,ensure_ascii=False,indent=2),""]
        (OUT/"summary.md").write_text("\n".join(lines),encoding="utf8")
        manifest["status"]="completed"
        manifest["completed_at"]=datetime.now(timezone.utc).isoformat()
        save("manifest.json",manifest)
        print("\n".join(lines),flush=True)
    except Exception as exc:
        manifest["status"]="failed"
        manifest["error"]=str(exc)
        save("manifest.json",manifest)
        (OUT/"summary.md").write_text("# Mega Golisopod actual-use audit FAILED\n\nNo win rates claimed.\n"+str(exc),encoding="utf8")
        traceback.print_exc()
        sys.exit(1)

if __name__=="__main__":
    main()
