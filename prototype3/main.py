#!/usr/bin/env python
#    main.py
#    Copyright (C) 2014-2016 by CJP
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
	return str(Decimal(value) / 100000) + ' mBTC'


def choiceInput(options, prompt):
	while True:
		for i in range(len(options)):
			print '%d: %s' % (i+1, str(options[i]))

		answer = raw_input(prompt + ' (leave empty to abort): ').strip()
		if answer == '':
			raise Exception('Aborted')

		answer = int(answer) - 1
		if answer >= 0 and answer < len(options):
			return options[answer]

		print 'Answer is out of range; please try again.'


def handleCommand(cmd):

	cmd = cmd.strip() # remove whitespace

	if len(cmd) == 0:
		return

	cmd = cmd.lower()

	if cmd in ['quit', 'exit']:
		a.stop()
		crypto.cleanup()
		sys.exit()
	elif cmd == 'help':
		print '''\
exit
quit
  Terminate application.
help
  Display this message.
license
  Display licensing information.
request
  Request a payment
pay
  Pay a payment request
list
  Print a list of objects
getbalance
  Print balance information
makelink
  Make a new link
makemeetingpoint
  Make a new meeting point
deposit
  Deposit funds into a link
withdraw
  Withdraw from a channel of a link
'''
	elif cmd == 'license':
		print '''Amiko Pay is free software: you can redistribute it and/or modify
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
'''

	elif cmd == 'request':
		amount = int(raw_input('Amount (Satoshi): '))
		receipt = (raw_input('Receipt (can be empty): '))

		URL = a.request(amount, receipt)
		print 'Request URL (pass this to the payer): ', URL

	elif cmd == 'pay':
		URL = raw_input('Request URL: ').strip()

		data = a.list()
		linknames = data['links'].keys()
		class Any:
			def __str__(self):
				return "(any link)"
		linkname = choiceInput([Any()] + linknames, 'Choose a link to pay with')
		if linkname.__class__ == Any:
			amount, receipt = a.pay(URL)
		else:
			amount, receipt = a.pay(URL, linkname)

		print 'Receipt: ', repr(receipt)
		print 'Amount: (Satoshi)', amount
		answer = raw_input('Do you want to pay (y/n)? ')
		OK = answer.lower() == 'y'
		state = a.confirmPayment(OK)
		print 'Payment is ', state

	elif cmd == 'list':
		data = a.list()
		pprint.pprint(data)

	elif cmd == 'getbalance':
		balance = a.getBalance()
		keys = balance.keys()
		keys.sort()
		for k in keys:
			print k, formatBitcoinAmount(balance[k])

	elif cmd == 'makelink':
		localName = raw_input('Local name of the link: ')
		remoteURL = raw_input('Remote URL of the link (can be empty): ').strip()
		if remoteURL == '':
			localURL = a.makeLink(localName)
		else:
			localURL = a.makeLink(localName, remoteURL)

		print 'Link URL (pass this to the peer): ', localURL

	elif cmd == 'makemeetingpoint':
		meetingPointName = raw_input('Name of the meeting point: ')
		a.makeMeetingPoint(meetingPointName)

	elif cmd == 'deposit':
		data = a.list()
		linknames = data['links'].keys()
		linkname = choiceInput(linknames, 'Choose a link to deposit in')
		amount = int(raw_input('Amount (Satoshi): '))

		if raw_input('Are you sure (y/n)? ') != 'y':
			print 'Aborted'
			return

		#TODO: other channel types
		channel = iouchannel.IOUChannel.makeForOwnDeposit(amount)

		a.deposit(linkname, channel)

	elif cmd == 'withdraw':
		data = a.list()
		linknames = data['links'].keys()
		linkname = choiceInput(linknames, 'Choose a link to withdraw from')
		numChannels = len(data['links'][linkname]['channels'])
		channelID = choiceInput(range(numChannels), 'Channel index')

		if raw_input('Are you sure (y/n)? ') != 'y':
			print 'Aborted'
			return

		a.withdraw(linkname, channelID)

	else:
		print 'Unknown command. Enter \'help\' for a list of commands.'


a = node.Node()
a.start()

print '''
Amiko Pay %s Copyright (C) 2013 - %s

Enter 'help' for a list of commands. Enter 'license' for licensing information.
''' % (node.version, node.lastCopyrightYear)

while True:
	cmd = raw_input('> ')
	try:
		handleCommand(cmd)
	except Exception as e:
		print str(e)

