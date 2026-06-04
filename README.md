# SlackTime

A soft, non-blocking desktop reminder to drink water and stretch.

Every N minutes (default 40, adjustable) a small toast slides in from the
left across the top of each monitor, holds briefly, then slides off — gentle,
never blocking your work. Runs quietly in the system tray.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python slacktime.py
```

Use `pythonw slacktime.py` to run without a console window.

## Controls

Right-click the water-drop tray icon:

- **Pause / Resume**
- **Remind now** — preview the toast
- **Interval** — 15 / 20 / 30 / 40 / 60 / 90 minutes (saved across restarts)
- **Quit**

Click any toast to dismiss it early.
