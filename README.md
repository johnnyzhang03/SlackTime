<div align="center">

# 💧 SlackTime

### *Your gentle nudge to drink water and stretch — without breaking your flow.*

A soft, non-blocking desktop reminder for Windows that slides quietly across
the top of every screen, then disappears. No pop-ups. No blocking. No nagging.

`Stay hydrated.` &nbsp;•&nbsp; `Stretch often.` &nbsp;•&nbsp; `Keep working.`

</div>

---

## ✨ Why SlackTime?

Most reminder apps **interrupt** you — a modal dialog steals focus, a system
notification piles up in the Action Center, and you dismiss it without a second
thought. SlackTime is different:

| | |
|---|---|
| 🌊 **Soft & floating** | A small toast glides in from the left, holds for a moment, then slides away |
| 🚫 **Never blocks you** | It never steals focus or interrupts your typing — glance at it or ignore it |
| 🖥️ **Multi-monitor aware** | The reminder appears on **every** screen, perfectly centered on each |
| ⏱️ **Your rhythm** | Default every 40 minutes — adjustable to 15 / 20 / 30 / 40 / 60 / 90 |
| 🪶 **Lives in the tray** | Quietly runs in the background with a tiny water-drop icon |
| 🔁 **Starts with Windows** | One-click install sets it to launch automatically at login |

---

## 🚀 Quick Start

### Option A — Just run it (Python)

```bash
pip install -r requirements.txt
python slacktime.py
```

> Tip: use `pythonw slacktime.py` to launch with **no console window**.

### Option B — Build a standalone app + auto-start 🪄

No Python needed after building. Double-click:

```bash
build.bat
```

This builds `SlackTime.exe`, installs it to `%LOCALAPPDATA%\SlackTime`, and
adds a Startup shortcut so it **launches every time you log in**.

> **Why a folder, not a single .exe?** Corporate machines often run Application
> Control (WDAC/AppLocker) that blocks DLLs loaded from `%TEMP%`. The build uses
> PyInstaller's `--onedir` mode so everything lives in one fixed folder — no
> temp extraction, no policy errors.

---

## 🎛️ Controls

Right-click the **💧 water-drop icon** in your system tray:

```
💧 SlackTime
 ├─ Pause / Resume
 ├─ Remind now        ← preview the toast instantly
 ├─ Interval ▸        ← 15 · 20 · 30 · 40 · 60 · 90 min
 └─ Quit
```

- Your chosen interval is **saved across restarts**.
- **Click any toast** to dismiss it early.

> Can't find the icon? On Windows 11 it may be tucked under the **`^`** (show
> hidden icons) arrow on the taskbar — drag it out to pin it.

---

## 🩹 Uninstall / Disable

| Goal | How |
|---|---|
| Stop it auto-starting | Delete `SlackTime.lnk` from the Startup folder (run `shell:startup` in **Win+R**) |
| Quit it now | Right-click tray icon → **Quit** |
| Remove it completely | Delete `%LOCALAPPDATA%\SlackTime` and the Startup shortcut |

---

## 🛠️ Built With

- **[tkinter](https://docs.python.org/3/library/tkinter.html)** — the floating toast & slide animation
- **[pystray](https://pypi.org/project/pystray/)** — the system-tray icon & menu
- **[Pillow](https://pypi.org/project/pillow/)** — draws the water-drop icon
- **[screeninfo](https://pypi.org/project/screeninfo/)** — finds every monitor
- **[PyInstaller](https://pyinstaller.org/)** — bundles it into a standalone app

---

<div align="center">

*Made to keep you hydrated, limber, and in the zone.* 💧🧘

</div>
