"""命令行入口单元测试。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from metronome.cli import main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.target = self.root / "节拍器.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> Tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def run_parse_error(self, argv: List[str]) -> Tuple[int, str]:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main(argv)
        return int(ctx.exception.code or 0), err.getvalue()

    def test_defaults(self) -> None:
        code, out, err = self.run_cli(["-o", str(self.target)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("已生成", out)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn('"bpm":90', page)
        self.assertIn('"beats":4', page)
        self.assertIn('"accent":1', page)
        self.assertIn('"minutes":5', page)
        self.assertIn('<span id="bpmValue">90</span>', page)
        self.assertIn("05:00", page)

    def test_custom_config(self) -> None:
        code, out, _ = self.run_cli(
            [
                "--bpm", "120",
                "--beats", "3",
                "--accent", "2",
                "--minutes", "10",
                "--title", "视唱课",
                "-o", str(self.target),
            ]
        )
        self.assertEqual(code, 0)
        self.assertIn("120 BPM", out)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("<h1>视唱课</h1>", page)
        self.assertIn('"bpm":120', page)
        self.assertIn("1/3", page)
        self.assertIn("10:00", page)

    def test_output_file_content(self) -> None:
        self.run_cli(["-o", str(self.target)])
        page = self.target.read_text(encoding="utf-8")
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("AudioContext", page)
        self.assertIn('addEventListener("keydown"', page)
        self.assertIn("时间到", page)

    def test_accent_equals_beats(self) -> None:
        code, _, _ = self.run_cli(
            ["--beats", "3", "--accent", "3", "-o", str(self.target)]
        )
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn('class="dot accent" data-beat="3"', page)

    def test_min_bounds(self) -> None:
        code, _, _ = self.run_cli(
            [
                "--bpm", "30",
                "--beats", "1",
                "--accent", "1",
                "--minutes", "1",
                "-o", str(self.target),
            ]
        )
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("01:00", page)

    def test_max_bounds(self) -> None:
        code, _, _ = self.run_cli(
            [
                "--bpm", "240",
                "--beats", "12",
                "--accent", "12",
                "--minutes", "60",
                "-o", str(self.target),
            ]
        )
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("60:00", page)
        self.assertEqual(page.count('class="dot'), 12)

    def test_invalid_bpm_low(self) -> None:
        code, _, err = self.run_cli(["--bpm", "29", "-o", str(self.target)])
        self.assertEqual(code, 2)
        self.assertIn("BPM", err)
        self.assertFalse(self.target.exists())

    def test_invalid_bpm_high(self) -> None:
        code, _, err = self.run_cli(["--bpm", "241", "-o", str(self.target)])
        self.assertEqual(code, 2)
        self.assertIn("240", err)
        self.assertFalse(self.target.exists())

    def test_invalid_beats(self) -> None:
        for value in ("0", "13"):
            code, _, err = self.run_cli(
                ["--beats", value, "-o", str(self.target)]
            )
            self.assertEqual(code, 2, value)
            self.assertIn("每小节拍数", err)

    def test_invalid_accent(self) -> None:
        for value in ("0", "5"):
            code, _, err = self.run_cli(
                ["--beats", "4", "--accent", value, "-o", str(self.target)]
            )
            self.assertEqual(code, 2, value)
            self.assertIn("重拍位置", err)

    def test_invalid_minutes(self) -> None:
        for value in ("0", "61"):
            code, _, err = self.run_cli(
                ["--minutes", value, "-o", str(self.target)]
            )
            self.assertEqual(code, 2, value)
            self.assertIn("练习时长", err)

    def test_blank_title(self) -> None:
        code, _, err = self.run_cli(["--title", "  ", "-o", str(self.target)])
        self.assertEqual(code, 2)
        self.assertIn("标题", err)
        self.assertFalse(self.target.exists())

    def test_long_title(self) -> None:
        code, _, err = self.run_cli(
            ["--title", "节" * 41, "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("40", err)

    def test_title_escaped_in_output(self) -> None:
        code, _, _ = self.run_cli(
            ["--title", "</script><script>alert(1)</script>", "-o", str(self.target)]
        )
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertEqual(page.count("</script>"), 2)
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_non_integer_argument(self) -> None:
        code, err = self.run_parse_error(["--bpm", "abc", "-o", str(self.target)])
        self.assertEqual(code, 2)
        self.assertIn("必须是整数", err)

    def test_missing_argument_value(self) -> None:
        code, err = self.run_parse_error(["--bpm"])
        self.assertEqual(code, 2)
        self.assertIn("缺少值", err)

    def test_unknown_argument(self) -> None:
        code, err = self.run_parse_error(["--unknown", "-o", str(self.target)])
        self.assertEqual(code, 2)
        self.assertIn("无法识别", err)

    def test_help(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("usage", out.getvalue())
        self.assertIn("--bpm", out.getvalue())

    def test_version(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("0.1.0", out.getvalue())

    def test_output_is_directory(self) -> None:
        code, _, err = self.run_cli(["-o", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", err)

    def test_missing_output_parent(self) -> None:
        target = self.root / "missing" / "out.html"
        code, _, err = self.run_cli(["-o", str(target)])
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", err)

    def test_default_title(self) -> None:
        code, _, _ = self.run_cli(["-o", str(self.target)])
        self.assertEqual(code, 0)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("<h1>节拍器</h1>", page)


if __name__ == "__main__":
    unittest.main()
