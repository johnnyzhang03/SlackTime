"""macOS-specific behaviour for SlackTime.

UNTESTED on real hardware — written against the documented macOS / Tk / launchd
behaviour. Expect to tune the toast styling, the menu-bar app, and the
LaunchAgent once you can run it on a Mac. The interface matches
platform_support.windows so slacktime.py needs no changes.

Why this is different from Windows: on macOS both Tk and the tray backend insist
on the main thread, so the Windows "pystray on a background thread" model
crashes. Here a rumps menu-bar app owns the main thread and AppKit run loop, and
a rumps Timer (which fires on the main thread) pumps Tk via root.update() so the
toast still animates — Tk never gets its own mainloop().
"""

import sys
from pathlib import Path

# macOS ships these system fonts; "Apple Color Emoji" renders the water drop.
FONT_UI = ("Helvetica Neue", 13)
FONT_EMOJI = ("Apple Color Emoji", 22)


def run(app):
    """Own the main thread with a rumps menu-bar app; pump Tk from a timer."""
    import rumps

    menubar = rumps.App("SlackTime", title="💧", quit_button=None)

    pause_item = rumps.MenuItem("Pause", callback=lambda _: app.toggle_pause())
    remind_item = rumps.MenuItem("Remind now", callback=lambda _: app.remind_now())
    autostart_item = rumps.MenuItem(
        "Start at login", callback=lambda _: app.toggle_autostart()
    )
    interval_items = [
        rumps.MenuItem(
            f"{m} min",
            callback=(lambda m: lambda _: app.set_interval(m))(m),
        )
        for m in app.interval_choices
    ]
    quit_item = rumps.MenuItem("Quit", callback=lambda _: _quit(app))

    menubar.menu = [
        pause_item,
        remind_item,
        ("Interval", interval_items),
        autostart_item,
        None,                       # separator
        quit_item,
    ]

    def refresh():
        pause_item.title = "Resume" if app.paused else "Pause"
        autostart_item.state = 1 if is_autostart_enabled() else 0
        for item in interval_items:
            item.state = 1 if item.title == f"{app.interval_min} min" else 0

    app.on_changed = refresh
    refresh()

    # Pump Tk on the main thread so toasts animate without Tk owning the loop.
    rumps.Timer(lambda _: _pump(app), 0.02).start()

    menubar.run()


def _pump(app):
    try:
        app.root.update()
    except Exception:
        pass


def _quit(app):
    import rumps
    app.quit()
    rumps.quit_application()


def style_toast_window(win):
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    # Float above full-screen Spaces without activating/stealing focus.
    try:
        win.tk.call("::tk::unsupported::MacWindowStyle", "style",
                    win._w, "utility", "noActivates")
    except Exception:
        pass
    try:
        win.attributes("-alpha", 0.96)
    except Exception:
        pass


_PLIST_LABEL = "com.slacktime.reminder"


def _plist_path():
    return Path.home() / "Library" / "LaunchAgents" / f"{_PLIST_LABEL}.plist"


def _program_args():
    """The argv launchd should run at login."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    script = Path(__file__).resolve().parent.parent / "slacktime.py"
    return [sys.executable, str(script)]


def is_autostart_enabled():
    return _plist_path().exists()


def install_autostart():
    args_xml = "".join(f"        <string>{a}</string>\n" for a in _program_args())
    plist = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "    <key>Label</key>\n"
        f"    <string>{_PLIST_LABEL}</string>\n"
        "    <key>ProgramArguments</key>\n"
        "    <array>\n"
        f"{args_xml}"
        "    </array>\n"
        "    <key>RunAtLoad</key>\n"
        "    <true/>\n"
        "</dict>\n"
        "</plist>\n"
    )
    path = _plist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plist)


def remove_autostart():
    try:
        _plist_path().unlink()
    except FileNotFoundError:
        pass
