"""Platform-specific behaviour for SlackTime.

Each supported OS provides a module exposing the same interface:

    FONT_UI      -> (family, size) tuple for the message text
    FONT_EMOJI   -> (family, size) tuple for the water-drop glyph
    style_toast_window(win)   -> apply borderless/floating/topmost styling
    install_autostart()       -> make the app launch at login
    remove_autostart()        -> undo install_autostart()
    is_autostart_enabled()    -> bool

`current()` returns the right module for the running OS.
"""

import sys


def current():
    if sys.platform == "darwin":
        from . import macos
        return macos
    from . import windows
    return windows
