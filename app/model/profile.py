from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class FilterConfig:
    tag: str | None = None      # match log lines by tag (e.g. "AF_DEBUG")
    keyword: str | None = None  # match log lines by keyword in message


@dataclass
class PatternConfig:
    type: str                        # "segment", "key_value", "function", "regex"
    params: dict = field(default_factory=dict)


@dataclass
class DerivedConfig:
    name: str   # output key name (e.g. "dofDiff")
    expr: str   # arithmetic expression using extracted keys (e.g. "pdResult - aiResult")


@dataclass
class PlotConfig:
    title: str
    keys: list[str]
    y_label: str | None = None
    y2_keys: list[str] = field(default_factory=list)
    y2_label: str | None = None
    center_zero: bool = False


@dataclass
class VisualizationConfig:
    layout: str = "grid"            # "single" | "grid"
    plots: list[PlotConfig] = field(default_factory=list)


@dataclass
class AnalysisProfile:
    name: str
    filter: FilterConfig
    patterns: list[PatternConfig]
    visualization: VisualizationConfig
    derived: list[DerivedConfig] = field(default_factory=list)
