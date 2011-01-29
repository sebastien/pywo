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

"""actions - core PyWO actions classes and functions."""

import logging
import os.path
import sys

from pywo.core import Window, WindowManager, Type, State, Mode
from pywo import filters


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

WM = WindowManager()

TYPE_FILTER = filters.ExcludeType(desktop=True, dock=True, splash=True)
STATE_FILTER = filters.ExcludeState(fullscreen=True, maximized=True)
TYPE_STATE_FILTER = filters.AND(TYPE_FILTER, STATE_FILTER)


class ActionException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Action(object):

    """PyWO Action."""

    __ACTIONS = {} # {action.name: action, }
    _LOADED = False # TODO: remove?

    def __init__(self, action, name='',
                 filter=None, unshade=False):
        self.name = name or action.__name__
        self.__doc__ = action.__doc__
        self.__action = action
        self.__filter = filter
        self.__unshade = unshade
        self.post_action_hooks = []
        self.args = action.func_code.co_varnames[1:action.func_code.co_argcount]
        if action.func_defaults:
            self.obligatory_args = self.args[:-len(action.func_defaults)]
        else:
            self.obligatory_args = self.args
        self.optional_args = [arg for arg in self.args 
                                  if arg not in self.obligatory_args]

    def __call__(self, win, **kwargs):
        self.perform(win, **kwargs)

    def perform(self, win, **kwargs):
        """Perform action on window and with given arguments."""
        if self.__filter and not self.__filter(win):
            error = "Can't perform %s on this window." % self.name
            raise ActionException(error)
        if self.__unshade:
            win.shade(Mode.UNSET)
            win.flush()
        self.__action(win, **kwargs)
        win.flush()
        for hook in self.post_action_hooks:
            hook(self, win, **kwargs)

    def register(self):
        if self.name in Action.__ACTIONS:
            log.warning('Action with name %s already registered!' % self.name)
        Action.__ACTIONS[self.name] = self
        log.debug('Registered action %s' % self.name)

    @classmethod
    def get(cls, name):
        """Return action with given name or None."""
        return cls.__ACTIONS.get(name, None)

    @classmethod
    def all(cls):
        """Return set of all actions."""
        return cls.__ACTIONS.values()


def register(name, filter=None, unshade=False):
    """Register function as PyWO action with given name."""
    def register_action(action):
        action = Action(action, name, filter, unshade)
        action.register()
        return action
    name = name.lower()
    return register_action


def post_action_hook(hook):
    """Register post_action_hook that will be called after performing action."""
    Action.post_action_hooks.append(hook)
    return hook


@register(name='debug', filter=TYPE_FILTER)
def _debug_info(win):
    """Print debug info about Window Manager, and current Window."""
    log.info('-= Window Manager =-')
    WindowManager().debug_info(log)
    log.info('-= Current Window =-')
    win.debug_info(log)
    log.info('-= Move with same geometry =-')
    geo =  win.geometry
    win.set_geometry(geo)
    win.sync()
    log.info('New geometry=%s' % win.geometry)
    log.info('-= End of debug =-')


def __load():
    """Autodiscover actions."""
    # TODO: use pkg_resources and pywo.actions entry point
    path = os.path.dirname(os.path.abspath(__file__))
    modules = [file[0:-3] for file in os.listdir(path) 
                          if file.endswith('.py')]
    for module in modules:
        __import__('pywo.actions.%s' % module)
    Action._LOADED = True


def get(name):
    """Return action with given name."""
    if not Action._LOADED:
        __load()
    return Action.get(name.lower())


def all():
    """Return set of all actions."""
    if not Action._LOADED:
        __load()
    return Action.all()


def get_args(action, config, section=None, options=None):
    # TODO: move to Action class?
    kwargs = {}
    for arg in action.args:
        for obj in [options, section, config]:
            value = getattr(obj, arg, None)
            if value is not None:
                kwargs[arg] = value
                break
    return kwargs


# TODO: move to commandline.py as perform_action?
def perform(args, config, options={}, win_id=0):
    if not options.action and len(args) == 0:
        raise ActionException('No ACTION provided')
    name = options.action or args.pop(0)
    action = get(name)
    if not action:
        raise ActionException('Invalid ACTION name: %s' % name)
    need_section = 'direction' in action.args or \
                   'position' in action.args or \
                   'gravity' in action.args
    if need_section and options.section:
        name = options.section #or args.pop(0)
        section = config.section(name)
        if not section:
            raise ActionException('Invalid SECTION name: %s' % name)
    else:
        section = None

    missing_args = []
    for arg in action.obligatory_args:
        if not getattr(options, arg):
            missing_args.append(arg.upper())
    if need_section and not section and missing_args:
        raise ActionException('Missing %s' % ', '.join(missing_args))

    if win_id or options.win_id:
        # TODO: try/except invalid options.win_id, or non existant Window
        window = Window(win_id or int(options.win_id, 0))
    elif args:
        # TODO: check system encoding?
        args = [arg.decode('utf-8') for arg in args]
        match = u' '.join(args)
        windows = WM.windows(filters.NORMAL_TYPE, match=match)
        try:
            window = windows[0]
        except:
            raise ActionException('No WINDOW matching name: %s' % match)
    else:
        window = WM.active_window()

    kwargs = get_args(action, config, section, options)
    log.debug('%s(%s)' % 
              (action.name, 
              ', '.join(['%s=%s' % (key, str(value)) 
                         for key, value in kwargs.items()])))
    action(window, **kwargs)

