#!/usr/bin/env python3
"""Final Mega Golisopod partner safety test vs complete registered Sun teams.
All eligible finalists have Golisopite as their sole Mega Stone, no Salamence.
No results are human tournament win-rate estimates.
"""
from __future__ import annotations
import json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from evolve import ROOT,ENGINE,parse_team,stringify,registered_set,exclusive_mega_golisopod,run_cli,checked_rate
from replace_salamence import TEAM,variant

OUT=ROOT/"reports/final-sun-guard"
POLICY="POKEPROTOCOL_WEATHER_PREVIEW_V2"
CANDIDATES=["Corviknight | sand-proof Tailwind","Farigiraf | Armor Tail semiroom",
            "Incineroar | defensive pivot","Staraptor | balanced Intimidate/Tailwind"]
SUN_IDS=[
 ("Torkoal/CharizardY/Venusaur 7-1 event winner", "6af1e82ce99f3235a75e4c32:hn9l6x"),
 ("CharizardY/Venusaur 9-0 event winner","6adf3a9180a8f79408d1e7e8:1ov1znt")]
NFIELD=180
NMATCH=70
NSEARCH=12
NHOLDOUT=320

def save(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf8")
def pc(x):return f"{100*x:.1f}%"
def rate(x,k,n):
    a=checked_rate(x,k,n)
    return {key:a.get(key) for key in ("wins","losses","ties","n","rate","ci95")}
def mega(x):return x.get("side",x.get("a",{})).get("megaEvolvedIn",0)
def bring(x,species):
    side=x.get("side",x.get("a",{}))
    return next((a.get("brought",0) for a in side.get("bringRate",[]) if a.get("species")==species),0)
def team_from_ots(sources,ident,dest):
    row=next((t for t in sources if t["id"]==ident),None)
    if row is None or len(row.get("sets",[]))!=6:
        raise RuntimeError("Missing full OTS "+ident)
    sets=[registered_set(a) for a in row["sets"]]
    if any(a is None for a in sets):
        raise RuntimeError("Incomplete OTS "+ident)
    p=OUT/dest
    p.write_text(stringify(tuple(sets)),encoding="utf8")
    return p,row
def opponents():
    j=json.loads((ROOT/"data/field-recent.json").read_text(encoding="utf8"))
    pool=j["teams"];ans={};provenance={}
    for i,(name,ident) in enumerate(SUN_IDS):
        path,row=team_from_ots(pool,ident,"registered-sun-"+str(i+1)+".txt")
        if row["placing"]!=1 or not any(s["species"]=="Charizard" and s["item"]=="Charizardite Y" for s in row["sets"]):
            raise RuntimeError("Sun OTS source changed "+ident)
        ans[name]=path
        provenance[name]={"event":row["event"],"date":row["date"],"record":row["record"],
                          "placing":row["placing"],"id":ident,"species":[x["species"] for x in row["sets"]]}
    ans["LAIC published-set proxy (inferred Stat Points)"]=ROOT/"teams/benchmark-laic-champion-published-proxy.txt"
    latest=json.loads((ROOT/"data/latest-teams.json").read_text(encoding="utf8"))
    sets=[registered_set(x) for x in latest["teams"][1]["sets"]]
    if len(sets)!=6 or any(x is None for x in sets):
        raise RuntimeError("Missing complete registered second winner")
    p=OUT/"registered-recent-winner-2.txt"
    p.write_text(stringify(tuple(sets)),encoding="utf8")
    ans["Recent 11-0 fully registered winner #2"]=p
    return ans,provenance

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m={"status":"running","started_at":datetime.now(timezone.utc).isoformat(),
      "engine":"09d59984631dd2a45fb21700970c65ee24cf7d0f","policy":POLICY,
      "field_n":NFIELD,"match_n":NMATCH,"search_n":NSEARCH,"holdout_n":NHOLDOUT,
      "score":"35% field / 20% Torkoal Sun / 15% CharY Venusaur / 10% LAIC / 10% recent winner / 10% actual Goli Mega",
      "megagoli_floor":0.8}
    save("manifest.json",m)
    try:
        file=ENGINE/"src/engine/policy/preview.ts"
        if not file.exists() or POLICY not in file.read_text(encoding="utf8"):
            raise RuntimeError("Weather-aware policy not installed")
        if not (ROOT/"reports/evolution/weather-preview-policy.json").exists():
            raise RuntimeError("Policy source provenance missing")
        opp,provenance=opponents()
        m["full_ots_provenance"]=provenance
        for name,p in opp.items():
            v=run_cli("validate",p)
            if v.get("ok") is not True:
                raise RuntimeError("Illegal opponent "+name+": "+str(v.get("problems")))
        original=TEAM.read_text(encoding="utf8")
        teams={}
        for i,name in enumerate(CANDIDATES):
            txt=variant(original,name)
            parsed=parse_team(txt)
            if not exclusive_mega_golisopod(parsed) or any(x.species=="Salamence" for x in parsed):
                raise RuntimeError("Non-Goli-Mega alternative entered: "+name)
            p=OUT/("candidate-"+str(i)+".txt");p.write_text(txt,encoding="utf8")
            v=run_cli("validate",p)
            if v.get("ok") is not True:
                raise RuntimeError("Illegal candidate "+name+": "+str(v.get("problems")))
            teams[name]=p
        scores={}
        for i,(name,p) in enumerate(teams.items()):
            print("FIELD",name,flush=True)
            f=run_cli("field",p,"--n",NFIELD,"--player","heuristic","--seed","final-sun-goli|field")
            fw=rate(f,"winRate",NFIELD);mg=mega(f);b=bring(f,"Golisopod")
            save("field-"+str(i)+".json",f)
            targets={}
            for j,(opname,op) in enumerate(opp.items()):
                print("VS",name,opname,flush=True)
                x=run_cli("sim",p,op,"--n",NMATCH,"--player","heuristic",
                          "--seed","final-sun-goli|"+opname,"--logs",4)
                targets[opname]=rate(x,"winRateA",NMATCH)
                save("match-"+str(i)+"-"+str(j)+".json",x)
            v=list(targets.values())
            score=0.35*fw["rate"]+0.20*v[0]["rate"]+0.15*v[1]["rate"]+0.10*v[2]["rate"]+0.10*v[3]["rate"]+0.10*mg
            scores[name]={"field":fw,"targets":targets,"mega_used":mg,"goli_brought":b,"score":score}
            save("training.json",scores)
            print("SCORE",name,pc(score),pc(mg),flush=True)
        q=sorted((n for n in CANDIDATES if scores[n]["mega_used"]>=0.8),
                 key=lambda n:(-scores[n]["score"],n))
        if not q:raise RuntimeError("No finalist actually Mega Evolves Goli in >=80% of games")
        winner=q[0];runner=q[1] if len(q)>1 else q[0]
        m["frozen_winner"]=winner;m["ranking"]=q;save("manifest.json",m)
        (OUT/"best.txt").write_text(teams[winner].read_text(encoding="utf8"),encoding="utf8")
        strong={}
        for name in dict.fromkeys([winner,runner]):
            strong[name]={}
            for j,(oname,op) in enumerate(opp.items()):
                print("SEARCH",name,oname,flush=True)
                x=run_cli("sim",teams[name],op,"--n",NSEARCH,"--player","search",
                          "--seed","final-sun-goli|lookahead|"+oname,"--logs",2)
                strong[name][oname]=rate(x,"winRateA",NSEARCH)
                save("strong-"+str(q.index(name))+"-"+str(j)+".json",x)
        save("lookahead.json",strong)
        holdout={}
        for name in dict.fromkeys([winner,runner]):
            print("HOLDOUT",name,flush=True)
            x=run_cli("field",teams[name],"--n",NHOLDOUT,"--player","heuristic",
                      "--seed","final-sun-goli|reserved-holdout")
            holdout[name]={**rate(x,"winRate",NHOLDOUT),"goli_mega":mega(x),"goli_brought":bring(x,"Golisopod")}
            save("holdout-"+str(q.index(name))+".json",x)
        save("holdout.json",holdout)
        lines=["# Final Fire/Sun safety guard for Mega Golisopod","",
          "All candidate sets and complete registered tournament opponents passed M-C Showdown validation.",
          "Two real registered Sun teams have complete OTS; LAIC proxy has inferred Stat Points.",
          "No ordinary Salamence and no second Mega; minimum 80% actual Mega Golisopod activation.",
          "This is BOT simulation under versioned weather-aware M-C policy, not human tournament performance.",
          "Winner was selected before lookahead and untouched holdout.",
          "", "## Predeclared composite and stress matchups","",
          "| Candidate | Field W/N | Field rate | Torkoal Sun | CharY Venusaur | LAIC | Difficult OTS | Goli Mega | Score |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for name,a in sorted(scores.items(),key=lambda kv:-kv[1]["score"]):
            vals=list(a["targets"].values());fw=a["field"]
            lines.append(f"| {name} | {fw['wins']}/{fw['n']} | {pc(fw['rate'])} | "+
              f"{pc(vals[0]['rate'])} | {pc(vals[1]['rate'])} | {pc(vals[2]['rate'])} | "+
              f"{pc(vals[3]['rate'])} | {pc(a['mega_used'])} | {pc(a['score'])} |")
        lines+=["","**Winner frozen before holdout: "+winner+"**","",
          "## Fresh independent holdout","",
          "| Candidate | W/N | Rate | Goli brought | Mega Goli activated |",
          "|---|---:|---:|---:|---:|"]
        for name,a in holdout.items():
            lines.append(f"| {name} | {a['wins']}/{a['n']} | {pc(a['rate'])} | {pc(a['goli_brought'])} | {pc(a['goli_mega'])} |")
        lines+=["","## Lookahead AI diagnostic (small samples)","",
          "| Candidate | Opponent | W/N | Rate |","|---|---|---:|---:|"]
        for name,targets in strong.items():
            for oname,a in targets.items():
                lines.append(f"| {name} | {oname} | {a['wins']}/{a['n']} | {pc(a['rate'])} |")
        lines+=["","## Sun OTS provenance","",
          "~~~json",json.dumps(provenance,indent=2),"~~~","",
          "## Winner's full Showdown paste","",
          "~~~",teams[winner].read_text(encoding="utf8").rstrip(),"~~~","",
          "Results apply only to Regulation M-C. M-D and human matches remain untested.",""]
        (OUT/"summary.md").write_text("\n".join(lines),encoding="utf8")
        m["status"]="completed";m["completed_at"]=datetime.now(timezone.utc).isoformat()
        save("manifest.json",m)
        print("\n".join(lines),flush=True)
    except Exception as e:
        m["status"]="failed";m["error"]=str(e);save("manifest.json",m)
        (OUT/"summary.md").write_text("# Fire/sun safety test failed\n\nNo results claimed.\n"+str(e))
        traceback.print_exc();sys.exit(1)

if __name__=="__main__":
    main()
