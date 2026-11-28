#!/usr/bin/env python3
"""Fail-closed readiness gate for the *M-C* Poképrotocol simulator.

M-D is NOT supported until a new ruleset, engine and opponent field are
independently verified. This guard intentionally prevents accidental re-use.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re
import sys

M_D_START = datetime(2026, 12, 2, 2, 0, tzinfo=timezone.utc)
M_C_FORMAT = "gen9championsvgc2026regmc"
OTHER_REGULATION = re.compile(
    r"\bm[ -]?[a-bd-z]\b|\breg(?:ulation)?\s*(?:set\s*)?[a-bd-ln-z]\b|\bsingles?\b",
    flags=re.I,
)
MEGA_STONE = re.compile(r"ite(?:\s+[XYZ])?$", flags=re.I)
STATS = re.compile(r"(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)\b", flags=re.I)


def validate_roster(text: str) -> dict:
    blocks = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    if len(blocks) != 6:
        raise ValueError(f"Expected six sets, found {len(blocks)}")
    species, items, spreads = [], [], []
    for block in blocks:
        lines = block.splitlines()
        if " @ " not in lines[0]:
            raise ValueError("A Pokémon set has no species/item header")
        name, item = lines[0].split(" @ ", 1)
        species.append(name.strip())
        items.append(item.strip())
        evs = [line[5:].strip() for line in lines if line.startswith("EVs: ")]
        if len(evs) != 1:
            raise ValueError(f"{name} requires one Stat Point EVs line")
        vals = STATS.findall(evs[0])
        if len(vals) not in (2, 3, 4, 5, 6):
            raise ValueError(f"{name} has malformed Stat Points: {evs[0]}")
        if sum(int(n) for n, _ in vals) != 66 or any(int(n) > 32 for n, _ in vals):
            raise ValueError(f"{name} must use 66 Stat Points with 32 max per stat")
        if len({stat.lower() for _, stat in vals}) != len(vals):
            raise ValueError(f"{name} has duplicate stats in EVs")
        spreads.append(evs[0])
    if species[0] != "Golisopod" or items[0] != "Golisopite":
        raise ValueError("Canonical primary Mega must be Golisopod @ Golisopite in slot one")
    if len({x.casefold() for x in species}) != 6:
        raise ValueError("Duplicate species violate Species Clause")
    if len({x.casefold() for x in items}) != 6:
        raise ValueError("Duplicate held items violate Item Clause")
    if any(x.casefold() == "salamence" for x in species):
        raise ValueError("Ordinary Salamence excluded from the current primary Golisopod build")
    stones = [item for item in items if item.casefold() != "eviolite" and MEGA_STONE.search(item)]
    if stones != ["Golisopite"]:
        raise ValueError(f"Only Golisopite may be a Mega Stone: {stones}")
    return {"species": species, "items": items, "stat_points": 66, "mega": "Golisopod"}


def validate_field(field: dict, audit: dict, *, now: datetime, max_age_days: int = 10) -> dict:
    if audit.get("format") != M_C_FORMAT:
        raise ValueError(f"Unsupported field audit format: {audit.get('format')}")
    refreshed = datetime.fromisoformat(str(audit["refreshedAt"]).replace("Z", "+00:00"))
    if refreshed.tzinfo is None:
        raise ValueError("Field refresh timestamp must include a UTC offset")
    age = now - refreshed
    if age > timedelta(days=max_age_days) or age < timedelta(days=-1):
        raise ValueError(f"M-C field is stale or future-dated: age {age}")
    meta = field.get("meta", {})
    if not isinstance(meta, dict):
        raise ValueError("No tournament field metadata")
    sources = meta.get("sources", [])
    teams = field.get("teams", [])
    if not isinstance(sources, list) or not isinstance(teams, list):
        raise ValueError("Tournament field metadata is malformed")
    if len(sources) < 3 or len(teams) < 30:
        raise ValueError("Insufficient recent tournament sources / teams")
    bad_sources = [str(s.get("name", "<unnamed>")) for s in sources
                   if s.get("reg") != "M-C" or OTHER_REGULATION.search(str(s.get("name", "")))]
    if bad_sources:
        raise ValueError("Non-M-C event labels/regulations in recent field: "
                         + "; ".join(bad_sources[:6]))
    bad_teams = [t for t in teams if t.get("reg") != "M-C"]
    if bad_teams:
        raise ValueError(f"Found {len(bad_teams)} opponents not marked M-C")
    return {"field_teams": len(teams), "field_sources": len(sources),
            "field_refreshed_at": refreshed.isoformat(), "field_format": M_C_FORMAT}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", type=Path, required=True)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--format", default="M-C")
    parser.add_argument("--max-age-days", type=int, default=10)
    parser.add_argument("--allow-historical-mc", action="store_true")
    args = parser.parse_args(argv)
    now = datetime.now(timezone.utc)
    if args.format != "M-C":
        raise ValueError("M-D unsupported: cannot certify new regulation with the M-C engine")
    if now >= M_D_START and not args.allow_historical_mc:
        raise ValueError("M-C has ended. Run only explicit archived M-C tests until M-D support is validated")
    roster = validate_roster(args.team.read_text(encoding="utf-8"))
    field = json.loads(args.field.read_text(encoding="utf-8"))
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    report = validate_field(field, audit, now=now, max_age_days=args.max_age_days)
    print(json.dumps({"status": "passed", "scope": "M-C only",
                      "md_supported": False, **roster, **report}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as error:
        print("PRE_MD_AUDIT_FAILED:", error, file=sys.stderr)
        sys.exit(1)
