import os
import tempfile
import unittest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app.parser import LogParser, ProfileManager, RuleEngine
from app.visualize import PlotEngine
from app.model.profile import VisualizationConfig, PlotConfig
from app.model.parsed_data import ExtractionResult, ExtractedEntry
from datetime import datetime


def _make_entries(n: int) -> list[ExtractedEntry]:
    base = datetime(2024, 4, 17, 10, 0, 0)
    from datetime import timedelta
    return [
        ExtractedEntry(
            timestamp=base + timedelta(seconds=i * 2),
            values={"x": float(i), "y": float(i * 2), "z": float(i * 3)},
            line_number=i + 1,
            raw_text=f"line {i}",
        )
        for i in range(n)
    ]


class TestPlotEngine(unittest.TestCase):

    def setUp(self):
        self.engine = PlotEngine()
        self.entries = _make_entries(5)
        self.result = ExtractionResult(entries=self.entries)

    def tearDown(self):
        plt.close("all")

    # ------------------------------------------------------ secondary y-axis
    def test_y2_keys_creates_twin_axis(self):
        vis = VisualizationConfig(plots=[PlotConfig(title="T", keys=["x"], y2_keys=["y"])])
        fig = self.engine.render(self.result, vis)
        # twinx adds a second Axes sharing the same x-axis
        self.assertEqual(len(fig.axes), 2)

    def test_y2_axis_draws_secondary_line(self):
        vis = VisualizationConfig(plots=[PlotConfig(title="T", keys=["x"], y2_keys=["y"])])
        fig = self.engine.render(self.result, vis)
        ax2 = fig.axes[1]
        self.assertEqual(len(ax2.lines), 1)

    def test_y2_label_applied(self):
        vis = VisualizationConfig(plots=[PlotConfig(title="T", keys=["x"], y2_keys=["y"], y2_label="Right")])
        fig = self.engine.render(self.result, vis)
        ax2 = fig.axes[1]
        self.assertEqual(ax2.get_ylabel(), "Right")

    def test_no_y2_keys_single_axes(self):
        vis = VisualizationConfig(plots=[PlotConfig(title="T", keys=["x"])])
        fig = self.engine.render(self.result, vis)
        self.assertEqual(len(fig.axes), 1)

    # --------------------------------------------------------- basic render
    def test_render_returns_figure(self):
        vis = VisualizationConfig(plots=[PlotConfig(title="X", keys=["x"])])
        fig = self.engine.render(self.result, vis)
        self.assertIsInstance(fig, plt.Figure)

    def test_single_plot_single_key(self):
        vis = VisualizationConfig(layout="single", plots=[PlotConfig(title="X", keys=["x"])])
        fig = self.engine.render(self.result, vis)
        ax = fig.axes[0]
        self.assertEqual(len(ax.lines), 1)

    def test_multi_key_plot_draws_multiple_lines(self):
        vis = VisualizationConfig(plots=[PlotConfig(title="XY", keys=["x", "y"])])
        fig = self.engine.render(self.result, vis)
        ax = fig.axes[0]
        self.assertEqual(len(ax.lines), 2)

    def test_grid_layout_creates_correct_axes(self):
        vis = VisualizationConfig(layout="grid", plots=[
            PlotConfig(title="A", keys=["x"]),
            PlotConfig(title="B", keys=["y"]),
            PlotConfig(title="C", keys=["z"]),
        ])
        fig = self.engine.render(self.result, vis)
        # 3 plots in grid → 2 cols, 2 rows = 4 axes (1 hidden)
        visible = [ax for ax in fig.axes if ax.get_visible()]
        self.assertEqual(len(visible), 3)

    def test_no_plots_raises_value_error(self):
        vis = VisualizationConfig(plots=[])
        with self.assertRaises(ValueError):
            self.engine.render(self.result, vis)

    def test_missing_key_skipped_gracefully(self):
        vis = VisualizationConfig(plots=[PlotConfig(title="T", keys=["nonexistent"])])
        fig = self.engine.render(self.result, vis)
        ax = fig.axes[0]
        self.assertEqual(len(ax.lines), 0)

    def test_y_label_applied(self):
        vis = VisualizationConfig(plots=[PlotConfig(title="T", keys=["x"], y_label="Units")])
        fig = self.engine.render(self.result, vis)
        self.assertEqual(fig.axes[0].get_ylabel(), "Units")

    def test_save_to_file(self):
        vis = VisualizationConfig(plots=[PlotConfig(title="T", keys=["x"])])
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            self.engine.render(self.result, vis, save_path=path)
            self.assertTrue(os.path.getsize(path) > 0)
        finally:
            os.unlink(path)

    # ------------------------------------------ integration with SampleLog
    def test_sample_log_full_pipeline(self):
        with open("Sample/SampleLog.txt", encoding="utf-8") as f:
            raw = f.read()
        profile = ProfileManager().get("AF BFC Scan")
        parse_result = LogParser().parse(raw)
        extraction = RuleEngine().apply(parse_result, profile)

        fig = self.engine.render(extraction, profile.visualization)
        self.assertIsInstance(fig, plt.Figure)
        # twinx axes share the x-axis and have no title — exclude them
        visible_axes = [ax for ax in fig.axes if ax.get_visible() and ax.get_title()]
        self.assertEqual(len(visible_axes), len(profile.visualization.plots))

    def test_sample_log_plot_titles_match_profile(self):
        with open("Sample/SampleLog.txt", encoding="utf-8") as f:
            raw = f.read()
        profile = ProfileManager().get("AF BFC Scan")
        extraction = RuleEngine().apply(LogParser().parse(raw), profile)
        fig = self.engine.render(extraction, profile.visualization)

        expected_titles = {pl.title for pl in profile.visualization.plots}
        actual_titles = {ax.get_title() for ax in fig.axes if ax.get_visible() and ax.get_title()}
        self.assertEqual(expected_titles, actual_titles)

    def test_sample_log_lines_have_data_points(self):
        with open("Sample/SampleLog.txt", encoding="utf-8") as f:
            raw = f.read()
        profile = ProfileManager().get("AF BFC Scan")
        extraction = RuleEngine().apply(LogParser().parse(raw), profile)
        fig = self.engine.render(extraction, profile.visualization)

        for ax in fig.axes:
            if not ax.get_visible():
                continue
            for line in ax.lines:
                self.assertEqual(len(line.get_xdata()), 22)


if __name__ == "__main__":
    unittest.main()
