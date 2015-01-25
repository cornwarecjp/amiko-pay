#!/usr/bin/env python
#    twonodes.py
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
import pprint

import testenvironment

import amiko
import event
import settings

settings1 = settings.Settings()
settings1.RPCURL = "dummy"
settings1.listenHost = "localhost"
settings1.listenPort = 4322
settings1.advertizedHost = settings1.listenHost
settings1.advertizedPort = settings1.listenPort
settings1.stateFile = "twonodes_1.dat"
settings1.payLogFile = "payments1.log"
with open(settings1.stateFile, "wb") as f:
	f.write("""
		{
		"links":
		[
			{
			"name": "node1",
			"localID": "node1",
			"remoteID": "node2",
			"remoteURL": "amikolink://localhost:4323/node2",
			"channels":
			[{
				"ID": 0,
				"amountLocal"           : 1000,
				"amountRemote"          : 1000,
				"transactionsIncomingReserved": {},
				"transactionsOutgoingReserved": {},
				"transactionsIncomingLocked"  : {},
				"transactionsOutgoingLocked"  : {},
				"type": "plain"
			}]
			}
		],

		"meetingPoints": [],

		"payees": []
		}
		""")
node1 = amiko.Amiko(settings1)
node1.start()

settings2 = settings.Settings()
settings2.RPCURL = "dummy"
settings2.listenHost = "localhost"
settings2.listenPort = 4323
settings2.advertizedHost = settings2.listenHost
settings2.advertizedPort = settings2.listenPort
settings2.stateFile = "twonodes_2.dat"
settings2.payLogFile = "payments2.log"
with open(settings2.stateFile, "wb") as f:
	f.write("""
		{
		"links":
		[
			{
			"name": "node2",
			"localID": "node2",
			"remoteID": "node1",
			"remoteURL": "",
			"channels":
			[{
				"ID": 0,
				"amountLocal"           : 1000,
				"amountRemote"          : 1000,
				"transactionsIncomingReserved": {},
				"transactionsOutgoingReserved": {},
				"transactionsIncomingLocked"  : {},
				"transactionsOutgoingLocked"  : {},
				"type": "plain"
			}]
			}
		],

		"meetingPoints":
		[
			{
			"ID": "node2"
			}
		],

		"payees": []
		}
		""")
node2 = amiko.Amiko(settings2)
node2.start()

#Allow links to connect
time.sleep(3)

print "Node 1:"
pprint.pprint(node1.list())

print "Node 2:"
pprint.pprint(node2.list())

URL = node2.request(123, "receipt")
print "Payment URL:", URL

payer = node1.pay(URL)
node1.confirmPayment(payer, True)
print "Payment is ", payer.state

#Allow paylink to disconnect
time.sleep(0.5)

print "Node 1:"
pprint.pprint(node1.list())

print "Node 2:"
pprint.pprint(node2.list())

node1.stop()
node2.stop()


