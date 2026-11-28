"""User preference: ordinary Salamence must not reappear in primary Mega Golisopod runs."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from evolve import parse_team,has_excluded_species,get_args

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"teams/golisopod-salamence-replacement-baseline.txt"

class ExclusionTests(unittest.TestCase):
    def test_cli_accepts_repeated_species_exclusions(self):
        args=get_args(["--exclude-species","Salamence","--exclude-species","Staraptor","--only-mega-golisopod"])
        self.assertEqual(args.exclude_species,["Salamence","Staraptor"])
        self.assertTrue(args.only_mega_golisopod)
    def test_excluded_species_case_insensitive(self):
        team=parse_team(BASE.read_text(encoding="utf8"))
        self.assertTrue(has_excluded_species(team,{"salamence"}))
        self.assertTrue(has_excluded_species(team,{"salamence","staraptor"}))
        self.assertFalse(has_excluded_species(team,{"incineroar","staraptor"}))
    def test_current_workflow_excludes_salamence(self):
        workflow=(ROOT/".github/workflows/evolve.yml").read_text(encoding="utf8")
        self.assertIn("--only-mega-golisopod",workflow)
        self.assertIn("--exclude-species Salamence",workflow)
    def test_replacing_salamence_releases_preference_lock(self):
        from replace_salamence import variant,SETS
        orig=BASE.read_text()
        replaced=parse_team(variant(orig,"Staraptor | balanced Intimidate/Tailwind"))
        self.assertFalse(has_excluded_species(replaced,{"salamence"}))
        self.assertTrue(has_excluded_species(replaced,{"staraptor"}))

if __name__=="__main__":
    unittest.main()
