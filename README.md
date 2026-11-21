# metronome

[![CI](https://github.com/eastyou/metronome/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/metronome/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给音乐课和练琴用的网页节拍器：一条命令生成**单文件、离线可用**的 HTML。声音由 Web Audio API 实时合成，不依赖任何音频文件、图片、字体或 CDN，拷到 U 盘或投影电脑上双击就能用。

深色大屏界面适合投影；BPM、拍号、剩余时间一目了然，重拍用橙色高亮和更高的提示音区分。

## 特性

- **单文件离线**：所有 HTML/CSS/JS 内嵌，零第三方依赖，不联网
- **大屏显示**：超大 BPM、当前拍号（如 `3/4`）、剩余时间，深色高对比
- **每拍高亮**：圆点随节拍点亮，重拍使用橙色与更响、更高的提示音
- **准时调度**：Web Audio 提前排程，避免 `setInterval` 抖动，节奏更稳
- **倒计时停止**：练习时长结束自动停止并显示「时间到」
- **空格键控制**：空格开始 / 暂停，不碰鼠标也能操作
- **快速调速**：`-5` / `+5` 按钮以 5 BPM 调整，立即生效
- **拍速测量**：点击「拍速」按钮，按点击间隔自动测出 BPM
- **严格校验**：BPM、拍数、重拍、时长、标题全部校验，中文报错
- **安全内嵌**：标题 HTML 转义，JSON 中的 `</script>` 不会破坏页面
- **85 个单元测试**：覆盖边界校验、转义、页面内容、退出码与文件输出

## 安装

```bash
pip install metronome
```

也可以直接下载源码，在项目目录运行：

```bash
python -m metronome --help
```

## 用法

生成课堂用的 4/4 拍、90 BPM、重拍在第一拍、5 分钟倒计时的节拍器：

```bash
python -m metronome --bpm 90 --beats 4 --accent 1 --minutes 5 --title 课堂节拍器 -o examples/节拍器.html
```

然后用浏览器打开 `examples/节拍器.html`。

### 参数

| 参数 | 说明 | 范围 | 默认 |
| --- | --- | --- | --- |
| `--bpm` | 速度 | 30~240 | `90` |
| `--beats` | 每小节拍数 | 1~12 | `4` |
| `--accent` | 重拍位置 | 1~`--beats` | `1` |
| `--minutes` | 练习时长（分钟） | 1~60 | `5` |
| `--title` | 页面标题，最多 40 字 | 非空 | `节拍器` |
| `-o, --output` | 输出 HTML 路径 | — | `节拍器.html` |
| `--version` | 显示版本 | — | — |

参数错误时输出中文提示并退出码 `2`；写文件失败退出码 `1`；成功退出码 `0`。

## 浏览器使用

1. 用 Chrome、Edge、Firefox 或 Safari 打开生成的 HTML。
2. 点击「开始」（部分浏览器要求先有一次点击才允许播放声音）。
3. **空格键**随时开始或暂停；「重置」回到完整时长。
4. **`-5` / `+5`** 调整速度，正在播放时下一拍立即使用新速度。
5. **「拍速」**：跟着心里想要的速度连续点击几次，页面上方 BPM 会自动更新。
6. 投影时可按 `F11` 全屏；页面宽度不足时自动换行，不会横向溢出。

练习时长归零后自动停止，状态栏显示「时间到」。

## 页面说明

- 初始配置由 CLI 参数写入页面内的 JSON（`#metronome-config`），打开即用。
- 提示音由 `OscillatorNode` 合成：重拍 1568 Hz、音量更高，普通拍 880 Hz。
- 倒计时使用单调时钟计算，暂停后继续不会丢失已用时间。
- 页面不引用任何外部资源，断网、离线、内网电脑都能正常使用。

## 项目结构

```text
metronome/
├── metronome/
│   ├── __init__.py   # 包导出与版本号
│   ├── __main__.py   # python -m metronome
│   ├── model.py      # 配置校验、安全 JSON、时间格式化
│   ├── render.py     # 单文件 HTML/CSS/JS 渲染
│   └── cli.py        # 命令行参数与退出码
├── tests/
│   ├── test_model.py
│   ├── test_render.py
│   └── test_cli.py
├── examples/
│   └── 节拍器.html   # 示例产物
└── .github/workflows/ci.yml
```

## 开发

```bash
# 运行全部单元测试（85 个）
python -m unittest discover -s tests

# 重新生成示例页面
python -m metronome --bpm 90 --beats 4 --accent 1 --minutes 5 \
  --title 课堂节拍器 -o examples/节拍器.html
```

CI 在 Ubuntu / macOS / Windows 上运行 Python 3.10 与 3.13，并额外覆盖 Ubuntu 22.04 + Python 3.9；单测之后还会生成页面并断言行内脚本、Web Audio 与倒计时内容。

## 许可证

[MIT](LICENSE) © 2026 eastyou
