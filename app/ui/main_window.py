from __future__ import annotations
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QComboBox, QLabel,
    QSplitter, QScrollArea, QSizePolicy, QMessageBox, QShortcut,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

from app.parser import LogParser, ProfileManager, RuleEngine
from app.visualize import PlotEngine


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LogScope")
        self.resize(1280, 960)

        self._parser = LogParser()
        self._profile_manager = ProfileManager()
        self._rule_engine = RuleEngine()
        self._plot_engine = PlotEngine()

        self._canvas: FigureCanvas | None = None
        self._toolbar: NavigationToolbar | None = None
        self._figure: plt.Figure | None = None

        self._build_ui()
        self._populate_profiles()
        self._setup_shortcuts()

    # ----------------------------------------------------------------- UI
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── top bar: profile selector + analyze button ──────────────────
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Profile:"))
        self._profile_combo = QComboBox()
        self._profile_combo.setMinimumWidth(200)
        top_bar.addWidget(self._profile_combo)
        top_bar.addStretch()
        self._analyse_btn = QPushButton("Analyze")
        self._analyse_btn.setFixedWidth(100)
        self._analyse_btn.clicked.connect(self._on_analyse)
        top_bar.addWidget(self._analyse_btn)
        root.addLayout(top_bar)

        # ── main splitter: log input (top) | graph (bottom) ─────────────
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(4)

        # top: log text input
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(QLabel("Log Input:"))
        self._log_input = QTextEdit()
        self._log_input.setPlaceholderText("Paste logcat log here…")
        self._log_input.setLineWrapMode(QTextEdit.NoWrap)
        top_layout.addWidget(self._log_input)
        splitter.addWidget(top_widget)

        # bottom: graph area (scrollable)
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(QLabel("Graph:"))
        self._graph_scroll = QScrollArea()
        self._graph_scroll.setWidgetResizable(True)
        self._graph_container = QWidget()
        self._graph_layout = QVBoxLayout(self._graph_container)
        self._graph_layout.setContentsMargins(0, 0, 0, 0)
        self._graph_scroll.setWidget(self._graph_container)
        bottom_layout.addWidget(self._graph_scroll)
        splitter.addWidget(bottom)

        # log:graph ≈ 28:72 (graph ~10% larger share than even split)
        splitter.setSizes([250, 640])
        root.addWidget(splitter, stretch=1)

        # ── status bar ───────────────────────────────────────────────────
        self._status = QLabel("Ready")
        self.statusBar().addWidget(self._status)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self._on_analyse)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._save_figure)

    def _populate_profiles(self) -> None:
        self._profile_combo.clear()
        for name in self._profile_manager.list_profiles():
            self._profile_combo.addItem(name)

    # ------------------------------------------------------------ actions
    def _on_analyse(self) -> None:
        raw = self._log_input.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, "LogScope", "Please paste log text first.")
            return

        profile_name = self._profile_combo.currentText()
        profile = self._profile_manager.get(profile_name)
        if not profile:
            QMessageBox.warning(self, "LogScope", f"Profile '{profile_name}' not found.")
            return

        parse_result = self._parser.parse(raw)
        extraction = self._rule_engine.apply(parse_result, profile)

        if not extraction.entries:
            QMessageBox.information(
                self, "LogScope",
                f"No matching lines found for profile '{profile_name}'.\n"
                f"Parsed {len(parse_result.parsed)} lines, "
                f"{len(parse_result.unparseable)} unparseable."
            )
            return

        self._render_graph(extraction, profile)
        self._status.setText(
            f"Profile: {profile_name}  |  "
            f"Matched: {len(extraction.entries)} lines  |  "
            f"Failed to extract: {len(extraction.failed_lines)}"
        )

    def _save_figure(self) -> None:
        if self._toolbar is not None:
            self._toolbar.save_figure()

    def _render_graph(self, extraction, profile) -> None:
        # remove previous canvas and toolbar
        if self._canvas:
            self._graph_layout.removeWidget(self._toolbar)
            self._graph_layout.removeWidget(self._canvas)
            self._toolbar.deleteLater()
            self._canvas.deleteLater()
            plt.close(self._figure)

        self._figure = self._plot_engine.render(extraction, profile.visualization)
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._toolbar = NavigationToolbar(self._canvas, self._graph_container)

        self._graph_layout.addWidget(self._toolbar)
        self._graph_layout.addWidget(self._canvas)
        self._canvas.draw()
