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

"""services - package containing services

All services must provide three functions:
setup(config) - setup service using provided Config instance;
start() - start service. New thread should be started, and main loop provided;
stop() - stop service. All EventHandlers should be unregistered, thread stopped.

"""

import logging


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

