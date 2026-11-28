#!/usr/bin/env python3
"""Build-quality checks complementing the authoritative M-C legality validator.

Flag two demonstrably flawed carryovers when Mega Salamence was changed to
base Salamence alongside Sand Stream in our Mega Golisopod project.
"""
from __future__ import annotations
from pathlib import Path
import argparse, json, re, sys

def problems(team) -> list[str]:
    issues=[]
    if (len(team)!=6 or team[0].species!="Golisopod" or
        team[0].item!="Golisopite" or
        len({p.species for p in team})!=6):
        issues.append("Requires exactly six unique Pokémon with Golisopod @ Golisopite in slot one")
    mega_stones=[p.item for p in team
                 if p.item.lower()!="eviolite" and
                 re.search(r"ite(?:\s+[XYZ])?$",p.item,re.I)]
    if mega_stones!=["Golisopite"]:
        issues.append("Golisopite must be the only Mega Stone")
    sand=any(p.species=="Tyranitar" and "Ability: Sand Stream" in p.text for p in team)
    for p in team:
        if p.species=="Salamence":
            # Hyper Voice is legal, but here it was carried over from Aerilate Mega Salamence.
            if "- Hyper Voice" in p.text and p.item!="Salamencite":
                issues.append("Base Salamence's Hyper Voice lost Mega Aerilate Flying STAB and boost")
            if sand and p.item=="Focus Sash":
                issues.append("Tyranitar sand end-turn chip conflicts with Salamence Focus Sash")
    return issues

def main():
    from evolve import parse_team
    parser=argparse.ArgumentParser()
    parser.add_argument("team",type=Path)
    args=parser.parse_args()
    issues=problems(parse_team(args.team.read_text(encoding="utf8")))
    print(json.dumps({"team":str(args.team),"pass":not issues,"issues":issues},indent=2))
    sys.exit(1 if issues else 0)

if __name__=="__main__":
    main()
