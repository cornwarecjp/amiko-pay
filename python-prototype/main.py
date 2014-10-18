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
import pprint
from decimal import Decimal

import amiko
import event
import network
import messages
import crypto


def formatBitcoinAmount(value):
	return str(Decimal(value) / 100000) + " mBTC"


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
		a.stop()
		crypto.cleanup()
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
pay URL [linkname]
  Pay the payment corresponding with URL
  If linkname is given, payment routing is restricted to the link with the
  given name.
list
  Print a list of objects
getbalance
  Print balance information
makelink localname [remoteURL]
  Make a new link.
  If remoteURL is given, connect to that URL.
  Prints the local link URL.
deposit linkname amount
  Deposit amount into a link
withdraw linkname channelID
  Withdraw from a channel of a link
"""
	elif cmd[0] == "request":
		checkNumArgs(1, 2)
		if len(cmd) < 3:
			cmd.append("")

		amount = int(cmd[1])
		receipt = (cmd[2])

		URL = a.request(amount, receipt)
		print URL

	elif cmd[0] == "pay":
		checkNumArgs(1, 2)

		URL = cmd[1]
		if len(cmd) < 3:
			payer = a.pay(URL)
		else:
			linkname = cmd[2]
			payer = a.pay(URL, linkname)

		print "Receipt: ", repr(payer.receipt)
		print "Amount: ", payer.amount
		answer = raw_input("Do you want to pay (y/n)? ")
		OK = answer.lower() == 'y'
		a.confirmPayment(payer, OK)
		print "Payment is ", payer.state

	elif cmd[0] == "list":
		data = a.list()
		pprint.pprint(data)

	elif cmd[0] == "getbalance":
		balance = a.getBalance()
		keys = balance.keys()
		keys.sort()
		for k in keys:
			print k, formatBitcoinAmount(balance[k])

	elif cmd[0] == "makelink":
		checkNumArgs(1, 2)

		localName = cmd[1]
		if len(cmd) < 3:
			print a.makeLink(localName)
		else:
			remoteURL = cmd[2]
			print a.makeLink(localName, remoteURL)

	elif cmd[0] == "deposit":
		checkNumArgs(2, 2)

		linkname = cmd[1]
		amount = int(cmd[2])

		if raw_input("Are you sure (y/n)? ") != 'y':
			print "Aborted"
			return

		a.deposit(linkname, amount)

	elif cmd[0] == "withdraw":
		checkNumArgs(2, 2)

		linkname = cmd[1]
		channelID = int(cmd[2])

		if raw_input("Are you sure (y/n)? ") != 'y':
			print "Aborted"
			return

		a.withdraw(linkname, channelID)

	else:
		print "Unknown command. Enter \"help\" for a list of commands."


a = amiko.Amiko()
a.start()

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

