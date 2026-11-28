"""Unit and offline-smoke tests for the evolution engine (no external dependencies)."""
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import evolve


def fake_set(species: str, item: str = "Sitrus Berry", offset: int = 0) -> str:
    moves = ["Protect", "Helping Hand", "Tackle", "Quick Attack"]
    if offset:
        moves[-1] = "Swords Dance"
    return "\n".join([f"{species} @ {item}", "Ability: Pressure", "Level: 50",
                      "EVs: 2 HP / 32 Atk / 32 Spe", "Adamant Nature",
                      *["- " + move for move in moves]])


class GeneticsTests(unittest.TestCase):
    def setUp(self):
        self.species = ["Golisopod", "Salamence", "Rillaboom", "Pelipper", "Archaludon", "Basculegion-F"]
        self.items = ["Golisopite", "Salamencite", "Miracle Seed", "Damp Rock", "Leftovers", "Focus Sash"]
        self.seed = evolve.parse_team("\n\n".join(fake_set(s, item) for s, item in zip(self.species, self.items)))

    def test_parse_and_locked_anchor(self):
        self.assertTrue(evolve.locked(self.seed))
        self.assertEqual(len(evolve.parse_team(evolve.stringify(self.seed))), 6)
        broken = list(self.seed)
        broken[0] = evolve.SetBlock(fake_set("Golisopod", "Focus Sash"))
        self.assertFalse(evolve.locked(tuple(broken)))

    def test_registered_set_preserves_actual_spread_and_moves(self):
        record = {"species": "Corviknight", "item": "Rocky Helmet", "ability": "Mirror Armor",
                  "nature": "Impish", "moves": ["Tailwind", "Brave Bird", "Roost", "Protect"],
                  "evs": {"hp": 32, "atk": 0, "def": 32, "spd": 2, "spe": 0, "spa": 0}}
        s = evolve.registered_set(record)
        self.assertEqual(s.species, "Corviknight")
        self.assertIn("EVs: 32 HP / 32 Def / 2 SpD", s.text)
        self.assertIn("- Roost", s.text)
        record["evs"]["hp"] = 40
        self.assertIsNone(evolve.registered_set(record))

    def test_mega_golisopod_exclusivity_rejects_partner_stones(self):
        candidates=list(self.seed)
        self.assertFalse(evolve.exclusive_mega_golisopod(tuple(candidates)))
        candidates[1]=evolve.SetBlock(fake_set("Salamence","Focus Sash"))
        self.assertTrue(evolve.exclusive_mega_golisopod(tuple(candidates)))
        eviolite=list(candidates)
        eviolite[2]=evolve.SetBlock(fake_set("Rillaboom","Eviolite"))
        self.assertTrue(evolve.exclusive_mega_golisopod(tuple(eviolite)))
        for extra_item in ("Tyranitarite","Raichunite X","Garchompite Z"):
            adjusted=list(candidates)
            adjusted[2]=evolve.SetBlock(fake_set("Rillaboom",extra_item))
            self.assertFalse(evolve.exclusive_mega_golisopod(tuple(adjusted)))

    def test_many_mutations_keep_anchor_intact(self):
        extra = ["Corviknight", "Tyranitar", "Excadrill", "Raichu"]
        pool = {s: [b, evolve.SetBlock(fake_set(s, b.item, 1))] for s, b in zip(self.species, self.seed)}
        for s in extra:
            pool[s] = [evolve.SetBlock(fake_set(s))]
        rng = random.Random(1234)
        kinds = set()
        for _ in range(350):
            result, description = evolve.mutate(self.seed, pool, rng, self.seed)
            kinds.add(description.split(":")[0])
            self.assertEqual(result[0], self.seed[0])
            if evolve.locked(result):
                self.assertEqual(len({p.species for p in result}), 6)
        self.assertIn("species-swap", kinds)
        self.assertIn("crossover", kinds)

    def test_offline_evolution_run_creates_report(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            teamfile = root / "team.txt"
            teamfile.write_text(evolve.stringify(self.seed), encoding="utf-8")
            donorsfile = root / "donors.json"
            species = ["Corviknight", "Tyranitar", "Excadrill", "Raichu", "Kingambit", "Metagross"]
            registered = []
            for name in species + self.species[1:]:
                registered.append({"species": name, "item": "Sitrus Berry", "ability": "Pressure",
                                   "nature": "Adamant", "moves": ["Protect", "Helping Hand", "Tackle", "Quick Attack"],
                                   "evs": {"hp": 2, "atk": 32, "spe": 32}})
            donorsfile.write_text(json.dumps({"teams": [{"sets": registered}]}), encoding="utf-8")
            (root / "engine" / "src/cli").mkdir(parents=True)
            (root / "engine" / "src/cli/lab.ts").write_text("stub", encoding="utf-8")
            fake_out = root / "reports/evolution"

            def fake_cli(command, team, *arguments):
                t = evolve.parse_team(Path(team).read_text())
                if command == "validate":
                    return {"ok": evolve.locked(t)}
                n = int(arguments[arguments.index("--n") + 1])
                # Stable fake signal for tournament-donor substitutions.
                rate = 0.55 if any(p.species == "Corviknight" for p in t) else 0.5
                return {("winRateA" if command == "sim" else "winRate"):
                        {"rate": rate, "n": n, "wins": round(n * rate), "losses": n - round(n * rate),
                         "ties": 0, "ci95": [max(rate - 0.1, 0), min(rate + 0.1, 1)]}}

            args = evolve.get_args(["--team", str(teamfile), "--donors", str(donorsfile),
                                     "--population", "4", "--generations", "2",
                                     "--field-games", "10", "--evolved-games", "4",
                                     "--holdout-games", "40", "--seed", "test"])
            with patch.object(evolve, "ENGINE", root / "engine"), patch.object(evolve, "OUT", fake_out), patch.object(evolve, "run_cli", fake_cli):
                evolve.run_experiment(args)
            report = (fake_out / "summary.md").read_text()
            manifest = json.loads((fake_out / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["completed_generations"], 2)
            self.assertTrue(evolve.locked(evolve.parse_team((fake_out / "best.txt").read_text())))
            self.assertIn("Independent holdout", report)
            self.assertTrue((fake_out / "lineage.json").exists())
            self.assertTrue((fake_out / "promotion.json").exists())
            self.assertIn("Global promotion round", report)
            self.assertEqual(manifest["global_promotion_winner"], manifest["best_team"])


    def test_global_promotion_may_keep_baseline_despite_lucky_last_generation(self):
        """Final selection must use the fixed promotion field, not last gen or holdout."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            teamfile = root / "team.txt"
            teamfile.write_text(evolve.stringify(self.seed), encoding="utf-8")
            donorsfile = root / "donors.json"
            names = ["Corviknight", "Tyranitar", "Excadrill", "Raichu", "Kingambit", "Metagross"]
            recorded = [
                {"species": name, "item": "Sitrus Berry", "ability": "Pressure",
                 "nature": "Adamant", "moves": ["Protect", "Helping Hand", "Tackle", "Quick Attack"],
                 "evs": {"hp": 2, "atk": 32, "spe": 32}}
                for name in names + self.species[1:]
            ]
            donorsfile.write_text(json.dumps({"teams": [{"sets": recorded}]}), encoding="utf8")
            (root / "engine/src/cli").mkdir(parents=True)
            (root / "engine/src/cli/lab.ts").write_text("stub", encoding="utf8")
            fake_out = root / "reports/evolution"

            def fake_cli(command, team, *arguments):
                current = evolve.parse_team(Path(team).read_text())
                if command == "validate":
                    return {"ok": evolve.locked(current)}
                n = int(arguments[arguments.index("--n") + 1])
                seed = arguments[arguments.index("--seed") + 1]
                baseline = current == self.seed
                if "PROMOTION" in seed:
                    rate = 0.9 if baseline else 0.1
                elif "HOLDOUT" in seed:
                    rate = 0.1 if baseline else 0.9
                else:
                    rate = 0.4 if baseline else 0.8
                wins = round(rate*n)
                return {("winRateA" if command == "sim" else "winRate"): {
                    "rate": rate, "wins": wins, "losses": n-wins, "ties": 0,
                    "n": n, "ci95": [0,1]}}

            args = evolve.get_args([
                "--team", str(teamfile), "--donors", str(donorsfile),
                "--population", "4", "--generations", "2",
                "--field-games", "10", "--evolved-games", "4",
                "--promotion-games", "40", "--holdout-games", "40", "--seed", "regression"])
            with patch.object(evolve, "ENGINE", root / "engine"), \
                 patch.object(evolve, "OUT", fake_out), \
                 patch.object(evolve, "run_cli", fake_cli):
                evolve.run_experiment(args)

            manifest = json.loads((fake_out / "manifest.json").read_text())
            self.assertEqual(manifest["best_team"], evolve.fingerprint(self.seed))
            promotion = json.loads((fake_out / "promotion.json").read_text())
            self.assertEqual(promotion[0]["id"], evolve.fingerprint(self.seed))
            holdout = json.loads((fake_out / "holdout.json").read_text())
            self.assertTrue(any(x["rate"] == 0.9 for x in holdout))
            self.assertEqual(manifest["best_holdout_rate"], 0.1)


if __name__ == "__main__":
    unittest.main()