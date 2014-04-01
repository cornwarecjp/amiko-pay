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

import time
import sys

import amiko
import event
import network
import messages


def handleCommand(cmd):
	cmd = cmd.strip().lower()

	if cmd == "":
		return
	if cmd in ["quit", "exit"]:
		a.sendSignal(None, event.signals.quit)
		a.stop()
		sys.exit()
	elif cmd == "help":
		print """\
exit:
quit:
  Terminate application.
help:
  Display this message.
"""
	else:
		print "Unknown command. Enter \"help\" for a list of commands."


a = amiko.Amiko()
a.start()

# Give Amiko some time to initialize:
time.sleep(2.0)

print """

Amiko Pay %s Copyright (C) 2013 - %s

Amiko Pay is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Amiko Pay is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.

Enter "help" for a list of commands.
""" % (amiko.version, amiko.lastCopyrightYear)

while True:
	cmd = raw_input('> ')
	handleCommand(cmd)


