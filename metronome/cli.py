"""命令行入口：生成单文件网页节拍器。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional, Sequence

from .model import (
    MAX_BPM,
    MAX_BEATS,
    MAX_MINUTES,
    MIN_BPM,
    MIN_BEATS,
    MIN_MINUTES,
    MetronomeConfig,
    MetronomeError,
)
from .render import render_html


class _ChineseParser(argparse.ArgumentParser):
    """把 argparse 的常见英文报错换成中文。"""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print("错误: %s" % _translate(message), file=sys.stderr)
        raise SystemExit(2)


def _translate(message: str) -> str:
    """翻译 argparse 常见错误信息。"""
    invalid_int = re.search(
        r"argument ([^:]+): invalid int value: (.+)", message
    )
    if invalid_int:
        return "参数 %s 必须是整数（收到：%s）" % (
            invalid_int.group(1).strip(),
            invalid_int.group(2).strip(),
        )
    missing_value = re.search(r"argument ([^:]+): expected one argument", message)
    if missing_value:
        return "参数 %s 缺少值" % missing_value.group(1).strip()
    if message.startswith("unrecognized arguments:"):
        return "无法识别的参数：%s" % message.split(":", 1)[1].strip()
    if message.startswith("the following arguments are required:"):
        return "缺少必需参数：%s" % message.split(":", 1)[1].strip()
    return "参数不合法（%s）" % message


def build_parser() -> argparse.ArgumentParser:
    parser = _ChineseParser(
        prog="metronome",
        description="课堂节拍器：生成离线可用的单文件网页节拍器",
    )
    parser.add_argument(
        "--version", action="version", version="metronome 0.1.0"
    )
    parser.add_argument(
        "--bpm",
        type=int,
        default=90,
        help="速度，%d~%d BPM（默认 90）" % (MIN_BPM, MAX_BPM),
    )
    parser.add_argument(
        "--beats",
        type=int,
        default=4,
        help="每小节拍数，%d~%d（默认 4）" % (MIN_BEATS, MAX_BEATS),
    )
    parser.add_argument(
        "--accent",
        type=int,
        default=1,
        help="重拍位置，1~每小节拍数（默认 1）",
    )
    parser.add_argument(
        "--minutes",
        type=int,
        default=5,
        help="练习时长，%d~%d 分钟（默认 5）" % (MIN_MINUTES, MAX_MINUTES),
    )
    parser.add_argument("--title", default="节拍器", help="页面标题")
    parser.add_argument(
        "-o", "--output", default="节拍器.html", help="输出 HTML 路径"
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        config = MetronomeConfig(
            bpm=args.bpm,
            beats=args.beats,
            accent=args.accent,
            minutes=args.minutes,
            title=args.title,
        )
        page = render_html(config)
    except MetronomeError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    print(
        "已生成 %s：%d BPM，%d/%d 拍，重拍第 %d 拍，%d 分钟"
        % (
            args.output,
            config.bpm,
            config.beats,
            config.beats,
            config.accent,
            config.minutes,
        )
    )
    print("用浏览器打开即可练习；空格键开始或暂停")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
