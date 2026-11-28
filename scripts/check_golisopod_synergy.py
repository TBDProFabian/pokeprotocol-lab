#!/usr/bin/env python3
"""Poképrotocol Golisopod-specific build consistency checks.

Distinct from Showdown legality: disallow two known strategic carryovers
observed when a Mega Salamence team was converted into a sole-Mega-Golisopod
sand team. The tool must NEVER claim to validate damage or metagame strength.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import sys

def problems(team:tuple[SetBlock,...]) -> list[str]:
    issues=[]
    if not exclusive_mega_golisopod(team):
        issues.append("Golisopite must be the only Mega Stone on this team's six")
    sand=any(p.species=="Tyranitar" and "Ability: Sand Stream" in p.text for p in team)
    for p in team:
        if p.species=="Salamence":
            # Hyper Voice remains legal and may suit other teams. In this specific
            # sole-Mega-Golisopod team, keeping it is an unjustified Mega-Aerilate carryover.
            if "- Hyper Voice" in p.text and p.item!="Salamencite":
                issues.append("Base Salamence's Hyper Voice lost Mega Aerilate's Flying typing and boost")
            if sand and p.item=="Focus Sash":
                issues.append("Tyranitar's sand chip conflicts with Salamence's Focus Sash after round one")
    return issues

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("team",type=Path)
    args=parser.parse_args()
    from evolve import parse_team,exclusive_mega_golisopod
    team=parse_team(args.team.read_text(encoding="utf8"))
    issues=problems(team)
    if not exclusive_mega_golisopod(team):
        issues.insert(0,"Golisopite must be the only Mega Stone on this team\'s six")
    print(json.dumps({"team":str(args.team),"pass":not issues,"issues":issues},indent=2))
    sys.exit(1 if issues else 0)

if __name__=="__main__":
    main()
