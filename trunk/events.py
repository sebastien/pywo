#
# Copyright 2010, Wojciech 'KosciaK' Pietrzok
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""events.py module encapsulate all X events handling.

events module contain abstract base classes representing event handler, and
event object wrapper. These should be subclassed by concrete implementations
dealing with concrete X event types.

Right now only handlers and wrappers for X.KeyPress events are provided.

"""

import logging

from Xlib import X 

from core import Window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


class Event(object):

    """Abstract base class for X event wrappers."""

    def __init__(self, event):
        """
        event - raw X event object
        """
        self.__event = event
        self.type = event.type

    @property
    def window_id(self):
        """Return id of the window, which is the source of the event."""
        return self.__event.window.id

    @property
    def window(self):
        """Return window, which is the source of the event."""
        return Window(self.window_id)


class EventHandler(object):

    """Abstract base class for event handlers."""

    def __init__(self, mask, types):
        """
        mask - X.EventMask
        types - list of X.EventTypes using given mask
        """
        self.mask = mask
        self.types = types

    def handle_event(self, event):
        """Handle raw X event. 
        
        This method is called by EventDispatcher, sending raw X event, which
        should be wrapped into correct Event object and handled.

        """
        raise NotImplementesError


class KeyEvent(Event):

    """Class representing X.KeyPress and X.KeyRelease events."""

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


class KeyPressEventHandler(EventHandler):
    
    """Handler for X.KeyPress events."""

    def __init__(self, keys, numlock, handler_method=None):
        """
        keys - list of (mask, keycode) pairs
        numlock - state of NumLock key (0 - OFF, 1 - OFF, 2 - IGNORE)
        handler_method - method that will handle events 
                         (if key_press is not overriden by subclass)
        """
        EventHandler.__init__(self, X.KeyPressMask, [X.KeyPress])
        self.handler_method = handler_method
        self.keys = keys
        self.numlock = numlock

    def grab_keys(self, window):
        """Grab keys and start listening to window's events."""
        for mask, code in self.keys:
            window.grab_key(mask, code, self.numlock)
        window.listen(self)

    def ungrab_keys(self, window):
        """Ungrab keys and stop listening to window's events."""
        for mask, code in self.keys:
            window.ungrab_key(mask, code, self.numlock)
        window.unlisten(self)

    def handle_event(self, event):
        """Wrap raw X event into KeyEvent and delegate to handler method."""
        event = KeyEvent(event)
        self.key_press(event)

    def key_press(self, event):
        """Handle key press event or delegate to handler method.
        
        This method should be overriden by subclasses.
        
        """
        if self.handler_method:
            self.handler_method(event)


