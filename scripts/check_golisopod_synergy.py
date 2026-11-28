#!/usr/bin/env python3
"""Separate legal/theme failures from matchup-dependent strategic warnings.

These warnings are informative only. In particular Focus Sash is sometimes
useful before Sand Stream chip or when Tyranitar is not brought, and base
Hyper Voice remains a neutral spread attack even without Aerilate.
"""
from __future__ import annotations
from pathlib import Path
import argparse, json, re, sys

def problems(team) -> list[str]:
    issues=[]
    if (len(team)!=6 or team[0].species!="Golisopod" or
        team[0].item!="Golisopite" or
        len({p.species for p in team})!=6):
        issues.append("Requires six unique Pokémon and Golisopod @ Golisopite in slot 1")
    mega_stones=[p.item for p in team
                 if p.item.lower()!="eviolite" and
                 re.search(r"ite(?:\s+[XYZ])?$",p.item,re.I)]
    if mega_stones!=["Golisopite"]:
        issues.append("Golisopite must be the only Mega Stone")
    return issues

def warnings(team) -> list[str]:
    advisories=[]
    sand=any(p.species=="Tyranitar" and "Ability: Sand Stream" in p.text for p in team)
    for p in team:
        if p.species=="Salamence":
            if "- Hyper Voice" in p.text and p.item!="Salamencite":
                advisories.append("Base Salamence Hyper Voice is ordinary Normal spread damage without Mega Aerilate STAB and boost; verify value against alternatives")
            if sand and p.item=="Focus Sash":
                advisories.append("Sand Stream can break Salamence Focus Sash after a turn; measure actual Tyranitar bring rate before rejecting it")
    return advisories

def main():
    from evolve import parse_team
    parser=argparse.ArgumentParser()
    parser.add_argument("team",type=Path)
    args=parser.parse_args()
    team=parse_team(args.team.read_text(encoding="utf8"))
    errors=problems(team)
    advice=warnings(team)
    print(json.dumps({"team":str(args.team),"pass":not errors,
                      "errors":errors,"advisories":advice},indent=2))
    sys.exit(1 if errors else 0)

if __name__=="__main__":
    main()
