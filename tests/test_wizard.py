"""Run with:  python3 -m unittest discover tests"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wizard"))
import wizard  # noqa: E402

BANNED = {"\u2014": "em dash", "\u2013": "en dash", "\u00b7": "middle dot"}


class WizardTest(unittest.TestCase):
    def answers(self, **changes):
        return wizard.validate({**json.loads((ROOT / "example-answers.json").read_text()), **changes})

    def test_slug_matches_home_assistant_area_ids(self):
        self.assertEqual(wizard.slug("Living Room"), "living_room")
        self.assertEqual(wizard.slug("Kid's Room 2"), "kid_s_room_2")

    def test_bad_answers_are_refused(self):
        for bad in ({"rooms": []}, {"rooms": ["Den", "den"]}, {"arrival_room": "Garage"},
                    {"leave_delay_minutes": 0}, {"notify": ["Mobile App!"]}, {"rooms": ["Café"]}):
            with self.assertRaises(wizard.AnswerError, msg=bad):
                self.answers(**bad)

    def test_choices_change_the_routines(self):
        off = wizard.routines_yaml(self.answers(lock_when_leaving=False, blinds=False))
        on = wizard.routines_yaml(self.answers(lock_when_leaving=True, blinds=True))
        self.assertNotIn("lock.lock", off)
        self.assertIn("lock.lock", on)
        self.assertIn("cover.close_cover", on)

    def test_notify_names_and_rooms_land_in_the_files(self):
        files = wizard.build(self.answers(notify=["notify.mobile_app_alex"], battery_check=False))
        self.assertIn("action: notify.mobile_app_alex", files["packages/house.yaml"])
        self.assertIn("area: living_room", files["dashboards/home.yaml"])
        self.assertNotIn("packages/maintenance.yaml", files)

    def test_written_files_have_no_ai_punctuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            wizard.write(wizard.build(self.answers()), Path(tmp))
            texts = [p.read_text(encoding="utf-8") for p in Path(tmp).rglob("*.yaml")]
        self.assertEqual(len(texts), 9)
        for text in texts:
            for char, name in BANNED.items():
                self.assertNotIn(char, text, name)

    def test_shipped_config_matches_the_example_answers(self):
        for rel, text in wizard.build(self.answers()).items():
            self.assertEqual((ROOT / "config" / rel).read_text(encoding="utf-8"), text, rel)


if __name__ == "__main__":
    unittest.main()
