"""Weather-preview patch guards and approximate weather/tempo semantics."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from install_weather_preview import patched, HIT, DAMAGE, DUEL, KEY, BOTH, BRING, LEAD, MARKER

class WeatherPreviewTests(unittest.TestCase):
    def test_reject_unpinned_source(self):
        with self.assertRaises(RuntimeError):
            patched("not a pinned preview policy")
    def test_patch_correctly_rewrites_all_anchors(self):
        src = "\n".join([HIT,DAMAGE,DUEL,KEY,BOTH,BRING,LEAD])
        out = patched(src)
        self.assertIn(MARKER,out)
        self.assertIn("function bestHit(dex: Dex, a: Unit, d: Unit, w: WeatherOdds)",out)
        self.assertIn("const w = estimateWeather(dex, mine, theirs)",out)
        self.assertIn("chargeTempo(mv, a.set.item, w)",out)
        self.assertIn("rain.toFixed(2)",out)
        self.assertIn("sun.toFixed(2)",out)
        self.assertIn("0.45 + 0.55",out)
        self.assertIn("powerherb",out)
        self.assertIn("sandstream",out)
        self.assertIn("drizzle",out)
        with self.assertRaises(RuntimeError):
            patched(out)
    def test_reject_duplicate_anchor(self):
        src = "\n".join([HIT,DAMAGE,DUEL,KEY,BOTH,BRING,LEAD,DUEL])
        with self.assertRaises(RuntimeError):
            patched(src)

if __name__ == "__main__":
    unittest.main()
