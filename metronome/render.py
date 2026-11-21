"""把节拍器配置渲染成单文件、离线可用的交互页面。"""

from __future__ import annotations

import html

from .model import MetronomeConfig, MetronomeError, format_clock


def _dots(config: MetronomeConfig) -> str:
    """生成每拍的圆点，重拍使用 accent 样式。"""
    parts = []
    for number in range(1, config.beats + 1):
        classes = "dot accent" if number == config.accent else "dot"
        parts.append(
            '<div class="%s" data-beat="%d"><span>%d</span></div>'
            % (classes, number, number)
        )
    return "".join(parts)


def _style() -> str:
    return """
  :root {
    color-scheme: dark;
    --bg: #060a12;
    --panel: #0d1626;
    --line: #243247;
    --text: #f8fafc;
    --muted: #94a3b8;
    --beat: #38bdf8;
    --beat-soft: rgba(56, 189, 248, 0.3);
    --accent: #f97316;
    --accent-soft: rgba(249, 115, 22, 0.34);
    --done: #facc15;
  }
  * { box-sizing: border-box; }
  html, body { max-width: 100%; overflow-x: hidden; }
  body {
    margin: 0;
    min-height: 100vh;
    padding: clamp(14px, 3vw, 36px);
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle at 18% 0%, #13233f 0%, var(--bg) 46%) fixed;
    color: var(--text);
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC",
      "Segoe UI", sans-serif;
  }
  .app { width: 100%; max-width: 1080px; min-width: 0; }
  .top {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 6px 18px;
    margin-bottom: clamp(12px, 2.2vw, 24px);
  }
  h1 {
    margin: 0;
    font-size: clamp(20px, 3vw, 30px);
    line-height: 1.25;
    letter-spacing: 2px;
    overflow-wrap: anywhere;
  }
  .subtitle {
    margin: 0;
    color: var(--muted);
    font-size: clamp(12px, 1.6vw, 15px);
  }
  .panel {
    padding: clamp(16px, 3.6vw, 40px);
    border: 1px solid var(--line);
    border-radius: 24px;
    background: linear-gradient(160deg, #111e35 0%, #091120 100%);
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
  }
  .bpm-row {
    display: flex;
    align-items: flex-end;
    justify-content: center;
    gap: clamp(8px, 1.6vw, 16px);
  }
  #bpmValue {
    font-size: clamp(68px, 18vw, 188px);
    line-height: 0.88;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.04em;
    text-shadow: 0 0 42px rgba(56, 189, 248, 0.26);
  }
  .unit {
    padding-bottom: clamp(10px, 2.2vw, 24px);
    color: var(--muted);
    font-size: clamp(15px, 2.6vw, 26px);
    font-weight: 700;
    letter-spacing: 3px;
  }
  .readouts {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: clamp(8px, 1.6vw, 18px);
    margin-top: clamp(10px, 2vw, 18px);
  }
  .readout {
    flex: 1 1 150px;
    min-width: 0;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    padding: 9px clamp(12px, 2vw, 20px);
    border: 1px solid var(--line);
    border-radius: 14px;
    background: rgba(148, 163, 184, 0.06);
  }
  .readout .label {
    color: var(--muted);
    font-size: clamp(12px, 1.5vw, 15px);
    letter-spacing: 2px;
    white-space: nowrap;
  }
  .readout .value {
    font-size: clamp(22px, 3.6vw, 36px);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .beats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(44px, 1fr));
    gap: clamp(7px, 1.3vw, 13px);
    margin: clamp(14px, 2.8vw, 28px) 0;
  }
  .dot {
    display: flex;
    align-items: center;
    justify-content: center;
    aspect-ratio: 1 / 1;
    min-width: 0;
    border: 2px solid #334155;
    border-radius: 50%;
    background: #0a1322;
    color: #64748b;
    font-size: clamp(14px, 2vw, 22px);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    transition: transform 0.08s ease, background 0.08s ease,
      border-color 0.08s ease, color 0.08s ease, box-shadow 0.08s ease;
  }
  .dot.accent { border-color: rgba(249, 115, 22, 0.7); color: #fdba74; }
  .dot.active {
    transform: scale(1.09);
    border-color: var(--beat);
    background: var(--beat);
    color: #04121f;
    box-shadow: 0 0 30px var(--beat-soft);
  }
  .dot.accent.active {
    border-color: var(--accent);
    background: var(--accent);
    color: #1a0d02;
    box-shadow: 0 0 34px var(--accent-soft);
  }
  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: clamp(8px, 1.3vw, 13px);
  }
  button {
    flex: 0 1 auto;
    min-width: 0;
    padding: clamp(11px, 1.7vw, 16px) clamp(15px, 2.5vw, 26px);
    border: 1px solid #334155;
    border-radius: 14px;
    background: #111c30;
    color: var(--text);
    font: inherit;
    font-size: clamp(14px, 1.8vw, 18px);
    font-weight: 700;
    cursor: pointer;
    transition: background 0.12s ease, border-color 0.12s ease,
      transform 0.08s ease;
  }
  button:hover { border-color: #64748b; background: #17243c; }
  button:active { transform: translateY(1px); }
  button:focus-visible { outline: 3px solid var(--beat); outline-offset: 2px; }
  button.primary {
    flex: 1 1 190px;
    border-color: #22c55e;
    background: linear-gradient(180deg, #22c55e, #16a34a);
    color: #04130a;
  }
  button.primary:hover {
    border-color: #4ade80;
    background: linear-gradient(180deg, #4ade80, #22c55e);
  }
  .status {
    min-height: 1.5em;
    margin: clamp(11px, 1.8vw, 18px) 0 0;
    text-align: center;
    color: var(--muted);
    font-size: clamp(13px, 1.7vw, 16px);
  }
  .status.done {
    color: var(--done);
    font-size: clamp(17px, 2.2vw, 23px);
    font-weight: 800;
    letter-spacing: 2px;
  }
  @media (prefers-reduced-motion: reduce) {
    .dot, button { transition: none; }
  }
"""


