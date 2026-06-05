"""SlackTime — a soft, non-blocking reminder to drink water and stretch.

A background tray app. Every N minutes (default 40) a small toast softly
slides in from the left across the top of the screen, then slides back out.
Use the tray/menu-bar icon to pause/resume, change the interval, or quit.

The tray backend and main-thread ownership differ per OS and live in
platform_support (pystray on Windows, rumps on macOS); this module holds the
shared scheduling and toast-rendering logic.
"""

import json
import threading
import tkinter as tk
from pathlib import Path

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


def make_icon_image():
    """The water-drop tray icon, as a Pillow image (shared by all backends)."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((18, 30, 46, 58), fill=(70, 150, 230, 255))
    d.polygon([(32, 8), (20, 36), (44, 36)], fill=(70, 150, 230, 255))
    return img


def _bind_recursive(widget, event, callback):
    widget.bind(event, callback)
    for child in widget.winfo_children():
        _bind_recursive(child, event, callback)


class SlackTime:
    """Backend-agnostic core: scheduling, state, and toast rendering.

    A platform `run(app)` function owns the main thread and the tray UI, and
    calls these action methods in response to menu clicks:
        toggle_pause() · set_interval(m) · remind_now() · toggle_autostart() · quit()
    """

    def __init__(self):
        self.interval_min = load_interval()
        self.interval_choices = INTERVAL_CHOICES
        self.paused = False
        self._timer = None
        self.on_changed = None      # backend sets this to refresh its menu

        # Tk is created here but its loop is driven by the platform run().
        self.root = tk.Tk()
        self.root.withdraw()

    def icon_image(self):
        return make_icon_image()

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
        # Timer runs off-thread; hand the drawing back to Tk.
        self.root.after(0, self._show_toast)
        self._schedule()

    def _notify_changed(self):
        if self.on_changed:
            self.on_changed()

    # ---- actions (called by the platform tray backend) ----
    def toggle_pause(self):
        self.paused = not self.paused
        self._notify_changed()
        self._schedule()

    def set_interval(self, minutes):
        self.interval_min = minutes
        save_interval(minutes)
        self._notify_changed()
        self._schedule()

    def remind_now(self):
        self.root.after(0, self._show_toast)

    def toggle_autostart(self):
        if PLATFORM.is_autostart_enabled():
            PLATFORM.remove_autostart()
        else:
            PLATFORM.install_autostart()
        self._notify_changed()

    def quit(self):
        self._cancel()
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

    # ---- lifecycle ----
    def start_scheduling(self):
        """Begin the reminder timer. The platform run() owns the main loop."""
        self._schedule()


if __name__ == "__main__":
    app = SlackTime()
    app.start_scheduling()
    # Each OS owns the main thread and tray UI its own way.
    PLATFORM.run(app)
