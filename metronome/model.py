"""节拍器配置模型：参数校验与安全的 JSON 内嵌。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Tuple

MIN_BPM = 30
MAX_BPM = 240
MIN_BEATS = 1
MAX_BEATS = 12
MIN_MINUTES = 1
MAX_MINUTES = 60
MAX_TITLE_LENGTH = 40


class MetronomeError(ValueError):
    """节拍器参数或输入不合法。"""


def _require_int(name: str, value: object, minimum: int, maximum: int) -> int:
    """校验整数范围，bool 不算整数。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise MetronomeError("%s必须是整数" % name)
    if value < minimum or value > maximum:
        raise MetronomeError(
            "%s必须在 %d~%d 之间，当前是 %d" % (name, minimum, maximum, value)
        )
    return value


def _require_title(value: object) -> str:
    """校验标题：非空、长度受限、不含控制字符。"""
    if not isinstance(value, str):
        raise MetronomeError("标题必须是文本")
    title = value.strip()
    if not title:
        raise MetronomeError("标题不能为空")
    if len(title) > MAX_TITLE_LENGTH:
        raise MetronomeError("标题最多 %d 个字符" % MAX_TITLE_LENGTH)
    for char in title:
        if ord(char) < 32 or ord(char) == 127:
            raise MetronomeError("标题不能包含换行或其他控制字符")
    return title


def _json_for_html(data: Dict[str, object]) -> str:
    """序列化为可安全放进 <script> 的 JSON。"""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # 转义 HTML 敏感字符与 JS 行分隔符，避免 </script> 提前闭合。
    return (
        text.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


@dataclass(frozen=True)
class MetronomeConfig:
    """一次练习的初始配置。"""

    bpm: int = 90
    beats: int = 4
    accent: int = 1
    minutes: int = 5
    title: str = "节拍器"

    def __post_init__(self) -> None:
        bpm = _require_int("BPM", self.bpm, MIN_BPM, MAX_BPM)
        beats = _require_int("每小节拍数", self.beats, MIN_BEATS, MAX_BEATS)
        accent = _require_int("重拍位置", self.accent, 1, beats)
        minutes = _require_int(
            "练习时长（分钟）", self.minutes, MIN_MINUTES, MAX_MINUTES
        )
        title = _require_title(self.title)
        object.__setattr__(self, "bpm", bpm)
        object.__setattr__(self, "beats", beats)
        object.__setattr__(self, "accent", accent)
        object.__setattr__(self, "minutes", minutes)
        object.__setattr__(self, "title", title)

    @property
    def total_seconds(self) -> int:
        """练习总时长（秒）。"""
        return self.minutes * 60

    @property
    def accent_pattern(self) -> Tuple[bool, ...]:
        """每拍是否重拍，索引从第 1 拍开始。"""
        return tuple(index == self.accent - 1 for index in range(self.beats))

    def to_dict(self) -> Dict[str, object]:
        """转为可内嵌到页面的配置字典。"""
        return {
            "bpm": self.bpm,
            "beats": self.beats,
            "accent": self.accent,
            "minutes": self.minutes,
            "title": self.title,
            "total_seconds": self.total_seconds,
        }

    def to_json(self) -> str:
        """转为可安全放进 <script> 的 JSON 文本。"""
        return _json_for_html(self.to_dict())


def format_clock(seconds: int) -> str:
    """把秒数格式化为 mm:ss。"""
    if isinstance(seconds, bool) or not isinstance(seconds, int):
        raise MetronomeError("秒数必须是整数")
    if seconds < 0:
        raise MetronomeError("秒数不能为负数")
    minutes, rest = divmod(seconds, 60)
    return "%02d:%02d" % (minutes, rest)
