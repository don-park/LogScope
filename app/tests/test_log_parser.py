import unittest
from datetime import datetime
from app.parser import LogParser
from app.model import ParsedLine, RawLine


class TestLogParser(unittest.TestCase):

    def setUp(self):
        self.parser = LogParser()

    # ------------------------------------------------------------------ helpers
    def _parse_one(self, line: str) -> ParsedLine:
        result = self.parser.parse(line)
        self.assertEqual(len(result.parsed), 1)
        self.assertEqual(len(result.unparseable), 0)
        return result.parsed[0]

    # ------------------------------------------------------------ happy path
    def test_parse_single_standard_line(self):
        line = "01-15 10:23:45.123  1234  5678 D CameraHAL: lens=239"
        entry = self._parse_one(line)
        self.assertEqual(entry.pid, 1234)
        self.assertEqual(entry.tid, 5678)
        self.assertEqual(entry.level, "D")
        self.assertEqual(entry.tag, "CameraHAL")
        self.assertEqual(entry.message, "lens=239")

    def test_parse_line_with_pipes_in_message(self):
        line = "01-15 10:23:45.999  2345  6789 W SomeTag: | DoF 64 | PDresult 8.214 |"
        entry = self._parse_one(line)
        self.assertEqual(entry.tag, "SomeTag")
        self.assertEqual(entry.message, "| DoF 64 | PDresult 8.214 |")

    def test_parse_multiline_input(self):
        raw = (
            "01-15 10:23:45.123  1234  5678 D CameraHAL: lens=239\n"
            "04-18 09:30:15.456   123   456 I AutoFocus: roi(10,20) lens=150\n"
            "01-15 10:23:45.999  2345  6789 W SomeTag: | DoF 64 | PDresult 8.214 |"
        )
        result = self.parser.parse(raw)
        self.assertEqual(len(result.parsed), 3)
        self.assertEqual(len(result.unparseable), 0)

    def test_timestamp_is_datetime_object(self):
        line = "01-15 10:23:45.123  1234  5678 D CameraHAL: lens=239"
        entry = self._parse_one(line)
        self.assertIsInstance(entry.timestamp, datetime)
        self.assertEqual(entry.timestamp.month, 1)
        self.assertEqual(entry.timestamp.day, 15)
        self.assertEqual(entry.timestamp.hour, 10)
        self.assertEqual(entry.timestamp.minute, 23)
        self.assertEqual(entry.timestamp.second, 45)

    def test_pid_tid_are_integers(self):
        line = "01-15 10:23:45.123  1234  5678 D CameraHAL: lens=239"
        entry = self._parse_one(line)
        self.assertIsInstance(entry.pid, int)
        self.assertIsInstance(entry.tid, int)

    def test_all_log_levels_parsed(self):
        template = "01-15 10:23:45.123  1234  5678 {level} Tag: msg"
        for level in ("D", "I", "W", "E", "V", "F"):
            with self.subTest(level=level):
                entry = self._parse_one(template.format(level=level))
                self.assertEqual(entry.level, level)

    def test_raw_text_preserved_on_parsed_line(self):
        line = "01-15 10:23:45.123  1234  5678 D CameraHAL: lens=239"
        entry = self._parse_one(line)
        self.assertEqual(entry.raw_text, line)

    def test_function_style_message(self):
        line = "04-18 09:30:15.456   123   456 I AutoFocus: roi(10,20) lens=150"
        entry = self._parse_one(line)
        self.assertEqual(entry.message, "roi(10,20) lens=150")

    # ------------------------------------------------------------ edge cases
    def test_unparseable_line_stored_as_raw(self):
        result = self.parser.parse("some garbage line")
        self.assertEqual(len(result.parsed), 0)
        self.assertEqual(len(result.unparseable), 1)
        self.assertIsInstance(result.unparseable[0], RawLine)
        self.assertEqual(result.unparseable[0].raw_text, "some garbage line")

    def test_mixed_valid_and_invalid_lines(self):
        raw = (
            "garbage line here\n"
            "01-15 10:23:45.123  1234  5678 D CameraHAL: lens=239\n"
            "another bad line\n"
            "01-15 10:23:46.000  1234  5678 I Tag: msg\n"
        )
        result = self.parser.parse(raw)
        self.assertEqual(len(result.parsed), 2)
        self.assertEqual(len(result.unparseable), 2)

    def test_empty_input_returns_empty_result(self):
        result = self.parser.parse("")
        self.assertEqual(len(result.parsed), 0)
        self.assertEqual(len(result.unparseable), 0)

    def test_blank_lines_ignored(self):
        raw = (
            "\n"
            "01-15 10:23:45.123  1234  5678 D CameraHAL: lens=239\n"
            "\n"
            "\n"
            "01-15 10:23:46.000  1234  5678 I Tag: msg\n"
        )
        result = self.parser.parse(raw)
        self.assertEqual(len(result.parsed), 2)

    def test_line_numbers_reflect_original_position(self):
        raw = (
            "garbage\n"                                               # line 1
            "01-15 10:23:45.123  1234  5678 D CameraHAL: lens=239\n"  # line 2
        )
        result = self.parser.parse(raw)
        self.assertEqual(result.unparseable[0].line_number, 1)
        self.assertEqual(result.parsed[0].line_number, 2)

    def test_windows_crlf_line_endings(self):
        raw = "01-15 10:23:45.123  1234  5678 D CameraHAL: lens=239\r\n01-15 10:23:46.000  5678  1234 I Tag: msg\r\n"
        result = self.parser.parse(raw)
        self.assertEqual(len(result.parsed), 2)

    def test_variable_subsecond_digits(self):
        for ms in ("1", "12", "123", "1234", "12345", "123456"):
            with self.subTest(ms=ms):
                line = f"01-15 10:23:45.{ms}  1234  5678 D Tag: msg"
                entry = self._parse_one(line)
                self.assertIsInstance(entry.timestamp, datetime)


if __name__ == "__main__":
    unittest.main()
