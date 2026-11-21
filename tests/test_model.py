"""model 模块单元测试。"""

from __future__ import annotations

import json
import unittest

from metronome.model import (
    MAX_BEATS,
    MAX_BPM,
    MAX_MINUTES,
    MAX_TITLE_LENGTH,
    MIN_BEATS,
    MIN_BPM,
    MIN_MINUTES,
    MetronomeConfig,
    MetronomeError,
    format_clock,
)


class DefaultsTest(unittest.TestCase):
    def test_defaults(self) -> None:
        config = MetronomeConfig()
        self.assertEqual(config.bpm, 90)
        self.assertEqual(config.beats, 4)
        self.assertEqual(config.accent, 1)
        self.assertEqual(config.minutes, 5)
        self.assertEqual(config.title, "节拍器")

    def test_total_seconds(self) -> None:
        self.assertEqual(MetronomeConfig(minutes=1).total_seconds, 60)
        self.assertEqual(MetronomeConfig(minutes=60).total_seconds, 3600)

    def test_accent_pattern(self) -> None:
        config = MetronomeConfig(beats=4, accent=2)
        self.assertEqual(config.accent_pattern, (False, True, False, False))

    def test_error_is_value_error(self) -> None:
        self.assertTrue(issubclass(MetronomeError, ValueError))


class BpmTest(unittest.TestCase):
    def test_minimum(self) -> None:
        self.assertEqual(MetronomeConfig(bpm=MIN_BPM).bpm, MIN_BPM)

    def test_maximum(self) -> None:
        self.assertEqual(MetronomeConfig(bpm=MAX_BPM).bpm, MAX_BPM)

    def test_below_minimum(self) -> None:
        with self.assertRaises(MetronomeError) as ctx:
            MetronomeConfig(bpm=MIN_BPM - 1)
        self.assertIn("BPM", str(ctx.exception))

    def test_above_maximum(self) -> None:
        with self.assertRaises(MetronomeError):
            MetronomeConfig(bpm=MAX_BPM + 1)

    def test_non_integer(self) -> None:
        for value in (90.0, "90", None, True):
            with self.assertRaises(MetronomeError, msg=repr(value)):
                MetronomeConfig(bpm=value)  # type: ignore[arg-type]


class BeatsTest(unittest.TestCase):
    def test_minimum(self) -> None:
        self.assertEqual(MetronomeConfig(beats=MIN_BEATS).beats, MIN_BEATS)

    def test_maximum(self) -> None:
        self.assertEqual(MetronomeConfig(beats=MAX_BEATS).beats, MAX_BEATS)

    def test_below_minimum(self) -> None:
        with self.assertRaises(MetronomeError):
            MetronomeConfig(beats=MIN_BEATS - 1)

    def test_above_maximum(self) -> None:
        with self.assertRaises(MetronomeError):
            MetronomeConfig(beats=MAX_BEATS + 1)

    def test_non_integer(self) -> None:
        for value in (4.0, "4", None, True):
            with self.assertRaises(MetronomeError, msg=repr(value)):
                MetronomeConfig(beats=value)  # type: ignore[arg-type]


class AccentTest(unittest.TestCase):
    def test_first_beat(self) -> None:
        self.assertEqual(MetronomeConfig(beats=4, accent=1).accent, 1)

    def test_last_beat_allowed(self) -> None:
        self.assertEqual(MetronomeConfig(beats=4, accent=4).accent, 4)

    def test_zero(self) -> None:
        with self.assertRaises(MetronomeError):
            MetronomeConfig(beats=4, accent=0)

    def test_greater_than_beats(self) -> None:
        with self.assertRaises(MetronomeError) as ctx:
            MetronomeConfig(beats=4, accent=5)
        self.assertIn("重拍位置", str(ctx.exception))

    def test_one_beat_allows_accent_one(self) -> None:
        self.assertEqual(MetronomeConfig(beats=1, accent=1).accent, 1)

    def test_non_integer(self) -> None:
        for value in (1.0, "1", None, True):
            with self.assertRaises(MetronomeError, msg=repr(value)):
                MetronomeConfig(accent=value)  # type: ignore[arg-type]


