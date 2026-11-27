#!/usr/bin/env python3
"""Harvest a reproducible, diverse set donor pool from the pinned tournament field.

The old latest-teams.json export has only two teams: that prevented meaningful
move mutations for core species not represented there (notably Archaludon).
This script queries actual field team sheets through Champions Lab. It does not
invent or silently generate moves. Validation remains in evolve.py.
"""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

from evolve import ROOT, run_cli, registered_set, parse_team

OUT = ROOT / "data" / "evolution-donors.json"
USAGE = ROOT / "data" / "latest-usage.json"
SEED = ROOT / "teams" / "golisopod-current.txt"
TARGET = (
 "Archaludon", "Golisopod", "Salamence", "Rillaboom", "Pelipper",
 "Basculegion", "Basculegion-F", "Tyranitar", "Incineroar", "Milotic",
 "Sneasler", "Kingambit", "Raichu", "Farigiraf", "Gholdengo",
 "Metagross", "Garchomp", "Charizard"
)

def dedupe(entries: list[dict], permitted: set[str]) -> tuple[list[dict], dict[str,int]]:
    """Keep tournament provenance, unique complete sets, and a bounded meta pool."""
    seen=set()
    filtered=[]
    counts=Counter()
    for row in entries:
        sets=[]
        for record in row.get("sets",[]):
            if not isinstance(record,dict) or record.get("species") not in permitted:
                continue
            s=registered_set(record)
            if not s:
                continue
            token=(s.species,s.text)
            if token in seen or counts[s.species]>=100:
                continue
            seen.add(token)
            sets.append(record)
            counts[s.species]+=1
        if sets:
            filtered.append({"event":row.get("event"),"date":row.get("date"),
                             "placing":row.get("placing"),"sets":sets})
    return filtered,dict(counts)

def gather(query: str|None=None, limit: int=50)->list[dict]:
    args=["teams"]
    if query:
        args += ["--species",query]
    args += ["--limit",str(limit)]
    result=run_cli(*args)
    teams=result.get("teams")
    if not isinstance(teams,list):
        raise RuntimeError("Champions Lab 'teams' query returned no teams collection")
    return teams

def main():
    if not USAGE.exists():
        raise RuntimeError("Missing latest-usage.json")
    usage=json.loads(USAGE.read_text(encoding="utf8"))
    recent=usage.get("usage",[])
    # Focus experimentation on real popular species, plus the active team's core.
    popular={x["species"] for x in recent[:50] if isinstance(x,dict) and x.get("species")}
    baseline={p.species for p in parse_team(SEED.read_text(encoding="utf8"))}
    permitted=popular|baseline|set(TARGET)
    raw=gather(None,120)
    print("Global donor teams:",len(raw),flush=True)
    for i,species in enumerate(TARGET):
        games=gather(species,35 if species not in baseline else 65)
        raw.extend(games)
        print(f"{i+1}/{len(TARGET)} {species}: {len(games)} field teams",flush=True)
    teams,counts=dedupe(raw,permitted)
    if counts.get("Archaludon",0)<2:
        raise RuntimeError("Archaludon still lacks at least two distinct tournament donor sets")
    if sum(counts.values())<60:
        raise RuntimeError("Field donor pool unexpectedly small")
    payload={
      "provenance":{"source":"pinned Champions Lab tournament field via teams CLI",
                    "created_at":datetime.now(timezone.utc).isoformat(),
                    "queries":["teams --limit 120"]+
                              [f"teams --species {s} --limit {35 if s not in baseline else 65}" for s in TARGET],
                    "distinct_species":len(counts),
                    "registered_sets":sum(counts.values()),
                    "per_species":counts,
                    "format":"gen9championsvgc2026regmc"},
      "teams":teams
    }
    OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf8")
    print("DONORS_READY",json.dumps({"species":len(counts),
                                      "sets":sum(counts.values()),
                                      "archaludon":counts["Archaludon"]}),flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("Donor refresh failed:",str(e),file=sys.stderr)
        sys.exit(1)
