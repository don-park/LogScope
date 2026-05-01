from __future__ import annotations
import os
import sys
import yaml
from app.model.profile import (
    AnalysisProfile, FilterConfig, PatternConfig, PlotConfig, VisualizationConfig,
    DerivedConfig,
)


def _default_profiles_dir() -> str:
    # PyInstaller --onefile extracts files to sys._MEIPASS at runtime
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    return os.path.join(base, "app", "parser", "profiles") if hasattr(sys, "_MEIPASS") \
        else os.path.join(os.path.dirname(__file__), "profiles")


class ProfileManager:
    def __init__(self, profiles_dir: str | None = None):
        if profiles_dir is None:
            profiles_dir = _default_profiles_dir()
        self._dir = profiles_dir
        self._profiles: dict[str, AnalysisProfile] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not os.path.isdir(self._dir):
            return
        for fname in os.listdir(self._dir):
            if fname.endswith(".yaml") or fname.endswith(".yml"):
                path = os.path.join(self._dir, fname)
                try:
                    profile = self._load_file(path)
                    self._profiles[profile.name] = profile
                except (KeyError, ValueError, yaml.YAMLError):
                    pass  # skip malformed profiles silently

    def _load_file(self, path: str) -> AnalysisProfile:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return self._from_dict(data)

    def _from_dict(self, data: dict) -> AnalysisProfile:
        fdata = data.get("filter", {})
        filter_cfg = FilterConfig(
            tag=fdata.get("tag"),
            keyword=fdata.get("keyword"),
        )

        patterns = [
            PatternConfig(type=p["type"], params=p.get("params", {}))
            for p in data.get("patterns", [])
        ]

        vdata = data.get("visualization", {})
        plots = [
            PlotConfig(
                title=pl["title"],
                keys=pl["keys"],
                y_label=pl.get("y_label"),
                y2_keys=pl.get("y2_keys", []),
                y2_label=pl.get("y2_label"),
                center_zero=pl.get("center_zero", False),
            )
            for pl in vdata.get("plots", [])
        ]
        vis = VisualizationConfig(
            layout=vdata.get("layout", "grid"),
            plots=plots,
        )

        derived = [
            DerivedConfig(name=d["name"], expr=d["expr"])
            for d in data.get("derived", [])
        ]

        return AnalysisProfile(
            name=data["name"],
            filter=filter_cfg,
            patterns=patterns,
            visualization=vis,
            derived=derived,
        )

    def list_profiles(self) -> list[str]:
        return sorted(self._profiles.keys())

    def get(self, name: str) -> AnalysisProfile | None:
        return self._profiles.get(name)

    def load_file(self, path: str) -> AnalysisProfile:
        profile = self._load_file(path)
        self._profiles[profile.name] = profile
        return profile
