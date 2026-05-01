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
        ax.grid(True, linestyle="--", alpha=0.5)

        for key in cfg.keys:
            y_values = [e.values.get(key) for e in result.entries]
            pairs = [(f, v) for f, v in zip(frames, y_values) if v is not None]
            if not pairs:
                continue
            fs, ys = zip(*pairs)
            ax.plot(fs, ys, marker="o", markersize=3, linewidth=1.2, label=key)

        ax.xaxis.get_major_locator().set_params(integer=True)
        plt.setp(ax.xaxis.get_majorticklabels(), fontsize=7)

        if cfg.center_zero and ax.lines:
            ymin, ymax = ax.get_ylim()
            limit = max(abs(ymin), abs(ymax))
            if limit > 0:
                ax.set_ylim(-limit, limit)

        all_handles, all_labels = ax.get_legend_handles_labels()

        if cfg.y2_keys:
            ax2 = ax.twinx()
            if cfg.y2_label:
                ax2.set_ylabel(cfg.y2_label, fontsize=8)
            ax2.tick_params(axis="y", labelsize=7)
            for key in cfg.y2_keys:
                y_values = [e.values.get(key) for e in result.entries]
                pairs = [(f, v) for f, v in zip(frames, y_values) if v is not None]
                if not pairs:
                    continue
                fs, ys = zip(*pairs)
                ax2.plot(fs, ys, marker="s", markersize=3, linewidth=1.2, linestyle="--", label=key)
            h2, l2 = ax2.get_legend_handles_labels()
            all_handles += h2
            all_labels += l2

        if len(all_handles) > 1:
            ax.legend(all_handles, all_labels, fontsize=7, loc="best")
