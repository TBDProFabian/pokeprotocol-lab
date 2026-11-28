"""Offline regression coverage for the M-C/M-D boundary and lab inputs."""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pre_md_audit import validate_roster, validate_field, OTHER_REGULATION, M_C_FORMAT

ROOT = Path(__file__).resolve().parents[1]

class PreMDAuditTests(unittest.TestCase):
    def test_real_current_roster_is_single_mega_and_six_unique_items(self):
        x=validate_roster((ROOT/"teams/golisopod-current.txt").read_text())
        self.assertEqual(x["mega"], "Golisopod")
        self.assertNotIn("Salamence",x["species"])
        self.assertEqual(len(x["items"]),6)
    def test_reject_duplicate_item(self):
        text=(ROOT/"teams/golisopod-current.txt").read_text().replace("Corviknight @ Sitrus Berry","Corviknight @ Chople Berry")
        with self.assertRaisesRegex(ValueError,"Item Clause"):
            validate_roster(text)
    def test_reject_other_mega(self):
        text=(ROOT/"teams/golisopod-current.txt").read_text().replace("Tyranitar @ Chople Berry","Tyranitar @ Tyranitarite")
        with self.assertRaisesRegex(ValueError,"Only Golisopite"):
            validate_roster(text)
    def test_reject_bad_stat_points(self):
        text=(ROOT/"teams/golisopod-current.txt").read_text().replace("2 HP / 32 Atk / 32 Spe", "2 HP / 31 Atk / 32 Spe",1)
        with self.assertRaisesRegex(ValueError,"66 Stat Points"):
            validate_roster(text)
    def test_regulation_label_classifier(self):
        for name in ("Reg I 2026", "Reg J", "M-D tournament", "regulation set M-D", "Regulation B", "Singles Cup"):
            self.assertIsNotNone(OTHER_REGULATION.search(name),name)
        for name in ("Regulation M-C Invitational", "2026 M-C Doubles", "champions M/C #8", "Open Finals"):
            self.assertIsNone(OTHER_REGULATION.search(name),name)
    def test_refresh_mutex_is_job_scoped_not_workflow_scoped(self):
        workflow=(ROOT/".github/workflows/refresh-database.yml").read_text(encoding="utf8")
        before_jobs, jobs = workflow.split("\njobs:\n",1)
        self.assertNotIn("concurrency:",before_jobs)
        self.assertIn("    concurrency:\n      group: pokeprotocol-field-refresh",jobs)
        self.assertIn("    if: >-",jobs)
    def test_reject_wrong_field_and_stale_refresh(self):
        now=datetime(2026,11,28,tzinfo=timezone.utc)
        base={"meta":{"sources":[{"name":"Champions M-C", "reg":"M-C"} for _ in range(3)]},
              "teams":[{"reg":"M-C"} for _ in range(30)]}
        audit={"format":M_C_FORMAT,"refreshedAt":"2026-11-26T00:00:00Z"}
        self.assertEqual(validate_field(base,audit,now=now)["field_teams"],30)
        base["meta"]["sources"][0]["name"]="Runback - Reg I"
        with self.assertRaisesRegex(ValueError,"Non-M-C"):
            validate_field(base,audit,now=now)
        base["meta"]["sources"][0]["name"]="Champions M-C"
        with self.assertRaisesRegex(ValueError,"stale"):
            validate_field(base,audit,now=datetime(2026,12,15,tzinfo=timezone.utc))
if __name__=="__main__":
    unittest.main()
