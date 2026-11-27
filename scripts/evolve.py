#!/usr/bin/env python3
"""Conservative, reproducible genetic search using the pinned Champions Lab CLI.

This is experimental simulator optimization, NOT an estimate of human win rate.
All proposed teams are passed through the real game's M-C team validator.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess
import sys
import traceback
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "champions-lab"
OUT = ROOT / "reports" / "evolution"
LOCKED_SPECIES = "Golisopod"
LOCKED_ITEM = "Golisopite"
ENGINE_SHA = "09d59984631dd2a45fb21700970c65ee24cf7d0f"


@dataclass(frozen=True)
class SetBlock:
    text: str

    @property
    def species(self) -> str:
        head = self.text.splitlines()[0].split(" @ ")[0].strip()
        # Showdown's optional nickname syntax: Nickname (Species) @ Item
        m = re.match(r"^.+\(([^()]*)\)$", head)
        return (m.group(1) if m else head).strip()

    @property
    def item(self) -> str:
        return self.text.splitlines()[0].split(" @ ", 1)[1].strip() if " @ " in self.text.splitlines()[0] else ""


def parse_team(text: str) -> tuple[SetBlock, ...]:
    blocks = [SetBlock("\n".join(line.rstrip() for line in b.strip().splitlines()))
              for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    if len(blocks) != 6:
        raise ValueError(f"Expected 6 Pokémon, got {len(blocks)}")
    if any(not b.item or len([x for x in b.text.splitlines() if x.startswith("- ")]) != 4 for b in blocks):
        raise ValueError("Every set needs an item and four moves")
    return tuple(blocks)


def stringify(team: tuple[SetBlock, ...]) -> str:
    return "\n\n".join(s.text for s in team) + "\n"


def fingerprint(team: tuple[SetBlock, ...]) -> str:
    return hashlib.sha256(stringify(team).encode()).hexdigest()[:16]


def locked(team: tuple[SetBlock, ...]) -> bool:
    return (len(team) == 6 and team[0].species == LOCKED_SPECIES and
            team[0].item == LOCKED_ITEM and sum(p.species == LOCKED_SPECIES for p in team) == 1 and
            len({p.species.casefold() for p in team}) == 6)


def registered_set(record: dict[str, Any]) -> SetBlock | None:
    """Convert full tournament sets, preserving their registered moves/item/stat points."""
    species, item, ability = (record.get(k) for k in ("species", "item", "ability"))
    nature, moves, evs = (record.get(k) for k in ("nature", "moves", "evs"))
    if not (isinstance(species, str) and isinstance(item, str) and isinstance(ability, str)
            and isinstance(nature, str) and isinstance(moves, list) and len(moves) == 4
            and all(isinstance(x, str) and x for x in moves) and isinstance(evs, dict)):
        return None
    mapping = (("hp", "HP"), ("atk", "Atk"), ("def", "Def"), ("spa", "SpA"), ("spd", "SpD"), ("spe", "Spe"))
    if any(type(evs.get(k, 0)) is not int or not 0 <= evs.get(k, 0) <= 32 for k, _ in mapping):
        return None
    if sum(evs.get(k, 0) for k, _ in mapping) > 66:
        return None
    vals = " / ".join(f"{evs.get(k, 0)} {n}" for k, n in mapping if evs.get(k, 0))
    if not vals:
        return None
    content = [f"{species} @ {item}", f"Ability: {ability}", f"Level: {record.get('level', 50)}", f"EVs: {vals}", f"{nature} Nature"]
    content.extend(f"- {m}" for m in moves)
    return SetBlock("\n".join(content))


def registry(seed: tuple[SetBlock, ...], donors_file: Path) -> dict[str, list[SetBlock]]:
    data = json.loads(donors_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("teams"), list) or not data["teams"]:
        raise ValueError("Tournament donor JSON lacks a nonempty teams array")
    by_species: dict[str, list[SetBlock]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    def add(s: SetBlock) -> None:
        key = (s.species, s.text)
        if key not in seen:
            by_species[s.species].append(s)
            seen.add(key)
    for b in seed:
        add(b)
    for team in data["teams"]:
        for obj in team.get("sets", []):
            if isinstance(obj, dict):
                record = registered_set(obj)
                if record:
                    add(record)
    if len(by_species) < 7:
        raise ValueError("Not enough registered donor species for genetic search")
    return dict(by_species)


def _replace_line(block: SetBlock, prefix: str, replacement: str) -> SetBlock:
    lines = block.text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = replacement
            return SetBlock("\n".join(lines))
    raise ValueError(f"Missing {prefix} in {block.species}")


def mutate(team: tuple[SetBlock, ...], pool: dict[str, list[SetBlock]], rng: random.Random,
           mate: tuple[SetBlock, ...] | None = None) -> tuple[tuple[SetBlock, ...], str]:
    """Mutation operators only recombine components from donor sets or a second parent."""
    positions = list(range(1, 6))
    i = rng.choice(positions)
    current = team[i]
    same = pool.get(current.species, [])
    # Entire sets and correlated spread+nature are more robust than arbitrary stat changes.
    operations = ["whole-set", "move", "item", "spread+nature", "species-swap"]
    if mate:
        operations.append("crossover")
    op = rng.choice(operations)
    replacement = current
    if op == "crossover" and mate:
        replacement = rng.choice(mate[1:])
    elif op == "species-swap":
        species = [s for s in pool if s != LOCKED_SPECIES and s not in {p.species for p in team}]
        if not species:
            return team, "no eligible species"
        replacement = rng.choice(pool[rng.choice(species)])
    elif same:
        donor = rng.choice(same)
        if op == "whole-set":
            replacement = donor
        elif op == "item":
            lines = current.text.splitlines()
            lines[0] = lines[0].split(" @ ")[0] + " @ " + donor.item
            replacement = SetBlock("\n".join(lines))
        elif op == "move":
            lines = current.text.splitlines()
            options = [m for m in donor.text.splitlines() if m.startswith("- ") and m not in lines]
            if options:
                targets = [j for j, line in enumerate(lines) if line.startswith("- ")]
                lines[rng.choice(targets)] = rng.choice(options)
                replacement = SetBlock("\n".join(lines))
        elif op == "spread+nature":
            lines = current.text.splitlines()
            spread = next((x for x in donor.text.splitlines() if x.startswith("EVs: ")), None)
            nature = next((x for x in donor.text.splitlines() if x.endswith(" Nature")), None)
            if spread and nature:
                lines = [spread if x.startswith("EVs: ") else nature if x.endswith(" Nature") else x for x in lines]
                replacement = SetBlock("\n".join(lines))
    result = list(team)
    result[i] = replacement
    return tuple(result), f"{op}: {current.species} → {replacement.species} (slot {i+1})"


def run_cli(*parts: object) -> dict[str, Any]:
    proc = subprocess.run(["node", "src/cli/lab.ts", *map(str, parts)], cwd=ENGINE,
                          capture_output=True, text=True, timeout=300, check=False)
    if proc.returncode:
        raise RuntimeError(f"Champions Lab exited {proc.returncode}: {proc.stderr[-1400:]} {proc.stdout[-1400:]}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Champions Lab returned invalid JSON: {proc.stdout[-700:]}") from exc
    if not isinstance(data, dict) or data.get("error"):
        raise RuntimeError(f"Champions Lab error: {str(data)[:1000]}")
    return data


def checked_rate(result: dict[str, Any], key: str, expected: int) -> dict[str, Any]:
    w = result.get(key)
    if not isinstance(w, dict) or w.get("n") != expected or not isinstance(w.get("rate"), (float, int)):
        raise RuntimeError(f"Unexpected {key} for {expected} battles: {str(result)[:900]}")
    return w


@dataclass
class Individual:
    team: tuple[SetBlock, ...]
    parents: tuple[str, ...]
    change: str
    generation: int
    field_rate: float | None = None
    evolved_rate: float | None = None
    score: float | None = None

    @property
    def id(self) -> str:
        return fingerprint(self.team)


def render_record(x: Individual) -> dict[str, Any]:
    return {"id": x.id, "generation": x.generation, "parents": x.parents,
            "change": x.change, "field_rate": x.field_rate,
            "evolved_rate": x.evolved_rate, "selection_score": x.score,
            "species": [p.species for p in x.team]}


def run_experiment(args: argparse.Namespace) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "candidates").mkdir(exist_ok=True)
    manifest = {"started_at": datetime.now(timezone.utc).isoformat(),
                "seed": args.seed, "generations": args.generations, "population": args.population,
                "field_games": args.field_games, "evolved_games": args.evolved_games,
                "holdout_games": args.holdout_games, "engine_commit": ENGINE_SHA,
                "format": "gen9championsvgc2026regmc",
                "status": "running", "tournament_source": str(args.donors),
                "field_source": "data/field-recent.json (required; copied into engine by workflow)",
                "note": "These are bot-versus-bot simulation rates, not real-player performance."}
    def save_manifest() -> None:
        (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    save_manifest()
    try:
        if not (ENGINE / "src/cli/lab.ts").exists():
            raise RuntimeError("Pinned Champions Lab engine missing. Run via cloud workflow.")
        seed_team = parse_team(args.team.read_text(encoding="utf-8"))
        if not locked(seed_team):
            raise ValueError("Seed team must contain Golisopod @ Golisopite in the first slot, once only")
        donors = registry(seed_team, args.donors)
        manifest["registered_donor_species"] = len(donors)
        manifest["registered_donor_sets"] = sum(map(len, donors.values()))
        valid_cache: dict[str, bool] = {}
        def materialize(team: tuple[SetBlock, ...]) -> Path:
            path = OUT / "candidates" / f"{fingerprint(team)}.txt"
            if not path.exists():
                path.write_text(stringify(team), encoding="utf-8")
            return path
        def valid(team: tuple[SetBlock, ...]) -> bool:
            if not locked(team):
                return False
            key = fingerprint(team)
            if key not in valid_cache:
                verdict = run_cli("validate", materialize(team))
                valid_cache[key] = verdict.get("ok") is True
            return valid_cache[key]
        if not valid(seed_team):
            raise RuntimeError("Seed team failed simulator legality validation")
        rng = random.Random(args.seed)
        baseline = Individual(seed_team, (), "seed: current Mega Golisopod", 0)
        history: dict[str, Individual] = {baseline.id: baseline}
        current = [baseline]
        hall: list[Individual] = []
        scores: list[dict[str, Any]] = []
        def replenish(from_parents: list[Individual], generation: int) -> list[Individual]:
            population = list(from_parents)
            used = {p.id for p in population}
            attempts = 0
            while len(population) < args.population and attempts < args.population * 55:
                attempts += 1
                p = rng.choice(from_parents)
                mate = rng.choice(from_parents) if len(from_parents) >= 2 and rng.random() < 0.35 else None
                team, change = mutate(p.team, donors, rng, mate.team if mate else None)
                identifier = fingerprint(team)
                if identifier in used or not valid(team):
                    continue
                child = Individual(team, (p.id, mate.id) if mate else (p.id,), change, generation)
                population.append(child)
                used.add(identifier)
                history.setdefault(identifier, child)
            if len(population) < args.population:
                print(f"WARNING: generated {len(population)}/{args.population} legal unique candidates in gen {generation}", flush=True)
            return population
        current = replenish(current, 0)
        for g in range(args.generations):
            if g:
                # Champion survives, and the second place survives to retain diversity.
                parents = sorted(current, key=lambda x: x.score if x.score is not None else -1, reverse=True)[:2]
                current = replenish([Individual(x.team, x.parents, f"elite from gen {g-1}", g) for x in parents], g)
            cohort: list[dict[str, Any]] = []
            for idx, contender in enumerate(current):
                path = materialize(contender.team)
                # A common seed per generation reduces opponent-sampling noise between candidates.
                result = run_cli("field", path, "--n", args.field_games, "--player", "heuristic",
                                 "--seed", f"{args.seed}|g{g}|field")
                win = checked_rate(result, "winRate", args.field_games)
                contender.field_rate = float(win["rate"])
                sim_rates = []
                rivals = [x for x in hall[-2:] if x.id != contender.id]
                for rival in rivals:
                    duel = run_cli("sim", path, materialize(rival.team), "--n", args.evolved_games,
                                   "--player", "heuristic", "--seed", f"{args.seed}|g{g}|rival:{rival.id}")
                    sim_rates.append(float(checked_rate(duel, "winRateA", args.evolved_games)["rate"]))
                contender.evolved_rate = (sum(sim_rates) / len(sim_rates)) if sim_rates else None
                contender.score = (0.75 * contender.field_rate + 0.25 * contender.evolved_rate
                                   if sim_rates else contender.field_rate)
                cohort.append(render_record(contender))
                print(f"gen {g+1}/{args.generations} {idx+1}/{len(current)} {contender.id} "
                      f"field={contender.field_rate:.1%} score={contender.score:.1%}", flush=True)
            current.sort(key=lambda x: x.score if x.score is not None else -1, reverse=True)
            winning = current[0]
            hall.append(winning)
            history[winning.id] = winning
            scores.append({"generation": g, "best_id": winning.id,
                           "best_selection_score": winning.score, "cohort": cohort})
            (OUT / f"generation-{g:02d}.json").write_text(json.dumps(scores[-1], indent=2), encoding="utf-8")
            manifest["completed_generations"] = g + 1
            manifest["last_champion"] = winning.id
            save_manifest()

        # Reserved holdout seed. Champion chosen on training results, NOT by holdout ranking.
        shortlisted = {x.id: x for x in [baseline, *hall, *current[:3]]}
        validation = []
        for x in shortlisted.values():
            r = run_cli("field", materialize(x.team), "--n", args.holdout_games,
                        "--player", "heuristic", "--seed", f"{args.seed}|HOLDOUT-2026")
            w = checked_rate(r, "winRate", args.holdout_games)
            validation.append({"id": x.id, "rate": w["rate"], "wins": w.get("wins"), "losses": w.get("losses"),
                               "ties": w.get("ties"), "n": w["n"], "ci95": w.get("ci95"),
                               "species": [p.species for p in x.team]})
        validation.sort(key=lambda d: d["rate"], reverse=True)
        winner = current[0]
        winner_result = next(v for v in validation if v["id"] == winner.id)
        (OUT / "best.txt").write_text(stringify(winner.team), encoding="utf-8")
        (OUT / "baseline.txt").write_text(stringify(seed_team), encoding="utf-8")
        (OUT / "lineage.json").write_text(json.dumps({k: render_record(v) for k, v in history.items()}, indent=2), encoding="utf-8")
        (OUT / "holdout.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
        baseline_result = next(v for v in validation if v["id"] == baseline.id)
        report = ["# Poképrotocol Evolution Engine V1", "",
                  "**Experimental M-C simulator optimization. Not real tournament performance.**", "",
                  f"- Seed: `{args.seed}`; {args.generations} generations; up to {args.population} candidate teams each generation.",
                  f"- Each candidate: {args.field_games} fast-AI field games plus {args.evolved_games} games per previous-generation champion (up to two).",
                  f"- Champion selection: 75% real field, 25% evolved opponents when available; independent holdout uses {args.holdout_games} field games.",
                  f"- Registered donor species: {len(donors)}; registered sets: {sum(map(len, donors.values()))}.",
                  f"- Source: `{args.donors}` (registered team sets); engine commit `{ENGINE_SHA[:12]}`.",
                  "- Golisopod @ Golisopite locked. Every candidate passed Showdown's M-C team legality validator.",
                  "- The evolved-opponent population is past champions only. This is **not** a fully coevolving simulated metagame yet.",
                  "- Winning team selected in the final generation *before* examining holdout results. Other holdout rows are diagnostic only.",
                  "", "## Independent holdout", "",
                  "| Team | Rate | Wins/N | 95% CI | Six Pokémon |", "|---|---:|---:|---|---|"]
        for v in validation:
            ci = v["ci95"] or [None, None]
            interval = (f"{ci[0]:.1%}–{ci[1]:.1%}" if all(isinstance(q, (int, float)) for q in ci) else "n/a")
            mark = " **(original)**" if v["id"] == baseline.id else ""
            report.append(f"| `{v['id']}`{mark} | {v['rate']:.1%} | {v['wins']}/{v['n']} | {interval} | {', '.join(v['species'])} |")
        report += ["", f"**Selected champion:** `{winner.id}` ({winner_result['rate']:.1%} held-out); baseline `{baseline.id}` ({baseline_result['rate']:.1%}).",
                   "", "## Generational champions", "",
                   "| Generation | Team ID | Selection score |", "|---:|---|---:|"]
        for rec in scores:
            report.append(f"| {rec['generation']+1} | `{rec['best_id']}` | {rec['best_selection_score']:.1%} |")
        report += ["", "## Suggested next step", "",
                   "Review `best.txt` and the `lineage.json`, then test against full verified championship teams with lookahead AI and actual human opponents.",
                   "This study does not verify M-D legality. Rebuild the engine and field before M-D.", "",
                   "## Best Showdown paste", "", "```", stringify(winner.team).rstrip(), "```", ""]
        (OUT / "summary.md").write_text("\n".join(report), encoding="utf-8")
        manifest.update({"status": "completed", "best_team": winner.id,
                         "baseline_holdout_rate": baseline_result["rate"],
                         "best_holdout_rate": winner_result["rate"],
                         "completed_at": datetime.now(timezone.utc).isoformat()})
        save_manifest()
        print(json.dumps({"status": "completed", "winner": winner.id,
                          "holdout_rate": winner_result["rate"], "baseline_rate": baseline_result["rate"]}))
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = str(exc)
        save_manifest()
        (OUT / "summary.md").write_text("# Evolution experiment failed\n\nNo win-rate claims.\n\n" + str(exc) + "\n", encoding="utf-8")
        traceback.print_exc()
        sys.exit(1)


def get_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Poképrotocol legal team evolution (M-C)")
    p.add_argument("--team", type=Path, default=ROOT / "teams/golisopod-current.txt")
    p.add_argument("--donors", type=Path, default=ROOT / "data/latest-teams.json")
    p.add_argument("--generations", type=int, default=3, choices=range(1, 11))
    p.add_argument("--population", type=int, default=8, choices=range(2, 25))
    p.add_argument("--field-games", type=int, default=40, choices=range(10, 201))
    p.add_argument("--evolved-games", type=int, default=16, choices=range(4, 101))
    p.add_argument("--holdout-games", type=int, default=200, choices=range(40, 501))
    p.add_argument("--seed", default="golisopod-evolve-v1")
    return p.parse_args(argv)


if __name__ == "__main__":
    run_experiment(get_args())