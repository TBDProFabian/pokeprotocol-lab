"""Offline tests for donor harvesting and deduplication."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import build_evolution_donors as donors

def setobj(species, move):
    return {"species":species,"item":"Leftovers","ability":"Stamina",
            "nature":"Calm","level":50,
            "moves":[move,"Dragon Pulse","Aura Sphere","Protect"],
            "evs":{"hp":32,"def":1,"spa":1,"spd":25,"spe":7}}

class DonorTests(unittest.TestCase):
    def test_deduped_arch_alternatives(self):
        a=setobj("Archaludon","Electro Shot")
        b=setobj("Archaludon","Flash Cannon")
        c=setobj("Unpermitted","Tackle")
        rows=[{"event":"first","sets":[a,c]},
              {"event":"second","sets":[a,b]}]
        kept,counts=donors.dedupe(rows,{"Archaludon"})
        self.assertEqual(counts["Archaludon"],2)
        self.assertEqual(len(kept),2)
        self.assertEqual(sum(len(r["sets"]) for r in kept),2)
    def test_gather_uses_field_query(self):
        with patch.object(donors,"run_cli",return_value={"teams":[{"sets":[]}]}) as call:
            self.assertEqual(len(donors.gather("Archaludon",20)),1)
            call.assert_called_once_with("teams","--species","Archaludon","--limit","20")
    def test_invalid_set_not_in_pool(self):
        bad=setobj("Archaludon","Flash Cannon")
        bad["evs"]["hp"]=99
        _,count=donors.dedupe([{"sets":[bad]}],{"Archaludon"})
        self.assertEqual(count,{})

if __name__=="__main__":
    unittest.main()