def _script() -> str:
    return """
(function () {
  "use strict";

  var configNode = document.getElementById("metronome-config");
  if (!configNode) { return; }

  var config;
  try {
    config = JSON.parse(configNode.textContent || "{}");
  } catch (error) {
    return;
  }

  var MIN_BPM = 30;
  var MAX_BPM = 240;
  var BPM_STEP = 5;
  var LOOKAHEAD_MS = 25;
  var SCHEDULE_AHEAD = 0.12;
  var TAP_TIMEOUT_MS = 2000;

  function clampNumber(value, minimum, maximum, fallback) {
    var number = Number(value);
    if (!isFinite(number)) { return fallback; }
    return Math.min(maximum, Math.max(minimum, number));
  }

  var bpm = Math.round(clampNumber(config.bpm, MIN_BPM, MAX_BPM, 90));
  var beats = Math.round(clampNumber(config.beats, 1, 12, 4));
  var accent = Math.round(clampNumber(config.accent, 1, beats, 1));
  var minutes = Math.round(clampNumber(config.minutes, 1, 60, 5));
  var totalSeconds = minutes * 60;

  var bpmValue = document.getElementById("bpmValue");
  var beatLabel = document.getElementById("beatLabel");
  var timeLeft = document.getElementById("timeLeft");
  var status = document.getElementById("status");
  var startBtn = document.getElementById("startBtn");
  var resetBtn = document.getElementById("resetBtn");
  var minusBtn = document.getElementById("minusBtn");
  var plusBtn = document.getElementById("plusBtn");
  var tapBtn = document.getElementById("tapBtn");
  var dots = Array.prototype.slice.call(document.querySelectorAll(".dot"));

  var playing = false;
  var audioContext = null;
  var schedulerId = null;
  var visualTimers = [];
  var nextNoteTime = 0;
  var beatIndex = 0;
  var remaining = totalSeconds;
  var remainingAtStart = totalSeconds;
  var startedAt = 0;
  var tapTimes = [];

  function formatClock(seconds) {
    var safe = Math.max(0, Math.ceil(seconds));
    var wholeMinutes = Math.floor(safe / 60);
    var rest = safe % 60;
    return (wholeMinutes < 10 ? "0" : "") + wholeMinutes +
      ":" + (rest < 10 ? "0" : "") + rest;
  }

  function updateReadouts() {
    timeLeft.textContent = formatClock(remaining);
    beatLabel.textContent = (beatIndex + 1) + "/" + beats;
  }

  function clearActive() {
    for (var i = 0; i < dots.length; i += 1) {
      dots[i].classList.remove("active");
    }
  }

  function paintBeat(index) {
    beatLabel.textContent = (index + 1) + "/" + beats;
    for (var i = 0; i < dots.length; i += 1) {
      if (i === index) {
        dots[i].classList.add("active");
      } else {
        dots[i].classList.remove("active");
      }
    }
  }

  function clearVisualTimers() {
    for (var i = 0; i < visualTimers.length; i += 1) {
      window.clearTimeout(visualTimers[i]);
    }
    visualTimers = [];
  }

  function stopScheduler() {
    if (schedulerId !== null) {
      window.clearInterval(schedulerId);
      schedulerId = null;
    }
    clearVisualTimers();
  }

  function ensureAudio() {
    var AudioCtor = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtor) { return null; }
    if (!audioContext) {
      audioContext = new AudioCtor();
    }
    if (audioContext.state === "suspended") {
      audioContext.resume();
    }
    return audioContext;
  }

  function playClick(time, isAccent) {
    if (!audioContext) { return; }
    var oscillator = audioContext.createOscillator();
    var gain = audioContext.createGain();
    var peak = isAccent ? 0.55 : 0.22;
    var duration = isAccent ? 0.09 : 0.055;
    oscillator.type = isAccent ? "triangle" : "sine";
    oscillator.frequency.setValueAtTime(isAccent ? 1568 : 880, time);
    gain.gain.setValueAtTime(0.0001, time);
    gain.gain.exponentialRampToValueAtTime(peak, time + 0.004);
    gain.gain.exponentialRampToValueAtTime(0.0001, time + duration);
    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start(time);
    oscillator.stop(time + duration + 0.02);
  }

  function finish() {
    playing = false;
    stopScheduler();
    remaining = 0;
    remainingAtStart = 0;
    beatIndex = 0;
    clearActive();
    timeLeft.textContent = "00:00";
    beatLabel.textContent = "1/" + beats;
    startBtn.textContent = "开始";
    status.textContent = "时间到";
    status.classList.add("done");
  }

  function scheduleAhead() {
    if (!playing || !audioContext) { return; }
    remaining = Math.max(
      0,
      remainingAtStart - (performance.now() - startedAt) / 1000
    );
    timeLeft.textContent = formatClock(remaining);
    if (remaining <= 0) {
      finish();
      return;
    }

    var horizon = audioContext.currentTime + SCHEDULE_AHEAD;
    while (nextNoteTime < horizon) {
      var isAccent = beatIndex === accent - 1;
      var shownBeat = beatIndex;
      var delay = Math.max(
        0,
        (nextNoteTime - audioContext.currentTime) * 1000
      );
      playClick(nextNoteTime, isAccent);
      visualTimers.push(window.setTimeout(function (index) {
        return function () { paintBeat(index); };
      }(shownBeat), delay));
      nextNoteTime += 60 / bpm;
      beatIndex = (beatIndex + 1) % beats;
    }
  }

  function start() {
    if (playing) {
      pause();
      return;
    }
    if (remaining <= 0) {
      remaining = totalSeconds;
      remainingAtStart = totalSeconds;
      beatIndex = 0;
      clearActive();
    }
    var context = ensureAudio();
    if (!context) {
      status.textContent = "当前浏览器不支持 Web Audio";
      return;
    }
    playing = true;
    startedAt = performance.now();
    remainingAtStart = remaining;
    nextNoteTime = context.currentTime + 0.08;
    startBtn.textContent = "暂停";
    status.textContent = "练习中：空格键暂停";
    status.classList.remove("done");
    schedulerId = window.setInterval(scheduleAhead, LOOKAHEAD_MS);
    scheduleAhead();
  }

  function pause() {
    if (!playing) { return; }
    remaining = Math.max(
      0,
      remainingAtStart - (performance.now() - startedAt) / 1000
    );
    playing = false;
    stopScheduler();
    startBtn.textContent = "继续";
    status.textContent = "已暂停：按空格或点击继续";
  }

  function reset() {
    playing = false;
    stopScheduler();
    remaining = totalSeconds;
    remainingAtStart = totalSeconds;
    beatIndex = 0;
    tapTimes = [];
    clearActive();
    updateReadouts();
    startBtn.textContent = "开始";
    status.textContent = "按空格开始或暂停";
    status.classList.remove("done");
  }

  function setBpm(value) {
    var next = Math.round(clampNumber(value, MIN_BPM, MAX_BPM, bpm));
    bpm = next;
    bpmValue.textContent = String(bpm);
  }

  function tapTempo() {
    var now = performance.now();
    if (tapTimes.length > 0 &&
        now - tapTimes[tapTimes.length - 1] > TAP_TIMEOUT_MS) {
      tapTimes = [];
    }
    tapTimes.push(now);
    if (tapTimes.length > 7) {
      tapTimes.shift();
    }
    if (tapTimes.length < 2) {
      status.textContent = "拍速：请继续跟着节拍点击";
      return;
    }
    var average = (tapTimes[tapTimes.length - 1] - tapTimes[0]) /
      (tapTimes.length - 1);
    setBpm(60000 / average);
    status.textContent = "拍速：" + bpm + " BPM";
  }

  startBtn.addEventListener("click", start);
  resetBtn.addEventListener("click", reset);
  minusBtn.addEventListener("click", function () {
    setBpm(bpm - BPM_STEP);
  });
  plusBtn.addEventListener("click", function () {
    setBpm(bpm + BPM_STEP);
  });
  tapBtn.addEventListener("click", tapTempo);

  document.addEventListener("keydown", function (event) {
    var isSpace = event.code === "Space" || event.key === " " ||
      event.key === "Spacebar";
    if (!isSpace || event.repeat) { return; }
    var target = event.target;
    var tag = target && target.tagName ? target.tagName.toUpperCase() : "";
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") { return; }
    if (target && target.isContentEditable) { return; }
    event.preventDefault();
    start();
  });

  bpmValue.textContent = String(bpm);
  updateReadouts();
})();
"""


