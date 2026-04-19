from __future__ import annotations
import re
from datetime import datetime
from app.model.log_entry import ParsedLine, RawLine, ParseResult


class LogParser:
    # Standard logcat format: MM-DD HH:MM:SS.mmm  PID  TID LEVEL TAG: message
    _LOGCAT_PATTERN = re.compile(
        r"^(\d{2}-\d{2})"               # group 1: MM-DD
        r"\s+(\d{2}:\d{2}:\d{2}\.\d+)"  # group 2: HH:MM:SS.mmm (variable sub-second digits)
        r"\s+(\d+)"                      # group 3: PID (right-aligned, variable leading spaces)
        r"\s+(\d+)"                      # group 4: TID
        r"\s+([DIWEVF])"                 # group 5: level
        r"\s+([^:]+?)"                   # group 6: tag (non-greedy, stops at first colon)
        r":\s(.*)"                       # group 7: message (everything after "TAG: ")
    )

    def parse(self, raw_text: str) -> ParseResult:
        result = ParseResult()
        for line_number, line in self._split_lines(raw_text):
            entry = self._parse_line(line_number, line)
            if isinstance(entry, ParsedLine):
                result.parsed.append(entry)
            else:
                result.unparseable.append(entry)
        return result

    def _split_lines(self, raw_text: str) -> list[tuple[int, str]]:
        # Use splitlines() to handle \r\n on Windows correctly
        # Keep original 1-based line numbers so UI can reference source positions
        lines = []
        for i, line in enumerate(raw_text.splitlines(), start=1):
            stripped = line.strip()
            if stripped:
                lines.append((i, stripped))
        return lines

    def _parse_line(self, line_number: int, line: str) -> ParsedLine | RawLine:
        m = self._LOGCAT_PATTERN.match(line)
        if not m:
            return RawLine(line_number=line_number, raw_text=line)
        try:
            timestamp = self._build_timestamp(m.group(1), m.group(2))
        except ValueError:
            return RawLine(line_number=line_number, raw_text=line)
        return ParsedLine(
            line_number=line_number,
            raw_text=line,
            timestamp=timestamp,
            pid=int(m.group(3)),
            tid=int(m.group(4)),
            level=m.group(5),
            tag=m.group(6).strip(),
            message=m.group(7),
        )

    def _build_timestamp(self, date_str: str, time_str: str) -> datetime:
        # Logcat omits the year; default to current year.
        # Logs spanning a year boundary will have incorrect year — acceptable for Phase 1.
        year = datetime.now().year
        return datetime.strptime(f"{year}-{date_str} {time_str}", "%Y-%m-%d %H:%M:%S.%f")
