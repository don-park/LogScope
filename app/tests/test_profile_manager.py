import os
import tempfile
import unittest
import yaml
from app.parser import ProfileManager
from app.model import AnalysisProfile, FilterConfig, PatternConfig, PlotConfig, VisualizationConfig


SAMPLE_PROFILE = {
    "name": "Test Profile",
    "filter": {"tag": "MY_TAG", "keyword": "some_func"},
    "patterns": [
        {"type": "key_value", "params": {"separator": "="}},
        {"type": "segment",   "params": {"delimiter": "|"}},
    ],
    "visualization": {
        "layout": "grid",
        "plots": [
            {"title": "Plot A", "keys": ["x", "y"], "y_label": "unit"},
            {"title": "Plot B", "keys": ["z"]},
        ],
    },
}


class TestProfileManager(unittest.TestCase):

    def _make_dir(self, profiles: list[dict]) -> str:
        d = tempfile.mkdtemp()
        for p in profiles:
            path = os.path.join(d, p["name"].replace(" ", "_") + ".yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(p, f, allow_unicode=True)
        return d

    # ---------------------------------------------------------------- loading
    def test_load_sample_profile_from_default_dir(self):
        pm = ProfileManager()
        self.assertIn("AF BFC Scan", pm.list_profiles())

    def test_loaded_profile_is_analysis_profile_instance(self):
        pm = ProfileManager()
        profile = pm.get("AF BFC Scan")
        self.assertIsInstance(profile, AnalysisProfile)

    def test_af_bfc_filter(self):
        pm = ProfileManager()
        p = pm.get("AF BFC Scan")
        self.assertEqual(p.filter.tag, "AF_DEBUG")
        self.assertEqual(p.filter.keyword, "BFC scanning")

    def test_af_bfc_has_one_pattern(self):
        pm = ProfileManager()
        p = pm.get("AF BFC Scan")
        self.assertEqual(len(p.patterns), 1)
        self.assertEqual(p.patterns[0].type, "segment")

    def test_af_bfc_visualization_has_three_plots(self):
        pm = ProfileManager()
        p = pm.get("AF BFC Scan")
        self.assertEqual(len(p.visualization.plots), 3)
        self.assertEqual(p.visualization.plots[0].title, "Lens Position")

    # -------------------------------------------- custom dir / load_file
    def test_load_from_custom_directory(self):
        d = self._make_dir([SAMPLE_PROFILE])
        pm = ProfileManager(profiles_dir=d)
        self.assertIn("Test Profile", pm.list_profiles())

    def test_profile_fields_parsed_correctly(self):
        d = self._make_dir([SAMPLE_PROFILE])
        pm = ProfileManager(profiles_dir=d)
        p = pm.get("Test Profile")
        self.assertIsInstance(p.filter, FilterConfig)
        self.assertEqual(p.filter.tag, "MY_TAG")
        self.assertEqual(p.filter.keyword, "some_func")
        self.assertEqual(len(p.patterns), 2)
        self.assertIsInstance(p.patterns[0], PatternConfig)
        self.assertEqual(p.patterns[0].type, "key_value")
        self.assertEqual(p.patterns[0].params["separator"], "=")
        self.assertIsInstance(p.visualization, VisualizationConfig)
        self.assertEqual(p.visualization.layout, "grid")
        self.assertEqual(len(p.visualization.plots), 2)
        self.assertIsInstance(p.visualization.plots[0], PlotConfig)
        self.assertEqual(p.visualization.plots[0].title, "Plot A")
        self.assertEqual(p.visualization.plots[0].keys, ["x", "y"])
        self.assertEqual(p.visualization.plots[0].y_label, "unit")
        self.assertIsNone(p.visualization.plots[1].y_label)

    def test_load_file_adds_profile(self):
        pm = ProfileManager(profiles_dir=tempfile.mkdtemp())
        f = tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False, encoding="utf-8")
        yaml.dump(SAMPLE_PROFILE, f, allow_unicode=True)
        f.close()
        loaded = pm.load_file(f.name)
        self.assertEqual(loaded.name, "Test Profile")
        self.assertIn("Test Profile", pm.list_profiles())
        os.unlink(f.name)

    def test_yml_extension_also_loaded(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "test.yml")
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(SAMPLE_PROFILE, f, allow_unicode=True)
        pm = ProfileManager(profiles_dir=d)
        self.assertIn("Test Profile", pm.list_profiles())

    # ---------------------------------------------------------- edge cases
    def test_empty_profiles_dir_returns_empty_list(self):
        pm = ProfileManager(profiles_dir=tempfile.mkdtemp())
        self.assertEqual(pm.list_profiles(), [])

    def test_nonexistent_dir_returns_empty_list(self):
        pm = ProfileManager(profiles_dir="/nonexistent/path/xyz")
        self.assertEqual(pm.list_profiles(), [])

    def test_get_unknown_profile_returns_none(self):
        pm = ProfileManager()
        self.assertIsNone(pm.get("does not exist"))

    def test_malformed_yaml_file_is_skipped(self):
        d = tempfile.mkdtemp()
        bad = os.path.join(d, "bad.yaml")
        with open(bad, "w") as f:
            f.write("name: [unclosed bracket")
        pm = ProfileManager(profiles_dir=d)
        self.assertEqual(pm.list_profiles(), [])

    def test_list_profiles_is_sorted(self):
        d = self._make_dir([
            {**SAMPLE_PROFILE, "name": "Zebra"},
            {**SAMPLE_PROFILE, "name": "Alpha"},
        ])
        pm = ProfileManager(profiles_dir=d)
        names = pm.list_profiles()
        self.assertEqual(names, sorted(names))

    def test_filter_tag_none_when_omitted(self):
        profile = {**SAMPLE_PROFILE, "filter": {"keyword": "only_keyword"}}
        d = self._make_dir([profile])
        pm = ProfileManager(profiles_dir=d)
        p = pm.get("Test Profile")
        self.assertIsNone(p.filter.tag)
        self.assertEqual(p.filter.keyword, "only_keyword")


if __name__ == "__main__":
    unittest.main()