def render_html(config: MetronomeConfig) -> str:
    """生成自包含的暗色节拍器页面。"""
    if not isinstance(config, MetronomeConfig):
        raise MetronomeError("config 必须是 MetronomeConfig 对象")

    title = html.escape(config.title)
    subtitle = html.escape(
        "%d 拍 · 重拍第 %d 拍 · 练习 %d 分钟"
        % (config.beats, config.accent, config.minutes)
    )
    clock = format_clock(config.total_seconds)
    dots = _dots(config)

    return "".join(
        [
            "<!doctype html>\n",
            '<html lang="zh-CN">\n',
            "<head>\n",
            '<meta charset="utf-8">\n',
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
            "<title>%s</title>\n" % title,
            "<style>%s</style>\n" % _style(),
            "</head>\n",
            "<body>\n",
            '<main class="app">\n',
            '<header class="top">\n',
            "<h1>%s</h1>\n" % title,
            '<p class="subtitle">%s</p>\n' % subtitle,
            "</header>\n",
            '<section class="panel" aria-label="节拍器控制面板">\n',
            '<div class="bpm-row">',
            '<span id="bpmValue">%d</span>' % config.bpm,
            '<span class="unit">BPM</span>',
            "</div>\n",
            '<div class="readouts">\n',
            '<div class="readout"><span class="label">拍号</span>'
            '<span class="value" id="beatLabel">1/%d</span></div>\n'
            % config.beats,
            '<div class="readout"><span class="label">剩余</span>'
            '<span class="value" id="timeLeft">%s</span></div>\n' % clock,
            "</div>\n",
            '<div class="beats" id="beats" aria-hidden="true">%s</div>\n' % dots,
            '<div class="controls">\n',
            '<button id="startBtn" class="primary" type="button">开始</button>\n',
            '<button id="resetBtn" type="button">重置</button>\n',
            '<button id="minusBtn" type="button" aria-label="降低 5 BPM">-5</button>\n',
            '<button id="plusBtn" type="button" aria-label="提高 5 BPM">+5</button>\n',
            '<button id="tapBtn" type="button">拍速</button>\n',
            "</div>\n",
            '<p id="status" class="status" role="status" aria-live="polite">'
            "按空格开始或暂停</p>\n",
            "</section>\n",
            "</main>\n",
            '<script id="metronome-config" type="application/json">%s</script>\n'
            % config.to_json(),
            "<script>%s</script>\n" % _script(),
            "</body>\n",
            "</html>\n",
        ]
    )
