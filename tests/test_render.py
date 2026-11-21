"""render 模块单元测试。"""

from __future__ import annotations

import json
import unittest

from metronome.model import MetronomeConfig, MetronomeError
from metronome.render import render_html

CONFIG_MARK = '<script id="metronome-config" type="application/json">'


def extract_config(page: str) -> dict:
    """从页面中取出内嵌配置。"""
    start = page.index(CONFIG_MARK) + len(CONFIG_MARK)
    end = page.index("</script>", start)
    return json.loads(page[start:end])


class RenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = MetronomeConfig(
            bpm=90, beats=4, accent=1, minutes=5, title="课堂节拍器"
        )
        self.page = render_html(self.config)

    def test_document(self) -> None:
        self.assertTrue(self.page.startswith("<!doctype html>"))
        self.assertIn('<html lang="zh-CN">', self.page)
        self.assertTrue(self.page.rstrip().endswith("</html>"))

    def test_self_contained(self) -> None:
        self.assertNotIn("http://", self.page)
        self.assertNotIn("https://", self.page)
        self.assertNotIn("<link", self.page)
        self.assertNotIn("src=", self.page)
        self.assertNotIn("url(", self.page)

    def test_title(self) -> None:
        self.assertIn("<title>课堂节拍器</title>", self.page)
        self.assertIn("<h1>课堂节拍器</h1>", self.page)

    def test_bpm_display(self) -> None:
        self.assertIn('<span id="bpmValue">90</span>', self.page)
        self.assertIn("BPM", self.page)

    def test_beat_label(self) -> None:
        self.assertIn('<span class="value" id="beatLabel">1/4</span>', self.page)

    def test_remaining_time(self) -> None:
        self.assertIn('<span class="value" id="timeLeft">05:00</span>', self.page)

    def test_embedded_config(self) -> None:
        data = extract_config(self.page)
        self.assertEqual(data["bpm"], 90)
        self.assertEqual(data["beats"], 4)
        self.assertEqual(data["accent"], 1)
        self.assertEqual(data["minutes"], 5)
        self.assertEqual(data["title"], "课堂节拍器")
        self.assertEqual(data["total_seconds"], 300)

    def test_dots_count(self) -> None:
        self.assertEqual(self.page.count('class="dot'), 4)

    def test_accent_dot(self) -> None:
        self.assertEqual(self.page.count('class="dot accent"'), 1)
        self.assertIn('class="dot accent" data-beat="1"', self.page)

    def test_twelve_beats(self) -> None:
        page = render_html(MetronomeConfig(beats=12, accent=12))
        self.assertEqual(page.count('class="dot'), 12)
        self.assertIn('class="dot accent" data-beat="12"', page)
        self.assertIn("1/12", page)

    def test_web_audio(self) -> None:
        self.assertIn("AudioContext", self.page)
        self.assertIn("webkitAudioContext", self.page)
        self.assertIn("createOscillator", self.page)
        self.assertIn("createGain", self.page)
        self.assertIn("exponentialRampToValueAtTime", self.page)

    def test_keyboard(self) -> None:
        self.assertIn('document.addEventListener("keydown"', self.page)
        self.assertIn('event.code === "Space"', self.page)
        self.assertIn("preventDefault", self.page)

    def test_buttons(self) -> None:
        for button_id in ("startBtn", "resetBtn", "minusBtn", "plusBtn", "tapBtn"):
            self.assertIn('id="%s"' % button_id, self.page)
        self.assertIn("开始", self.page)
        self.assertIn("重置", self.page)

    def test_bpm_step(self) -> None:
        self.assertIn("BPM_STEP = 5", self.page)
        self.assertIn(">+5</button>", self.page)
        self.assertIn(">-5</button>", self.page)

    def test_tap_tempo(self) -> None:
        self.assertIn("tapTempo", self.page)
        self.assertIn("拍速", self.page)

    def test_finish_message(self) -> None:
        self.assertIn("时间到", self.page)

    def test_dark_theme(self) -> None:
        self.assertIn("color-scheme: dark", self.page)
        self.assertIn("--bg: #060a12", self.page)

    def test_responsive(self) -> None:
        self.assertIn("overflow-x: hidden", self.page)
        self.assertIn("flex-wrap: wrap", self.page)
        self.assertIn("minmax(44px, 1fr)", self.page)

    def test_accent_colors(self) -> None:
        self.assertIn("--beat: #38bdf8", self.page)
        self.assertIn("--accent: #f97316", self.page)
        self.assertIn(".dot.accent.active", self.page)

    def test_title_escaped(self) -> None:
        page = render_html(MetronomeConfig(title="<节拍器>"))
        self.assertIn("&lt;节拍器&gt;", page)
        self.assertNotIn("<h1><节拍器></h1>", page)

    def test_script_injection_blocked(self) -> None:
        page = render_html(
            MetronomeConfig(title="</script><script>alert(1)</script>")
        )
        self.assertEqual(page.count("</script>"), 2)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertEqual(
            extract_config(page)["title"],
            "</script><script>alert(1)</script>",
        )

    def test_invalid_config(self) -> None:
        with self.assertRaises(MetronomeError):
            render_html("config")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