class MinutesTest(unittest.TestCase):
    def test_minimum(self) -> None:
        self.assertEqual(MetronomeConfig(minutes=MIN_MINUTES).minutes, MIN_MINUTES)

    def test_maximum(self) -> None:
        self.assertEqual(MetronomeConfig(minutes=MAX_MINUTES).minutes, MAX_MINUTES)

    def test_below_minimum(self) -> None:
        with self.assertRaises(MetronomeError):
            MetronomeConfig(minutes=MIN_MINUTES - 1)

    def test_above_maximum(self) -> None:
        with self.assertRaises(MetronomeError):
            MetronomeConfig(minutes=MAX_MINUTES + 1)

    def test_non_integer(self) -> None:
        for value in (5.0, "5", None, True):
            with self.assertRaises(MetronomeError, msg=repr(value)):
                MetronomeConfig(minutes=value)  # type: ignore[arg-type]


class TitleTest(unittest.TestCase):
    def test_stripped(self) -> None:
        self.assertEqual(MetronomeConfig(title="  练琴  ").title, "练琴")

    def test_empty(self) -> None:
        for value in ("", "   ", "\t"):
            with self.assertRaises(MetronomeError, msg=repr(value)):
                MetronomeConfig(title=value)

    def test_too_long(self) -> None:
        with self.assertRaises(MetronomeError):
            MetronomeConfig(title="节" * (MAX_TITLE_LENGTH + 1))

    def test_max_length_allowed(self) -> None:
        title = "节" * MAX_TITLE_LENGTH
        self.assertEqual(MetronomeConfig(title=title).title, title)

    def test_non_text(self) -> None:
        for value in (None, 123, True):
            with self.assertRaises(MetronomeError, msg=repr(value)):
                MetronomeConfig(title=value)  # type: ignore[arg-type]

    def test_control_character(self) -> None:
        with self.assertRaises(MetronomeError):
            MetronomeConfig(title="课堂\n节拍器")

    def test_special_characters_allowed(self) -> None:
        self.assertEqual(MetronomeConfig(title="<节拍>").title, "<节拍>")


class SerializationTest(unittest.TestCase):
    def test_to_dict(self) -> None:
        data = MetronomeConfig(
            bpm=120, beats=3, accent=1, minutes=2, title="视唱"
        ).to_dict()
        self.assertEqual(data["bpm"], 120)
        self.assertEqual(data["beats"], 3)
        self.assertEqual(data["accent"], 1)
        self.assertEqual(data["minutes"], 2)
        self.assertEqual(data["title"], "视唱")
        self.assertEqual(data["total_seconds"], 120)

    def test_to_json_roundtrip(self) -> None:
        config = MetronomeConfig(title="课堂节拍器")
        self.assertEqual(json.loads(config.to_json()), config.to_dict())

    def test_script_injection_escaped(self) -> None:
        config = MetronomeConfig(title="</script><script>alert(1)</script>")
        text = config.to_json()
        self.assertNotIn("</script>", text)
        self.assertNotIn("<", text)
        self.assertEqual(json.loads(text)["title"], config.title)

    def test_chinese_kept_readable(self) -> None:
        text = MetronomeConfig(title="练琴").to_json()
        self.assertIn("练琴", text)


class FormatClockTest(unittest.TestCase):
    def test_zero(self) -> None:
        self.assertEqual(format_clock(0), "00:00")

    def test_minutes(self) -> None:
        self.assertEqual(format_clock(300), "05:00")

    def test_mixed(self) -> None:
        self.assertEqual(format_clock(65), "01:05")

    def test_hour(self) -> None:
        self.assertEqual(format_clock(3600), "60:00")

    def test_invalid(self) -> None:
        for value in (-1, 1.0, "60", None, True):
            with self.assertRaises(MetronomeError, msg=repr(value)):
                format_clock(value)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
