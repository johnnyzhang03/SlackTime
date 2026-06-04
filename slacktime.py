"""SlackTime — a soft, non-blocking reminder to drink water and stretch.

A background tray app. Every N minutes (default 40) a small toast softly
slides in from the left across the top of the screen, then slides back out.
Right-click the tray icon to pause/resume, change the interval, or quit.
"""

import json
import threading
import tkinter as tk
from pathlib import Path

import pystray
from PIL import Image, ImageDraw
from screeninfo import get_monitors

CONFIG_PATH = Path(__file__).with_name("slacktime_config.json")
DEFAULT_INTERVAL_MIN = 40
INTERVAL_CHOICES = [15, 20, 30, 40, 60, 90]

MESSAGE = "Time to drink water and stretch"
TOAST_W = 320
TOAST_H = 64
SLIDE_MS = 5        # frame delay during slide
SLIDE_STEP = 8      # px per frame
HOLD_MS = 4000       # how long the toast lingers fully visible


def load_interval():
    try:
        return int(json.loads(CONFIG_PATH.read_text())["interval_min"])
    except Exception:
        return DEFAULT_INTERVAL_MIN


def save_interval(minutes):
    try:
        CONFIG_PATH.write_text(json.dumps({"interval_min": minutes}))
    except Exception:
        pass


def _bind_recursive(widget, event, callback):
    widget.bind(event, callback)
    for child in widget.winfo_children():
        _bind_recursive(child, event, callback)


class SlackTime:
    def __init__(self):
        self.interval_min = load_interval()
        self.paused = False
        self._timer = None

        # Tkinter must live on one thread; we own the main thread.
        self.root = tk.Tk()
        self.root.withdraw()

        self.icon = pystray.Icon(
            "slacktime", self._make_icon(), "SlackTime", self._build_menu()
        )

    # ---- tray icon image ----
    def _make_icon(self):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # a simple water drop
        d.ellipse((18, 30, 46, 58), fill=(70, 150, 230, 255))
        d.polygon([(32, 8), (20, 36), (44, 36)], fill=(70, 150, 230, 255))
        return img

    def _build_menu(self):
        interval_items = [
            pystray.MenuItem(
                f"{m} min",
                (lambda m: lambda: self._set_interval(m))(m),
                checked=(lambda m: lambda item: self.interval_min == m)(m),
                radio=True,
            )
            for m in INTERVAL_CHOICES
        ]
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: "Resume" if self.paused else "Pause",
                self._toggle_pause,
            ),
            pystray.MenuItem("Remind now", self._remind_now),
            pystray.MenuItem("Interval", pystray.Menu(*interval_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

    # ---- scheduling ----
    def _schedule(self):
        self._cancel()
        if self.paused:
            return
        self._timer = threading.Timer(self.interval_min * 60, self._fire)
        self._timer.daemon = True
        self._timer.start()

    def _cancel(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _fire(self):
        # Hand off to the Tk thread to draw the toast.
        self.root.after(0, self._show_toast)
        self._schedule()

    # ---- menu actions ----
    def _toggle_pause(self, icon, item):
        self.paused = not self.paused
        self.icon.update_menu()
        self._schedule()

    def _set_interval(self, minutes):
        self.interval_min = minutes
        save_interval(minutes)
        self.icon.update_menu()
        self._schedule()

    def _remind_now(self, icon, item):
        self.root.after(0, self._show_toast)

    def _quit(self, icon, item):
        self._cancel()
        self.icon.stop()
        self.root.after(0, self.root.quit)

    # ---- the soft slide-in toast (one per monitor) ----
    def _show_toast(self):
        for m in get_monitors():
            self._show_toast_on(m.x, m.y, m.width)

    def _show_toast_on(self, mon_x, mon_y, mon_w):
        offscreen_x = mon_x - TOAST_W            # fully hidden, just left of the screen
        center_x = mon_x + (mon_w - TOAST_W) // 2
        exit_x = mon_x + mon_w                   # past the right edge
        y = mon_y + 24

        win = self._build_toast(offscreen_x, y)

        # click anywhere on the toast to dismiss it early
        dismiss = lambda _e: self._slide(win, exit_x, y, win.destroy)
        _bind_recursive(win, "<Button-1>", dismiss)

        # slide in → hold → slide out
        self._slide(win, center_x, y,
                    lambda: win.after(HOLD_MS,
                                      lambda: self._slide(win, exit_x, y, win.destroy)))

    def _build_toast(self, x, y):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        try:
            win.attributes("-alpha", 0.96)
        except tk.TclError:
            pass
        win.configure(bg="#1f2937")
        win.geometry(f"{TOAST_W}x{TOAST_H}+{x}+{y}")

        frame = tk.Frame(win, bg="#1f2937")
        frame.pack(fill="both", expand=True, padx=16, pady=10)
        tk.Label(frame, text="\U0001F4A7", bg="#1f2937", fg="#7cc4fa",
                 font=("Segoe UI Emoji", 22)).pack(side="left", padx=(0, 12))
        tk.Label(frame, text=MESSAGE, bg="#1f2937", fg="#f3f4f6",
                 font=("Segoe UI", 12), justify="left").pack(side="left")
        return win

    def _slide(self, win, target_x, y, on_done):
        """Move the toast toward target_x one step per frame, then call on_done."""
        if not win.winfo_exists():
            return
        x = win.winfo_x()
        step = SLIDE_STEP if target_x > x else -SLIDE_STEP
        x = min(x + step, target_x) if step > 0 else max(x + step, target_x)
        win.geometry(f"{TOAST_W}x{TOAST_H}+{x}+{y}")
        if x != target_x:
            win.after(SLIDE_MS, lambda: self._slide(win, target_x, y, on_done))
        elif on_done:
            on_done()

    # ---- run ----
    def run(self):
        self._schedule()
        threading.Thread(target=self.icon.run, daemon=True).start()
        self.root.mainloop()


if __name__ == "__main__":
    SlackTime().run()
