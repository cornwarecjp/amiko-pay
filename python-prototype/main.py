#!/usr/bin/env python
#    main.py
#    Copyright (C) 2014 by CJP
#
#    This file is part of Amiko Pay.
#
#    Amiko Pay is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Amiko Pay is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.

import amiko
from network import Listener, Connection

context = amiko.Context()

listener = Listener(context, 4321)

connection = Connection(context, ('localhost', 4321))

connection.send("hello")

context.dispatchNetworkEvents()
context.dispatchNetworkEvents()

context.sendSignal(amiko.signals.quit)

