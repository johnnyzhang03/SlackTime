"""macOS-specific behaviour for SlackTime.

UNTESTED on real hardware — written against the documented macOS / Tk / launchd
behaviour. Expect to tune the toast styling and the LaunchAgent once you can run
it on a Mac. The interface matches platform_support.windows so slacktime.py
needs no changes.
"""

import sys
from pathlib import Path

# macOS ships these system fonts; "Apple Color Emoji" renders the water drop.
FONT_UI = ("Helvetica Neue", 13)
FONT_EMOJI = ("Apple Color Emoji", 22)


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
