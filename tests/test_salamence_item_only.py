"""Keep the Focus Sash vs Sand Stream analysis single-variable and reproducible."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import audit_salamence_item_only as audit
from evolve import parse_team,exclusive_mega_golisopod

class ItemOnlyTests(unittest.TestCase):
    def test_six_and_salamence_move_spread_unchanged(self):
        original=parse_team(audit.SEED_TEAM.read_text(encoding="utf8"))
        self.assertTrue(exclusive_mega_golisopod(original))
        for item in audit.ITEMS:
            altered=parse_team(audit.change_item(audit.SEED_TEAM.read_text(encoding="utf8"),item))
            self.assertTrue(exclusive_mega_golisopod(altered))
            for a,b in zip(original,altered):
                if a.species=="Salamence":
                    self.assertEqual(b.item,item)
                    self.assertEqual(b.text.splitlines()[1:],a.text.splitlines()[1:])
                else:
                    self.assertEqual(a.text,b.text)
    def test_drifted_seed_fails(self):
        with self.assertRaises(RuntimeError):
            audit.change_item(audit.SEED_TEAM.read_text(encoding="utf8").replace(
                 "Salamence @ Focus Sash","Salamence @ Haban Berry"),"Sitrus Berry")
    def test_log_analysis_does_not_duplicate_split_messages(self):
        log={"logs":[{"log":[
             "|-weather|Sandstorm|[from] ability: Sand Stream|[of] p1b: Tyranitar",
             "|-damage|p1a: Salamence|80/100|[from] Sandstorm",
             "|-damage|p1a: Salamence|120/150|[from] Sandstorm",
             "|-enditem|p1a: Salamence|Focus Sash",
             "|-enditem|p1a: Salamence|Focus Sash"]}]}
        info=audit.inspect_logs(log)
        self.assertEqual(info["sash_activation_games"],1)
        self.assertEqual(info["our_salamence_sand_damage_games"],1)
        self.assertEqual(info["our_tyranitar_sand_starts"],1)

if __name__=="__main__":
    unittest.main()
