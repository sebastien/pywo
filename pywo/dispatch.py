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

"""dispatch.py - dispatch events generated by X Server."""


import logging
import threading
import time


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)


class EventDispatcher(object):

    """Checks the event queue and dispatches events to correct handlers.

    EventDispatcher will run in separate thread.
    The self.__handlers attribute holds all registered EventHnadlers,
    it has structure as follows:
    self.__handlers = {win_id: {event_type: handler}} 
    That's why there can be only one handler per window/event_type.

    """

    def __init__(self, display):
        # What about integration with gobject?
        # gobject.io_add_watch(root.display, gobject.IO_IN, handle_xevent)
        self.__display = display
        self.__root = display.screen().root
        self.__handlers = {} # {window.id: {handler.type: [handler, ], }, }
        # TODO: {event.type: {window.id: set([hander, ], ...}, ...}
        self.__thread = None

    def run(self):
        """Perform event queue checking.

        Every 50ms check event queue for pending events and dispatch them.
        If there's no registered handlers stop running.

        """
        log.debug('EventDispatcher started')
        while self.__handlers:
            while self.__display.pending_events():
                # Dispatch all pending events if present
                self.__dispatch(self.__display.next_event())
            time.sleep(0.05)
        log.debug('EventDispatcher stopped')

    def __get_masks(self, window_id):
        """Return event type masks for given window."""
        masks = set()
        for type_handlers in self.__handlers.get(window_id, {}).values():
            for handler in type_handlers:
                masks.update(handler.masks)
        return masks

    def register(self, window, handler):
        """Register event handler and return new window's event mask."""
        log.debug('Registering %s for %s' % (handler, window))
        window_handlers = self.__handlers.setdefault(window.id, {})
        for type in handler.types:
            type_handlers = window_handlers.setdefault(type, [])
            type_handlers.append(handler)
        if not self.__thread or \
           (self.__thread and not self.__thread.isAlive()):
            # start new thread only if needed
            self.__thread = threading.Thread(name='EventDispatcher', 
                                 target=self.run)
            self.__thread.start()
        return self.__get_masks(window.id)

    def unregister(self, window=None, handler=None):
        """Unregister event handler and return new window's event mask.
        
        If window is None all handlers for all windows will be unregistered.
        If handler is None all handlers for this window will be unregistered.
        
        """
        if not window:
            log.debug('Unregistering all handlers for all windows')
            self.__handlers.clear()
            return []
        if not window.id in self.__handlers:
            log.error('No handlers registered for %s' % window)
        elif not handler and window.id in self.__handlers:
            log.debug('Unregistering all handlers for %s' % (window,))
            del self.__handlers[window.id]
        elif window.id in self.__handlers:
            log.debug('Unregistering %s for %s' % (handler, window))
            window_handlers = self.__handlers[window.id]
            for type in handler.types:
                type_handlers = window_handlers.setdefault(type, [])
                if handler in type_handlers:
                    type_handlers.remove(handler)
                if not type_handlers:
                    del window_handlers[type]
        if not self.__handlers.setdefault(window.id, {}):
            del self.__handlers[window.id]
        return self.__get_masks(window.id)

    def __dispatch(self, event):
        """Dispatch raw X event to correct handler."""
        if hasattr(event, 'window') and \
           event.window.id in self.__handlers:
            # Try window the event is reported on (if present)
            handlers = self.__handlers[event.window.id]
        elif hasattr(event, 'event') and \
             event.event.id in self.__handlers:
            # Try window the event is reported for (if present)
            handlers = self.__handlers[event.event.id]
        elif self.__root.id in self.__handlers:
            # Try root window
            handlers = self.__handlers[self.__root.id]
        else:
            log.error('No handler for this event %s' % event)
            return
        if not event.type in handlers:
            # Just skip unwanted events types
            return
        for handler in handlers[event.type]:
            handler.handle_event(event)

