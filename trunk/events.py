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

"""events.py - X events handling.

events module contain abstract base classes representing event handler, and
event object wrapper. These should be subclassed by concrete implementations
dealing with concrete X event types.

"""

import logging

from Xlib import X 

from core import Window, Geometry
import utils


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)
log.addHandler(utils.NullHandler())

_SUBSTRUCTURE = {True: X.SubstructureNotifyMask,
                 False: X.StructureNotifyMask}


class Event(object):

    """Abstract base class for X event wrappers."""

    def __init__(self, event):
        """
        event - raw X event object
        """
        self._event = event
        self.type = event.type
        self.window_id = event.window.id

    @property
    def window(self):
        """Return window, which is the source of the event."""
        return Window(self.window_id)


class EventHandler(object):

    """Abstract base class for event handlers."""

    def __init__(self, masks, mapping):
        """
        mask - X.EventMask
        mapping - dict of X.EventTypes and associated functions
        """
        self.masks = masks
        self.__mapping = mapping

    @property
    def types(self):
        return self.__mapping.keys()

    def handle_event(self, event):
        """Wrap raw X event into _EVENT_TYPE (Event object) and call _METHOD."""
        event_type, handler_method = self.__mapping[event.type]
        event = event_type(event)
        handler_method(event)


class KeyEvent(Event):

    """Class representing X.KeyPress and X.KeyRelease events.
    
    This event is generated if grabbed key is pressed.
    
    """

    # List of Modifiers we are interested in
    __KEY_MODIFIERS = (X.ShiftMask, X.ControlMask, X.Mod1Mask, X.Mod4Mask)

    def __init__(self, event):
        Event.__init__(self, event)
        self.modifiers, self.keycode = self.__get_modifiers_keycode(event)

    def __get_modifiers_keycode(self, event):
        """Return modifiers mask and keycode of this event."""
        keycode = event.detail
        state = event.state
        modifiers = 0
        for modifier in self.__KEY_MODIFIERS:
            if state & modifier:
                modifiers = modifiers | modifier
        return (modifiers or X.AnyModifier, keycode)


class KeyHandler(EventHandler):
    
    """Handler for X.KeyPress events."""

    def __init__(self, key_press=None, key_release=None,
                 keys=[], numlock=0, capslock=0):
        """
        key_press - function that will handle events 
        keys - list of (mask, keycode) pairs
        numlock - state of NumLock key (0 - OFF, 1 - ON, 2 - IGNORE)
        capslock - state of CapsLock key
        """
        EventHandler.__init__(self, [X.KeyPressMask, X.KeyReleaseMask], 
                              {X.KeyPress: (KeyEvent, self.key_press),
                               X.KeyRelease: (KeyEvent, self.key_release)})
        self.__key_press = key_press
        self.__key_release = key_release
        self.keys = keys
        self.numlock = numlock
        self.capslock = capslock

    def key_press(self, event):
        if self.__key_press:
            self.__key_press(event)

    def key_release(self, event):
        if self.__key_release:
            self.__key_release(event)

    def set_keys(self, keys, numlock, capslock):
        """Set new keys list."""
        self.keys = keys
        self.numlock = numlock
        self.capslock = capslock

    def grab_keys(self, window):
        """Grab keys and start listening to window's events."""
        for mask, code in self.keys:
            window.grab_key(mask, code, self.numlock, self.capslock)
        window.listen(self)

    def ungrab_keys(self, window):
        """Ungrab keys and stop listening to window's events."""
        for mask, code in self.keys:
            window.ungrab_key(mask, code, self.numlock, self.capslock)
        window.unlisten(self)


class DestroyNotifyEvent(Event):

    """Class representing X.DestroyNotify events.
    
    This event is generated when a window is destroyed.
    
    """

    def __init__(self, event):
        Event.__init__(self, event)


class DestroyNotifyHandler(EventHandler):

    """Handler for X.DestroyNotify events."""

    def __init__(self, destroy=None, children=False):
        """
        destroy - function that will handle events
        children - False - listen for children windows' events
                   True - listen for window's events
        """
        EventHandler.__init__(self, [_SUBSTRUCTURE[children]],
                              {X.DestroyNotify: (DestroyNotifyEvent, 
                                                 self.destroy)})
        self.__destroy = destroy

    def destroy(self, event):
        if self.__destroy:
            self.__destroy(event)


class CreateNotifyEvent(Event):

    """Class representing X.CreateNotify events.
    
    This event is generated when a window is created.
    
    """

    def __init__(self, event):
        Event.__init__(self, event)
        self.parent_id = event.parent.id
        self.border_width = event.border_width
        self.override = event.override

    @property
    def parent(self):
        return Window(self.parent_id)

    @ property
    def geometry(self):
        return Geometry(self._event.x, self._event.y,
                        self._event.width, self._event.height)


class CreateNotifyHandler(EventHandler):

    """Handler for X.CreateNotify events.
    
    WARNING! event.window might be destroyed just after creation, 
    that's why only events with override=False are handled, 
    but still you can't be sure if event.window still exists...
    
    """

    def __init__(self, create=None):
        """
        create - function that will handle events
        """
        EventHandler.__init__(self, [X.SubstructureNotifyMask],
                              {X.CreateNotify: (CreateNotifyEvent, 
                                                self.create)})
        self.__create = create

    def create(self, event):
        if not event.override and self.__create:
            self.__create(event)


class PropertyNotifyEvent(Event):

    """Class representing X.PropertyNotify events.
    
    This event is generated when property of the window is changed.
    
    """

    NEW_VALUE = X.PropertyNewValue
    DELETED = X.PropertyDelete

    def __init__(self, event):
        Event.__init__(self, event)
        self.atom = event.atom
        self.state = event.state

    @property
    def atom_name(self):
        """Return event's atom name."""
        return Window.atom_name(self.atom)


class PropertyNotifyHandler(EventHandler):

    """Hanlder for X.PropertyNotify events."""

    def __init__(self, property=None):
        """
        property - function that will handle events
        """
        EventHandler.__init__(self, [X.PropertyChangeMask], 
                              {X.PropertyNotify: (PropertyNotifyEvent, 
                                                  self.property)})
        self.__property = property

    def property(self, event):
        if self.__property:
            self.__property(event)


class ConfigureNotifyEvent(Event):

    def __init__(self, event):
        Event.__init__(self, event)
        self.parent_id = event.parent.id
        self.border_width = event.border_width
        self.override = event.override

    @property
    def parent(self):
        return Window(self.parent_id)

    @ property
    def geometry(self):
        return Geometry(self._event.x, self._event.y,
                        self._event.width, self._event.height)


class ConfigureNotifyHandler(EventHandler):

    """Hanlder for X.ConfigureNotify events."""

    def __init__(self, configure=None, children=False):
        """
        configure - function that will handle events
        children - False - listen for children windows' events
                   True - listen for window's events
        """
        EventHandler.__init__(self, [_SUBSTRUCTURE[children]], 
                              {X.PropertyNotify: (ConfigureNotifyEvent, 
                                                  self.configure)})
        self.__configure = configure

    def configure(self, event):
        if self.__configure:
            # TODO: filter out event.override=True?
            self.__configure(event)


