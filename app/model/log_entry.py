from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawLine:
    line_number: int
    raw_text: str


@dataclass
class ParsedLine:
    line_number: int
    raw_text: str
    timestamp: datetime
    pid: int
    tid: int
    level: str  # D/I/W/E/V/F
    tag: str
    message: str


@dataclass
class ParseResult:
    parsed: list[ParsedLine] = field(default_factory=list)
    unparseable: list[RawLine] = field(default_factory=list)
