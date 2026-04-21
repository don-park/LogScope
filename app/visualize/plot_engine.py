from __future__ import annotations
import matplotlib.pyplot as plt
from app.model.parsed_data import ExtractionResult
from app.model.profile import VisualizationConfig, PlotConfig


class PlotEngine:

    def render(
        self,
        result: ExtractionResult,
        vis: VisualizationConfig,
        save_path: str | None = None,
    ) -> plt.Figure:
        plots = vis.plots
        n = len(plots)
        if n == 0:
            raise ValueError("No plots defined in visualization config")

        cols = 2 if (vis.layout == "grid" and n > 1) else 1
        rows = (n + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(cols * 7, rows * 3.5), squeeze=False)
        fig.subplots_adjust(hspace=0.45, wspace=0.35)

        frames = list(range(len(result.entries)))

        for idx, plot_cfg in enumerate(plots):
            ax = axes[idx // cols][idx % cols]
            self._draw_plot(ax, frames, result, plot_cfg)

        # hide unused axes when grid has empty slots
        for idx in range(n, rows * cols):
            axes[idx // cols][idx % cols].set_visible(False)

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches="tight")

        return fig

    def _draw_plot(
        self,
        ax: plt.Axes,
        frames: list[int],
        result: ExtractionResult,
        cfg: PlotConfig,
    ) -> None:
        ax.set_title(cfg.title, fontsize=10, pad=6)
        ax.set_xlabel("Frame", fontsize=8)
        if cfg.y_label:
            ax.set_ylabel(cfg.y_label, fontsize=8)
        ax.tick_params(axis="both", labelsize=7)

        for key in cfg.keys:
            y_values = [e.values.get(key) for e in result.entries]
            pairs = [(f, v) for f, v in zip(frames, y_values) if v is not None]
            if not pairs:
                continue
            fs, ys = zip(*pairs)
            ax.plot(fs, ys, marker="o", markersize=3, linewidth=1.2, label=key)

        ax.xaxis.get_major_locator().set_params(integer=True)
        plt.setp(ax.xaxis.get_majorticklabels(), fontsize=7)

        if len(cfg.keys) > 1:
            ax.legend(fontsize=7, loc="best")

        ax.grid(True, linestyle="--", alpha=0.5)
