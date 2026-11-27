"""Check the diagnostic preview patch fails safely when source changes."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from compare_preview_charge import patched_source, variant, ANCHOR

class ChargePreviewTests(unittest.TestCase):
    def test_preview_patch_is_exactly_once(self):
        s="before\n"+ANCHOR+"\nafter"
        patched=patched_source(s)
        self.assertIn("chargeTempo",patched)
        self.assertIn("0.45",patched)
        self.assertNotIn(ANCHOR,patched)
    def test_patch_refuses_unknown_engine(self):
        with self.assertRaises(RuntimeError):
            patched_source("unrelated engine")
        with self.assertRaises(RuntimeError):
            patched_source(ANCHOR+"\n"+ANCHOR)
    def test_move_variant_preserves_rest_of_team(self):
        team="- Electro Shot\n- Protect\n"
        self.assertEqual(variant(team,"Flash Cannon"),"- Flash Cannon\n- Protect\n")
        with self.assertRaises(RuntimeError):
            variant("- Protect", "Flash Cannon")

if __name__=="__main__":
    unittest.main()
