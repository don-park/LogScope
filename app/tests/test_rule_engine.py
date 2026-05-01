import unittest
from app.parser import LogParser, ProfileManager, RuleEngine
from app.model import ExtractionResult, ExtractedEntry

# SampleLog의 AF_DEBUG BFC 라인 두 개 (음수 포함)
SAMPLE_LINES = """\
04-17 10:02:10.822  2107  4298  E  AF_DEBUG:    CheckDebugMode(4499) : [cam_id_0] BFC scaning 1 | Dof 64 | step 64 | point 10 | CurrLens 1726,  178 mm | currDof  -0.0000 | pdResult   0.0938 | aiResult  -1.3683, 1 | pdAvg   0.0891 | aiAvg  -1.5747
04-17 10:02:12.725  2107  4302  E  AF_DEBUG:    CheckDebugMode(4499) : [cam_id_0] BFC scaning 1 | Dof 64 | step 64 | point 10 | CurrLens 1086, 4930 mm | currDof -10.0000 | pdResult -10.0312 | aiResult -12.3674, 1 | pdAvg -10.0547 | aiAvg -12.3096
"""

# 필터에 걸리지 않아야 할 라인들
OTHER_LINES = """\
04-17 10:02:04.288  2167  4427  I  CHI:         [SS_INFO] [CHI ]: chxextensionmodule.cpp: SetSessionParams: 29194: test
04-17 10:02:04.743  2107  4396  E  AIAF:        setSessionInfo: AIAF Version : 0x0A30
04-17 10:02:04.770  2107  3158  I  AF_DEBUG:    AFStepmoveTo(2680) [cam_id_1][AF_INFO] Final Lens position 4088
"""


class TestRuleEngine(unittest.TestCase):

    def setUp(self):
        self.parser = LogParser()
        self.profile = ProfileManager().get("AF BFC Scan")
        self.engine = RuleEngine()

    def _run(self, raw: str) -> ExtractionResult:
        return self.engine.apply(self.parser.parse(raw), self.profile)

    # --------------------------------------------------------- filter
    def test_non_matching_lines_excluded(self):
        result = self._run(OTHER_LINES)
        self.assertEqual(len(result.entries), 0)

    def test_only_bfc_lines_extracted(self):
        result = self._run(SAMPLE_LINES + OTHER_LINES)
        self.assertEqual(len(result.entries), 2)

    def test_wrong_tag_excluded(self):
        line = "04-17 10:02:10.822  2107  4298  E  AIAF:    BFC scaning 1 | Dof 64 | CurrLens 1726, 178 mm | pdResult 0.09\n"
        result = self._run(line)
        self.assertEqual(len(result.entries), 0)

    def test_missing_keyword_excluded(self):
        line = "04-17 10:02:10.822  2107  4298  E  AF_DEBUG:    CheckDebugMode | Dof 64 | CurrLens 1726, 178 mm | pdResult 0.09\n"
        result = self._run(line)
        self.assertEqual(len(result.entries), 0)

    # ------------------------------------------------ segment extraction
    def test_segment_extracts_dof(self):
        result = self._run(SAMPLE_LINES)
        self.assertIn("Dof", result.entries[0].values)
        self.assertEqual(result.entries[0].values["Dof"], 64.0)

    def test_segment_extracts_pdresult(self):
        result = self._run(SAMPLE_LINES)
        self.assertAlmostEqual(result.entries[0].values["pdResult"], 0.0938, places=4)

    def test_segment_extracts_negative_values(self):
        result = self._run(SAMPLE_LINES)
        self.assertAlmostEqual(result.entries[1].values["pdResult"], -10.0312, places=4)
        self.assertAlmostEqual(result.entries[1].values["aiResult"], -12.3674, places=4)

    def test_segment_extracts_all_expected_keys(self):
        result = self._run(SAMPLE_LINES)
        expected = {"Dof", "currDof", "step", "point", "pdResult", "aiResult", "pdAvg", "aiAvg"}
        self.assertTrue(expected.issubset(result.entries[0].values.keys()))

    # ------------------------------------------------- regex extraction
    def test_regex_extracts_currlens_code(self):
        result = self._run(SAMPLE_LINES)
        self.assertIn("CurrLens_code", result.entries[0].values)
        self.assertEqual(result.entries[0].values["CurrLens_code"], 1726.0)

    def test_regex_extracts_currlens_mm(self):
        result = self._run(SAMPLE_LINES)
        self.assertIn("CurrLens_mm", result.entries[0].values)
        self.assertEqual(result.entries[0].values["CurrLens_mm"], 178.0)

    def test_regex_second_line_currlens(self):
        result = self._run(SAMPLE_LINES)
        self.assertEqual(result.entries[1].values["CurrLens_code"], 1086.0)
        self.assertEqual(result.entries[1].values["CurrLens_mm"], 4930.0)

    # -------------------------------------------------- entry metadata
    def test_entry_has_correct_timestamp(self):
        result = self._run(SAMPLE_LINES)
        ts = result.entries[0].timestamp
        self.assertEqual(ts.month, 4)
        self.assertEqual(ts.day, 17)
        self.assertEqual(ts.hour, 10)
        self.assertEqual(ts.minute, 2)
        self.assertEqual(ts.second, 10)

    def test_entry_preserves_line_number(self):
        result = self._run(SAMPLE_LINES)
        self.assertEqual(result.entries[0].line_number, 1)
        self.assertEqual(result.entries[1].line_number, 2)

    def test_entry_values_are_floats(self):
        result = self._run(SAMPLE_LINES)
        for v in result.entries[0].values.values():
            self.assertIsInstance(v, float)

    # ------------------------------------------------- derived fields
    def test_derived_dofDiff_computed(self):
        result = self._run(SAMPLE_LINES)
        entry = result.entries[0]
        expected = entry.values["pdResult"] - entry.values["aiResult"]
        self.assertAlmostEqual(entry.values["dofDiff"], expected, places=6)

    def test_derived_dofDiff_is_float(self):
        result = self._run(SAMPLE_LINES)
        self.assertIsInstance(result.entries[0].values["dofDiff"], float)

    def test_derived_dofDiff_negative_values(self):
        result = self._run(SAMPLE_LINES)
        entry = result.entries[1]
        expected = entry.values["pdResult"] - entry.values["aiResult"]
        self.assertAlmostEqual(entry.values["dofDiff"], expected, places=6)

    # ---------------------------------------------- full sample log
    def test_full_sample_log_extracts_22_entries(self):
        with open("Sample/SampleLog.txt", encoding="utf-8") as f:
            raw = f.read()
        result = self._run(raw)
        # SampleLog에는 BFC scaning 라인이 22개 (line 16~37)
        self.assertEqual(len(result.entries), 22)

    def test_full_sample_log_no_failed_lines(self):
        with open("Sample/SampleLog.txt", encoding="utf-8") as f:
            raw = f.read()
        result = self._run(raw)
        self.assertEqual(len(result.failed_lines), 0)


if __name__ == "__main__":
    unittest.main()
