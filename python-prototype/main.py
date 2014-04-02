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

	cmd = cmd.split() # split according to whitespace

	if len(cmd) == 0:
		return

	cmd[0] = cmd[0].lower()

	def checkNumArgs(mina, maxa):
		if len(cmd)-1 < mina:
			raise Exception("Not enough arguments")
		if len(cmd)-1 > maxa:
			raise Exception("Too many arguments")

	if cmd[0] in ["quit", "exit"]:
		checkNumArgs(0, 0)
		a.sendSignal(None, event.signals.quit)
		a.stop()
		sys.exit()
	elif cmd[0] == "help":
		checkNumArgs(0, 0)
		print """\
exit:
quit:
  Terminate application.
help:
  Display this message.
request amount [receipt]:
  Request payment of amount, with optional receipt
"""
	elif cmd[0] == "request":
		checkNumArgs(1, 2)
		if len(cmd) < 3:
			cmd.append("")

		amount = int(cmd[1])
		receipt = (cmd[2])

		URL = a.request(amount, receipt)
		print URL

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
	try:
		handleCommand(cmd)
	except Exception as e:
		print str(e)

