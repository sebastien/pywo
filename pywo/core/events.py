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

"""X events handling.

`events` module contains abstract base classes representing event handler, and
event object wrapper. These should be subclassed by concrete implementations
dealing with concrete X event types.

"""

import logging

from Xlib import X 

from pywo.core.basic import Geometry
from pywo.core.windows import Window


__author__ = "Wojciech 'KosciaK' Pietrzok"


log = logging.getLogger(__name__)

_SUBSTRUCTURE = [X.StructureNotifyMask, X.SubstructureNotifyMask]


class Event(object):

    """Abstract base class for raw X event wrappers."""

    def __init__(self, event):
        """
        `event` 
            is raw X event object
        """
        self._event = event
        self.type = event.type
        self.window_id = event.window.id

    @property
    def window(self):
        """Return :class:`~pywo.core.windows.Window`, 
        which is the source of the event."""
        return Window(self.window_id)

    def __str__(self):
        return '<%s type=%s, window_id=%s>' % \
               (self.__class__.__name__, self.type, self.window_id)


class EventHandler(object):

    """Abstract base class for event handlers."""

    def __init__(self, masks, mapping):
        """
        `mask`
            `X.EventMask`
        `mapping`
            dict of `X.EventType` and associated functions or methods
        """
        self.masks = masks
        self.__mapping = mapping

    @property
    def types(self):
        """Return set of `EventHandler`'s event types."""
        return self.__mapping.keys()

    def handle_event(self, event):
        """Wrap raw X event into :class:`Event` and call handler method."""
        event_type, handler_method = self.__mapping[event.type]
        event = event_type(event)
        handler_method(event)
    
    def __str__(self):
        return '<%s masks=%s, types=%s>' % \
               (self.__class__.__name__, self.masks, self.types)


class KeyEvent(Event):

    """Class representing `X.KeyPress` and `X.KeyRelease` events.
    
    This event is generated if grabbed key is pressed.
    
    """

    # List of Modifiers we are interested in
    __KEY_MODIFIERS = (X.ShiftMask, X.ControlMask, X.Mod1Mask, X.Mod4Mask)

    def __init__(self, event):
        Event.__init__(self, event)
        self.modifiers, self.keycode = self.__get_modifiers_keycode(event)

    def __get_modifiers_keycode(self, event):
        """Return modifiers mask and keycode of this."""
        keycode = event.detail
        state = event.state
        modifiers = 0
        for modifier in self.__KEY_MODIFIERS:
            if state & modifier:
                modifiers = modifiers | modifier
        return (modifiers or X.AnyModifier, keycode)

    def __str__(self):
        return '<%s type=%s, window_id=%s keycode=%s, modifiers=%s>' % \
               (self.__class__.__name__, self.type, self.window_id,
                self.keycode, self.modifiers)


class KeyHandler(EventHandler):
    
    """Handler for `X.KeyPress` events."""

    def __init__(self, key_press=None, key_release=None,
                 keys=None, numlock=0, capslock=0):
        """
        `key_press`
            function that will handle events 
        `keys`
            list of (mask, keycode) pairs
        `numlock`
            state of NumLock key (0 - OFF, 1 - ON, 2 - IGNORE)
        `capslock`
            state of CapsLock key
        """
        EventHandler.__init__(self, [X.KeyPressMask, X.KeyReleaseMask], 
                              {X.KeyPress: (KeyEvent, self.key_press),
                               X.KeyRelease: (KeyEvent, self.key_release)})
        self.__key_press = key_press
        self.__key_release = key_release
        self.keys = keys or []
        self.numlock = numlock
        self.capslock = capslock

    def key_press(self, event):
        """Handle :class:`KeyEvent` generated by `X.KeyPress`."""
        #if self.key_press:
        if self.__key_press and \
           (event.modifiers, event.keycode) in self.keys:
            self.__key_press(event)

    def key_release(self, event):
        """Handle :class:`KeyEvent` generated by `X.KeyRelease`."""
        #if self.__key_release:
        if self.__key_release and \
           (event.modifiers, event.keycode) in self.keys:
            self.__key_release(event)

    def grab_keys(self, window):
        """Grab keys and start listening to window's events."""
        for mask, code in self.keys:
            window.grab_key(mask, code, self.numlock, self.capslock)
        window.register(self)

    def ungrab_keys(self, window):
        """Ungrab keys and stop listening to window's events."""
        for mask, code in self.keys:
            window.ungrab_key(mask, code, self.numlock, self.capslock)
        window.unregister(self)


class FocusEvent(Event):

    """Class representing `X.FocusIn` and `X.FocusOut` events.
    
    This event is generated when focus input changes.
    
    """

    def __init__(self, event):
        Event.__init__(self, event)
        self.mode = event.mode
        self.detail = event.detail

    def __str__(self):
        return '<%s type=%s, window_id=%s mode=%s, detail=%s>' % \
               (self.__class__.__name__, self.type, self.window_id,
                self.mode, self.detail)


