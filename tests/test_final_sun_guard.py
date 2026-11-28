"""Fire/Sun acceptance gate validates exact registered opponent and user preference."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import final_sun_guard as g
from replace_salamence import variant
from evolve import parse_team,exclusive_mega_golisopod

class FinalSunGuardTests(unittest.TestCase):
    def test_all_replacements_keep_golisopite_only_and_no_salamence(self):
        original=g.TEAM.read_text(encoding="utf8")
        for name in g.CANDIDATES:
            team=parse_team(variant(original,name))
            self.assertTrue(exclusive_mega_golisopod(team),name)
            self.assertNotIn("Salamence",[p.species for p in team])
            self.assertEqual(len(set(p.item for p in team)),6)
    def test_complete_real_sun_tournament_sheet_sources(self):
        opponents,provenance=g.opponents()
        self.assertEqual(len(opponents),4)
        self.assertEqual(len(provenance),2)
        for name,source in provenance.items():
            self.assertEqual(source["placing"],1)
            self.assertEqual(len(source["species"]),6)
            self.assertIn("Charizard",source["species"])
    def test_mega_usage_threshold_predeclared(self):
        self.assertEqual(g.NFIELD,180)
        self.assertEqual(g.NHOLDOUT,320)
        self.assertEqual(g.POLICY,"POKEPROTOCOL_WEATHER_PREVIEW_V2")

if __name__=="__main__":
    unittest.main()
