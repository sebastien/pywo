#
# PyWO - Python Window Organizer
# Copyright 2010, Wojciech 'KosciaK' Pietrzok
#
# This file is part of PyWO.
#
# PyWO is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyWO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyWO.  If not, see <http://www.gnu.org/licenses/>.
#

"""state.py - PyWO actions - changing windows state."""

from actions import register, TYPE, STATE
from core import Window, WM


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


@register(name='maximize', check=[TYPE], unshade=True)
def _maximize(win, mode=Window.MODE_TOGGLE):
    """Maximize window."""
    state = win.state
    if mode == Window.MODE_TOGGLE and \
       Window.STATE_MAXIMIZED_HORZ in state and \
       Window.STATE_MAXIMIZED_VERT in state:
        mode = Window.MODE_UNSET
    elif mode == Window.MODE_TOGGLE:
        mode = Window.MODE_SET
    if Window.STATE_FULLSCREEN in state:
        win.fullscreen(win.MODE_UNSET)
    win.maximize(mode)

@register(name='maximize_vert', check=[TYPE], unshade=True)
def _maximize(win, mode=Window.MODE_TOGGLE):
    """Maximize vertically window."""
    win.fullscreen(win.MODE_UNSET)
    win.maximize(mode, horz=False)

@register(name='maximize_horz', check=[TYPE], unshade=True)
def _maximize(win, mode=Window.MODE_TOGGLE):
    """Maximize vertically window."""
    win.fullscreen(win.MODE_UNSET)
    win.maximize(mode, vert=False)


@register(name='shade', check=[TYPE])
def _shade(win, mode=Window.MODE_TOGGLE):
    """Shade window."""
    #win.maximize(win.MODE_UNSET)
    win.fullscreen(win.MODE_UNSET)
    win.shade(mode)


@register(name='fullscreen', check=[TYPE], unshade=True)
def _fullscreen(win, mode=Window.MODE_TOGGLE):
    """Fullscreen window."""
    #win.maximize(win.MODE_UNSET)
    win.fullscreen(mode)


@register(name='sticky', check=[TYPE])
def _sticky(win, mode=Window.MODE_TOGGLE):
    """Change sticky (stay on all desktops/viewports) property."""
    win.sticky(mode)


@register(name='activate', check=[TYPE], unshade=True)
def _activate(win, mode=Window.MODE_TOGGLE):
    """Activate window.
    
    Unshade, unminimize and switch to it's desktop/viewport.
    
    """
    desktop = win.desktop
    if desktop != WM.desktop:
        WM.set_desktop(desktop)
    win.activate()


@register(name="close", check=[TYPE])
def _close(win):
    """Close window."""
    win.close()


@register(name='blink', check=[TYPE, STATE])
def _blink(win):
    """Blink window (show border around window)."""
    win.blink()

