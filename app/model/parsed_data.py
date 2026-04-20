from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExtractedEntry:
    timestamp: datetime
    values: dict[str, float]    # key → numeric value
    line_number: int
    raw_text: str


@dataclass
class ExtractionResult:
    entries: list[ExtractedEntry] = field(default_factory=list)
    failed_lines: list[int] = field(default_factory=list)  # line_numbers that matched filter but failed to extract
