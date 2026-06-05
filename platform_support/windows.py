"""Windows-specific behaviour for SlackTime."""

import os
import subprocess
from pathlib import Path

FONT_UI = ("Segoe UI", 12)
FONT_EMOJI = ("Segoe UI Emoji", 22)


def style_toast_window(win):
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    try:
        win.attributes("-alpha", 0.96)
    except Exception:
        pass


def _startup_shortcut_path():
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / \
        "Programs" / "Startup" / "SlackTime.lnk"


def _launch_target():
    """The command Windows should run at login.

    When frozen by PyInstaller this is the .exe; otherwise it's
    `pythonw slacktime.py` so no console window appears.
    """
    import sys
    if getattr(sys, "frozen", False):
        return sys.executable, ""
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    runner = pythonw if pythonw.exists() else Path(sys.executable)
    script = Path(__file__).resolve().parent.parent / "slacktime.py"
    return str(runner), f'"{script}"'


def is_autostart_enabled():
    return _startup_shortcut_path().exists()


def install_autostart():
    target, args = _launch_target()
    lnk = _startup_shortcut_path()
    workdir = str(Path(target).parent)
    ps = (
        "$w=New-Object -ComObject WScript.Shell;"
        f"$l=$w.CreateShortcut('{lnk}');"
        f"$l.TargetPath='{target}';"
        f"$l.Arguments='{args}';"
        f"$l.WorkingDirectory='{workdir}';"
        "$l.Description='SlackTime - water and stretch reminder';"
        "$l.Save()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   check=False, capture_output=True)


def remove_autostart():
    lnk = _startup_shortcut_path()
    try:
        lnk.unlink()
    except FileNotFoundError:
        pass