class FocusHandler(EventHandler):

    """Handler for `X.FocusIn` and `X.FocusOut` events."""

    def __init__(self, focus_in=None, focus_out=None):
        EventHandler.__init__(self, [X.FocusChangeMask],
                              {X.FocusIn: (FocusEvent, self.focus_in),
                               X.FocusOut: (FocusEvent, self.focus_out)})
        self.__focus_in = focus_in
        self.__focus_out = focus_out

    def focus_in(self, event):
        """Handle :class:`FocusEvent` generated by `X.FocusIn`."""
        if self.__focus_in:
            self.__focus_in(event)

    def focus_out(self, event):
        """Handle :class:`FocusEvent` generated by `X.FocusOut`."""
        if self.__focus_out:
            self.__focus_out(event)


class DestroyNotifyEvent(Event):

    """Class representing `X.DestroyNotify` events.
    
    This event is generated when a window is destroyed.
    
    """

    def __init__(self, event):
        Event.__init__(self, event)


class DestroyNotifyHandler(EventHandler):

    """Handler for `X.DestroyNotify` events."""

    def __init__(self, destroy=None, children=False):
        """
        `destroy`
            function that will handle events
        `children`
            ``False`` - listen for children windows' events
            ``True`` - listen for window's events
        """
        EventHandler.__init__(self, [_SUBSTRUCTURE[bool(children)]],
                              {X.DestroyNotify: (DestroyNotifyEvent, 
                                                 self.destroy)})
        self.__destroy = destroy

    def destroy(self, event):
        """Handle :class:`DestroyNotifyEvent` generated by `X.DestroyNotify`."""
        if self.__destroy:
            self.__destroy(event)


class CreateNotifyEvent(Event):

    """Class representing `X.CreateNotify` events.
    
    This event is generated when a window is created.
    
    """

    def __init__(self, event):
        Event.__init__(self, event)
        self.parent_id = event.parent.id
        self.border_width = event.border_width
        self.override = event.override

    @property
    def parent(self):
        """Parent of newly created window."""
        return Window(self.parent_id)

    @ property
    def geometry(self):
        """Geoemtry of newly created window."""
        return Geometry(self._event.x, self._event.y,
                        self._event.width, self._event.height)


class CreateNotifyHandler(EventHandler):

    """Handler for `X.CreateNotify` events.
    
    .. warning::
      :attr:`window` might be destroyed just after creation, 
      that's why only events with ``override=False`` are handled, 
      but still you can't be sure if event.window still exists...
    
    """

    def __init__(self, create=None):
        """
        `create`
            function that will handle events
        """
        EventHandler.__init__(self, [X.SubstructureNotifyMask],
                              {X.CreateNotify: (CreateNotifyEvent, 
                                                self.create)})
        self.__create = create

    def create(self, event):
        """Handle :class:`CreateNotifyEvent` generated by `X.CreateNotify`."""
        if not event.override and self.__create:
            self.__create(event)


class PropertyNotifyEvent(Event):

    """Class representing `X.PropertyNotify` events.
    
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

    """Hanlder for `X.PropertyNotify` events."""

    def __init__(self, property=None):
        """
        `property`
            function that will handle events
        """
        EventHandler.__init__(self, [X.PropertyChangeMask], 
                              {X.PropertyNotify: (PropertyNotifyEvent, 
                                                  self.property)})
        self.__property = property

    def property(self, event):
        """Handle :class:`PropertyNotifyEvent` generated by `X.PropertyNotify`."""
        if self.__property:
            self.__property(event)


class ConfigureNotifyEvent(Event):

    """Class representing `X.ConfigureNotify` events.

    This event is generated when geometry of the window is changed.

    """

    def __init__(self, event):
        Event.__init__(self, event)
        self.border_width = event.border_width
        self.override = event.override

    @ property
    def geometry(self):
        """New :class:`~pywo.core.basic.Geometry` of the window."""
        return Geometry(self._event.x, self._event.y,
                        self._event.width, self._event.height)


class ConfigureNotifyHandler(EventHandler):

    """Hanlder for `X.ConfigureNotify` events."""

    def __init__(self, configure=None, children=False):
        """
        `configure`
            function that will handle events
        `children`
            ``False`` - listen for children windows' events,
            ``True`` - listen for window's events
        """
        EventHandler.__init__(self, [_SUBSTRUCTURE[bool(children)]], 
                              {X.ConfigureNotify: (ConfigureNotifyEvent, 
                                                   self.configure)})
        self.__configure = configure

    def configure(self, event):
        """Handle :class:`ConfigureNotifyEvent` generated by `X.ConfigureNotify`."""
        if self.__configure:
            # TODO: filter out event.override=True?
            self.__configure(event)


