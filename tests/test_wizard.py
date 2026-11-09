"""Fast offline checks. Run with:  python3 -m unittest discover tests
(The end-to-end test with a real Home Assistant is tests/integration_test.py and needs Docker.)"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "donkeyhome" / "app"
sys.path.insert(0, str(APP))
TMP = Path(tempfile.mkdtemp(prefix="donkeyhome-unit-"))
os.environ["CONFIG_DIR"] = str(TMP / "config")  # read by server.py at import
os.environ["DATA_DIR"] = str(TMP / "data")
import server  # noqa: E402
import wizard  # noqa: E402

BANNED = {"\u2014": "em dash", "\u2013": "en dash", "\u00b7": "middle dot"}


def answers(**changes):
    return wizard.validate({**json.loads((ROOT / "example-answers.json").read_text()), **changes})


class WizardTest(unittest.TestCase):
    def test_slug_matches_home_assistant_area_ids(self):
        self.assertEqual(wizard.slug("Living Room"), "living_room")
        self.assertEqual(wizard.slug("Kid's Room 2"), "kid_s_room_2")

    def test_bad_answers_are_refused(self):
        for bad in ({"rooms": []}, {"rooms": ["Den", "den"]}, {"arrival_room": "Garage"},
                    {"leave_delay_minutes": 0}, {"notify": ["Mobile App!"]}, {"rooms": ["Café"]},
                    {"area_ids": {"Kitchen": "../etc"}}):
            with self.assertRaises(wizard.AnswerError, msg=bad):
                answers(**bad)

    def test_choices_change_the_routines(self):
        off = wizard.routines_yaml(answers(lock_when_leaving=False, blinds=False))
        on = wizard.routines_yaml(answers(lock_when_leaving=True, blinds=True))
        self.assertNotIn("lock.lock", off)
        self.assertIn("lock.lock", on)
        self.assertIn("cover.close_cover", on)

    def test_real_area_ids_are_used(self):
        files = wizard.build(answers(area_ids={"Living Room": "lounge_2"}))
        self.assertIn("area: lounge_2", files["dashboards/home.yaml"])
        self.assertIn("area_id: lounge_2", files["packages/routines.yaml"])
        self.assertIn("area: kitchen", files["dashboards/home.yaml"])

    def test_notify_names_and_rooms_land_in_the_files(self):
        files = wizard.build(answers(notify=["notify.mobile_app_alex"], battery_check=False))
        self.assertIn("action: notify.mobile_app_alex", files["packages/house.yaml"])
        self.assertIn("area: living_room", files["dashboards/home.yaml"])
        self.assertNotIn("packages/maintenance.yaml", files)

    def test_write_keeps_your_own_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "automations.yaml").write_text("- id: mine\n")
            (out / "packages").mkdir()
            (out / "packages" / "mine.yaml").write_text("# my own package\n")
            wizard.write(wizard.build(answers()), out)
            self.assertEqual((out / "automations.yaml").read_text(), "- id: mine\n")
            self.assertTrue((out / "packages" / "mine.yaml").exists())
            self.assertTrue((out / "packages" / "maintenance.yaml").exists())
            _, deleted = wizard.write(wizard.build(answers(battery_check=False)), out)
            self.assertEqual(deleted, ["packages/maintenance.yaml"])
            self.assertFalse((out / "packages" / "maintenance.yaml").exists())

    def test_written_files_have_no_ai_punctuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            wizard.write(wizard.build(answers()), Path(tmp))
            texts = [p.read_text(encoding="utf-8") for p in Path(tmp).rglob("*.yaml")]
        self.assertEqual(len(texts), 11)
        for text in texts:
            for char, name in BANNED.items():
                self.assertNotIn(char, text, name)

    def test_shipped_example_config_is_up_to_date(self):
        for rel, data in wizard.build(answers()).items():
            path = ROOT / "config" / rel
            self.assertEqual(path.read_bytes() if isinstance(data, bytes) else path.read_text(encoding="utf-8"), data, rel)

    def test_dashboard_template_is_fully_filled(self):
        dash = wizard.build(answers())["dashboards/home.yaml"]
        self.assertNotIn("@@", dash)
        for room in ("living-room", "kitchen", "bedroom", "bathroom"):
            self.assertIn(f"path: room-{room}", dash)
        self.assertIn("type: home-area", dash)

    def test_licensed_canela_font_is_never_shipped(self):
        for rel, data in wizard.build(answers()).items():
            self.assertNotIn("canela", rel.lower())
            if isinstance(data, str):
                self.assertNotIn("Canela", data, rel)


class AppTest(unittest.TestCase):
    def setUp(self):
        self.cfg = server.CONFIG_DIR
        self.cfg.mkdir(parents=True, exist_ok=True)
        for f in self.cfg.rglob("*"):
            if f.is_file():
                f.unlink()

    def test_config_status(self):
        self.assertEqual(server.config_status(), "missing")
        (self.cfg / "configuration.yaml").write_text(
            "# Loads default set of integrations. Do not remove.\ndefault_config:\n\nfrontend:\n"
            "  themes: !include_dir_merge_named themes\n\nautomation: !include automations.yaml\n"
            "script: !include scripts.yaml\nscene: !include scenes.yaml\n")
        self.assertEqual(server.config_status(), "fresh")
        (self.cfg / "configuration.yaml").write_text("default_config:\nhttp:\n  server_port: 9000\n")
        self.assertEqual(server.config_status(), "custom")
        (self.cfg / "configuration.yaml").write_text(wizard.configuration_yaml(answers()))
        self.assertEqual(server.config_status(), "donkeyhome")

    def test_backup_and_restore_put_everything_back(self):
        (self.cfg / "configuration.yaml").write_text("old\n")
        files = wizard.build(answers())
        to_write, _ = wizard.plan(files, self.cfg)
        folder, new = server.backup(list(to_write))
        wizard.write(files, self.cfg)
        self.assertIn("packages/routines.yaml", new)
        server.restore(folder, new)
        self.assertEqual((self.cfg / "configuration.yaml").read_text(), "old\n")
        self.assertFalse((self.cfg / "packages" / "routines.yaml").exists())

    def test_phone_label(self):
        self.assertEqual(server.phone_label("mobile_app_alex_iphone"), "Alex Iphone")


if __name__ == "__main__":
    unittest.main()
