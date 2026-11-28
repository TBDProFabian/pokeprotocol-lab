"""Offline tests of the Mega-Golisopod-only roster guard."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import test_goli_mega_usage as audit
from evolve import parse_team,locked

class MegaGolisopodGuardTests(unittest.TestCase):
    def test_sand_only_golisopite_remains(self):
        text=audit.change_to_goli_only(audit.SAND.read_text())
        mons=parse_team(text)
        self.assertTrue(locked(mons))
        self.assertEqual([x.item for x in mons if x.item.lower().endswith("ite")],["Golisopite"])
        self.assertIn("Salamence @ Focus Sash",text)
        self.assertIn("Tyranitar @ Chople Berry",text)
    def test_rain_only_golisopite_remains(self):
        text=audit.change_to_goli_only(audit.RAIN.read_text())
        self.assertTrue(locked(parse_team(text)))
        self.assertNotIn("Salamencite",text)
    def test_tailwind_whimsicott_replacement(self):
        text=audit.change_to_goli_only(audit.SAND.read_text(),True)
        self.assertIn("Whimsicott @ Focus Sash",text)
        self.assertNotIn("Salamence @",text)
        self.assertTrue(locked(parse_team(text)))
    def test_prevent_unsupported_sources(self):
        with self.assertRaises(ValueError):
            audit.change_to_goli_only(audit.SAND.read_text().replace("Salamencite","Leftovers"))

if __name__=="__main__":
    unittest.main()
