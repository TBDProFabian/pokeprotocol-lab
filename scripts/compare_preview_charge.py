#!/usr/bin/env python3
"""A/B test Champions Lab's charging-move preview valuation.

The pinned upstream preview duel uses one-hit damage for charging moves, while
the in-battle heuristic explicitly uses a 0.45 discount when charge is needed.
This experiment DOES NOT alter the active team or its pinned production runner.
It applies an explicit local-only patch inside this disposable GitHub Actions
checkout, then re-runs matched team-preview / field / proxy comparisons.

The patch is a conservative *diagnostic* (not weather-perfect). A permanent
fix needs a weather-aware full preview model and simulator-policy review.
"""
from __future__ import annotations
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from evolve import ROOT, ENGINE, run_cli, checked_rate

OUT=ROOT/"reports/charging-preview-diagnostic"
SOURCE=ENGINE/"src/engine/policy/preview.ts"
BASE=ROOT/"teams/evolution-best-nov27.txt"
RAIN_PROXY=ROOT/"teams/benchmark-laic-rain-proxy.txt"
SEED="charging-preview-audit-v1"
ANCHOR="const f = (avg / r.defenderMaxHP) * acc * (mv.spread ? 1.25 : 1);"
REPLACEMENT="""// EXPERIMENTAL: model the tempo lost by charging outside Power Herb.
        // The live policy's chargeNow() returns 0.45 for delayed attacks;
        // this preview simplification has NO weather inference yet.
        const chargeTempo = mv.flags.includes('charge') && toID(a.set.item) !== 'powerherb' ? 0.45 : 1;
        const f = (avg / r.defenderMaxHP) * acc * (mv.spread ? 1.25 : 1) * chargeTempo;"""

def patched_source(text: str)->str:
    if text.count(ANCHOR)!=1 or "EXPERIMENTAL: model the tempo" in text:
        raise RuntimeError("Pinned preview code differs from validated patch anchor")
    return text.replace(ANCHOR, REPLACEMENT)

def variant(base: str, move: str)->str:
    if base.count("- Electro Shot")!=1:
        raise RuntimeError("Expected exactly one Electro Shot move")
    return base.replace("- Electro Shot","- "+move)

def save(name: str, data)->None:
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf8")

def pretty(r):
    return f"{100*r:.1f}%"

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw_source=SOURCE.read_text(encoding="utf8")
    patched=patched_source(raw_source)
    base=BASE.read_text(encoding="utf8")
    candidates={}
    for mv in ("Electro Shot","Flash Cannon"):
        path=OUT/("team-"+mv.lower().replace(" ","-")+".txt")
        path.write_text(variant(base,mv),encoding="utf8")
        v=run_cli("validate",path)
        if not v.get("ok"):
            raise RuntimeError(f"Illegal set {mv}: {v.get('problems')}")
        candidates[mv]=path
    output={}
    try:
        for policy in ("upstream","charge-aware"):
            if policy=="charge-aware":
                SOURCE.write_text(patched,encoding="utf8")
            per={}
            for name,path in candidates.items():
                print("PREVIEW",policy,name,flush=True)
                prev=run_cli("preview",path,RAIN_PROXY)
                print("FIELD",policy,name,flush=True)
                field=run_cli("field",path,"--n",120,"--player","heuristic",
                              "--seed",SEED+"|field")
                fw=checked_rate(field,"winRate",120)
                print("PROXY",policy,name,flush=True)
                sim=run_cli("sim",path,RAIN_PROXY,"--n",100,"--player","heuristic",
                            "--seed",SEED+"|rain","--logs",8)
                sw=checked_rate(sim,"winRateA",100)
                save("preview-"+policy+"-"+name.replace(" ","-")+".json",prev)
                save("field-"+policy+"-"+name.replace(" ","-")+".json",field)
                save("proxy-"+policy+"-"+name.replace(" ","-")+".json",sim)
                a=sim.get("a",{}).get("bringRate",[])
                a_arch=next((x.get("brought") for x in a if x.get("species")=="Archaludon"),None)
                per[name]={"preview_recommended":prev.get("recommended"),
                           "preview_my_bring_mix":prev.get("myBringMix"),
                           "field_rate":fw["rate"],"field_wins":fw["wins"],"field_n":fw["n"],
                           "rain_proxy_rate":sw["rate"],"rain_proxy_wins":sw["wins"],
                           "rain_proxy_n":sw["n"],"archaludon_brought_vs_rain":a_arch}
            output[policy]=per
            save("comparison.json",output)
    finally:
        SOURCE.write_text(raw_source,encoding="utf8")

    fmtname=lambda s:s.replace(" ","-")
    lines=["# Controlled test: charging move preview valuation","",
           "Pinned M-C simulator, not real-player performance.",
           "The only simulator change in charge-aware mode is a 0.45 expected",
           "tempo multiplier for charging attacks without Power Herb inside",
           "the **team-preview damage table**. Battle resolution/AI is unchanged.",
           "Weather prediction is NOT implemented in this diagnostic patch.",
           "All game comparisons use matched opponent sampling seeds.","",
           "## Results","",
           "| Policy | Arch move | Field W/N | Field rate | Rain proxy W/N | Rain proxy rate | Arch brought vs rain |",
           "|---|---|---:|---:|---:|---:|---:|"]
    for policy,values in output.items():
        for move,v in values.items():
            b=v["archaludon_brought_vs_rain"]
            lines.append(f"| {policy} | {move} | {v['field_wins']}/{v['field_n']} | "
                         f"{pretty(v['field_rate'])} | {v['rain_proxy_wins']}/{v['rain_proxy_n']} | "
                         f"{pretty(v['rain_proxy_rate'])} | {pretty(b) if b is not None else '?'} |")
    lines += ["","The upstream preview treats a charge move's full expected damage as",
              "immediate, whereas the in-battle model discounts charge attacks.",
              "If Archaludon bring frequency collapses after the preview patch, the",
              "earlier Electro Shot advantage was at least partly preview-policy bias.",
              "Do not interpret this local correction as a production-engine fix;",
              "weather-aware preview logic and tests are needed before adoption.",""]
    (OUT/"summary.md").write_text("\n".join(lines),encoding="utf8")
    save("manifest.json",{"status":"completed","created_at":datetime.now(timezone.utc).isoformat(),
                          "engine":"09d59984631dd2a45fb21700970c65ee24cf7d0f",
                          "patch_applied_temporarily":True,"team_count":len(candidates),
                          "policy_count":len(output)})
    print("\n".join(lines),flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        save("manifest.json",{"status":"failed","error":str(exc)})
        (OUT/"summary.md").write_text("# Charging preview diagnostic FAILED\n\nNo results claimed.\n"+str(exc))
        raise
