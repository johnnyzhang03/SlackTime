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

import platform_support

PLATFORM = platform_support.current()

CONFIG_PATH = Path(__file__).with_name("slacktime_config.json")
DEFAULT_INTERVAL_MIN = 40
INTERVAL_CHOICES = [15, 20, 30, 40, 60, 90]

MESSAGE = "Time to drink water and stretch"
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
            pystray.MenuItem(
                "Start at login",
                self._toggle_autostart,
                checked=lambda item: PLATFORM.is_autostart_enabled(),
            ),
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

    def _toggle_autostart(self, icon, item):
        if PLATFORM.is_autostart_enabled():
            PLATFORM.remove_autostart()
        else:
            PLATFORM.install_autostart()
        self.icon.update_menu()

    def _quit(self, icon, item):
        self._cancel()
        self.icon.stop()
        self.root.after(0, self.root.quit)

    # ---- the soft slide-in toast (one per monitor) ----
    def _show_toast(self):
        for m in get_monitors():
            self._show_toast_on(m.x, m.y, m.width)

    def _show_toast_on(self, mon_x, mon_y, mon_w):
        win, width = self._build_toast(mon_x, mon_y + 24)

        start_x = mon_x                                  # flush against the left edge
        center_x = mon_x + (mon_w - width) // 2
        exit_x = mon_x + mon_w - width                   # flush against the right edge
        y = mon_y + 24

        # click anywhere on the toast to dismiss it immediately
        _bind_recursive(win, "<Button-1>", lambda _e: win.destroy())

        # slide in from the left → hold → slide out to the right → destroy
        self._slide(win, width, start_x, center_x, y,
                    lambda: win.after(
                        HOLD_MS,
                        lambda: self._slide(win, width, center_x, exit_x, y,
                                            win.destroy)))

    def _build_toast(self, x, y):
        win = tk.Toplevel(self.root)
        PLATFORM.style_toast_window(win)
        win.configure(bg="#1f2937")

        frame = tk.Frame(win, bg="#1f2937")
        frame.pack(fill="both", expand=True, padx=16, pady=10)
        tk.Label(frame, text="\U0001F4A7", bg="#1f2937", fg="#7cc4fa",
                 font=PLATFORM.FONT_EMOJI).pack(side="left", padx=(0, 12))
        tk.Label(frame, text=MESSAGE, bg="#1f2937", fg="#f3f4f6",
                 font=PLATFORM.FONT_UI, justify="left").pack(side="left")

        # size the window to fit its contents instead of a fixed width
        win.update_idletasks()
        width = win.winfo_reqwidth()
        win.geometry(f"{width}x{TOAST_H}+{x}+{y}")
        return win, width

    def _slide(self, win, width, x, target_x, y, on_done):
        """Move the toast from x toward target_x one step per frame, then on_done."""
        if not win.winfo_exists():
            return
        if x == target_x:
            if on_done:
                on_done()
            return
        step = SLIDE_STEP if target_x > x else -SLIDE_STEP
        x = min(x + step, target_x) if step > 0 else max(x + step, target_x)
        win.geometry(f"{width}x{TOAST_H}+{x}+{y}")
        win.after(SLIDE_MS, lambda: self._slide(win, width, x, target_x, y, on_done))

    # ---- run ----
    def run(self):
        self._schedule()
        # Tk owns the main thread; the tray icon runs alongside it.
        # On macOS the tray backend (AppKit) is happiest on the main thread —
        # if the icon misbehaves there, that's the first thing to revisit.
        threading.Thread(target=self.icon.run, daemon=True).start()
        self.root.mainloop()


if __name__ == "__main__":
    SlackTime().run()
