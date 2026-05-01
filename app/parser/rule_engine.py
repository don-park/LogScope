from __future__ import annotations
import re
from app.model.log_entry import ParsedLine, ParseResult
from app.model.parsed_data import ExtractedEntry, ExtractionResult
from app.model.profile import AnalysisProfile, DerivedConfig, FilterConfig, PatternConfig


class RuleEngine:

    def apply(self, parse_result: ParseResult, profile: AnalysisProfile) -> ExtractionResult:
        result = ExtractionResult()
        for line in parse_result.parsed:
            if not self._matches_filter(line, profile.filter):
                continue
            values = {}
            for pattern in profile.patterns:
                values.update(self._apply_pattern(line.message, pattern))
            if profile.derived:
                self._apply_derived(values, profile.derived)
            if values:
                result.entries.append(ExtractedEntry(
                    timestamp=line.timestamp,
                    values=values,
                    line_number=line.line_number,
                    raw_text=line.raw_text,
                ))
            else:
                result.failed_lines.append(line.line_number)
        return result

    # --------------------------------------------------------------- derived
    def _apply_derived(self, values: dict, derived: list[DerivedConfig]) -> None:
        for d in derived:
            try:
                val = eval(d.expr, {"__builtins__": {}}, values)  # noqa: S307
                values[d.name] = float(val)
            except Exception:
                pass

    # ---------------------------------------------------------------- filter
    def _matches_filter(self, line: ParsedLine, f: FilterConfig) -> bool:
        if f.tag and line.tag != f.tag:
            return False
        if f.keyword and f.keyword not in line.message:
            return False
        return True

    # ---------------------------------------------------------------- dispatch
    def _apply_pattern(self, message: str, pattern: PatternConfig) -> dict[str, float]:
        if pattern.type == "segment":
            return self._apply_segment(message, pattern.params)
        if pattern.type == "key_value":
            return self._apply_key_value(message, pattern.params)
        if pattern.type == "regex":
            return self._apply_regex(message, pattern.params)
        return {}

    # --------------------------------------------------------------- segment
    def _apply_segment(self, message: str, params: dict) -> dict[str, float]:
        delimiter = params.get("delimiter", "|")
        strip = params.get("strip", True)
        inner_type = params.get("inner_type", "key_value")
        allowed_keys: list[str] | None = params.get("keys")

        segments = message.split(delimiter)
        values: dict[str, float] = {}
        for seg in segments:
            if strip:
                seg = seg.strip()
            if not seg:
                continue
            if inner_type == "key_value":
                extracted = self._apply_key_value(seg, params)
            elif inner_type == "regex":
                extracted = self._apply_regex(seg, params)
            else:
                continue
            if allowed_keys:
                extracted = {k: v for k, v in extracted.items() if k in allowed_keys}
            values.update(extracted)
        return values

    # ------------------------------------------------------------ key_value
    def _apply_key_value(self, text: str, params: dict) -> dict[str, float]:
        separator = params.get("separator", " ")
        # Split on separator, expecting exactly "key<sep>value ..."
        # The value is the first numeric token after the separator.
        values: dict[str, float] = {}
        # Build regex: key followed by separator(s) and a numeric value
        sep_pat = re.escape(separator) + r"+"
        pattern = re.compile(
            r"(\w+)" + sep_pat + r"([+-]?\d+(?:\.\d+)?)"
        )
        for m in pattern.finditer(text):
            key, raw_val = m.group(1), m.group(2)
            try:
                values[key] = float(raw_val)
            except ValueError:
                pass
        return values

    # --------------------------------------------------------------- regex
    def _apply_regex(self, message: str, params: dict) -> dict[str, float]:
        pattern_str = params.get("pattern", "")
        if not pattern_str:
            return {}
        try:
            m = re.search(pattern_str, message)
        except re.error:
            return {}
        if not m:
            return {}
        values: dict[str, float] = {}
        for key, raw_val in m.groupdict().items():
            if raw_val is None:
                continue
            try:
                values[key] = float(raw_val)
            except ValueError:
                pass
        return values
