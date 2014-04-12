#!/usr/bin/env python
#    twonodes.py
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

import sys
import time

sys.path.append("..")

import amiko

node1 = amiko.Amiko(conffile="twonodes_1.conf")
node1.start()
node2 = amiko.Amiko(conffile="twonodes_2.conf")
node2.start()

#Allow finlinks to link
time.sleep(3)

print "Node 1:"
print node1.list()

print "Node 2:"
print node2.list()

node1.stop()
node2.stop()


