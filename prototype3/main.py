#!/usr/bin/env python
#    main.py
#    Copyright (C) 2014-2015 by CJP
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
#
#    Additional permission under GNU GPL version 3 section 7
#
#    If you modify this Program, or any covered work, by linking or combining it
#    with the OpenSSL library (or a modified version of that library),
#    containing parts covered by the terms of the OpenSSL License and the SSLeay
#    License, the licensors of this Program grant you additional permission to
#    convey the resulting work. Corresponding Source for a non-source form of
#    such a combination shall include the source code for the parts of the
#    OpenSSL library used as well as that of the covered work.

import time
import sys
import pprint
from decimal import Decimal

from amiko.utils import crypto
from amiko.channels import iouchannel
from amiko import node



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
license:
  Display licensing information.
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
	elif cmd[0] == "license":
		print """Amiko Pay is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Amiko Pay is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.

Additional permission under GNU GPL version 3 section 7

If you modify this Program, or any covered work, by linking or combining it with
the OpenSSL library (or a modified version of that library), containing parts
covered by the terms of the OpenSSL License and the SSLeay License, the
licensors of this Program grant you additional permission to convey the
resulting work. Corresponding Source for a non-source form of such a combination
shall include the source code for the parts of the OpenSSL library used as well
as that of the covered work.

================================================================================

Amiko Pay uses and contains a copy of the Python-BitcoinRPC library.

Python-BitcoinRPC is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or
(at your option) any later version.

This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this software; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
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
			amount, receipt = a.pay(URL)
		else:
			linkname = cmd[2]
			amount, receipt = a.pay(URL, linkname)

		print "Receipt: ", repr(receipt)
		print "Amount: ", amount
		answer = raw_input("Do you want to pay (y/n)? ")
		OK = answer.lower() == 'y'
		state = a.confirmPayment(OK)
		print "Payment is ", state

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

		channel = iouchannel.IOUChannel.makeForOwnDeposit(a.getUIDContext(), amount)

		a.deposit(linkname, channel)

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


a = node.Node()
a.start()

print """
Amiko Pay %s Copyright (C) 2013 - %s

Enter "help" for a list of commands. Enter "license" for licensing information.
""" % (node.version, node.lastCopyrightYear)

while True:
	cmd = raw_input('> ')
	try:
		handleCommand(cmd)
	except Exception as e:
		print str(e)

