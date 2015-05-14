#!/usr/bin/env python
#    largenetwork.py
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
import json
import sys
sys.path.append('../..')

from amiko import node
from amiko.core import event, settings



"""
The network has the following shape:

            (4)
             |
            (3)
             |
(0) - (1) - (2) - (5) - (6)
             |
            (7)
             |
            (8)

Payment is between 0 and 6
"""

linkDefinitions = \
[
	[1],          #0
	[0, 2],       #1
	[1, 3, 5, 7], #2
	[2, 4],       #3
	[3],          #4
	[2, 6],       #5
	[5],          #6
	[2, 8],       #7
	[7]           #8
]

ports = [4321+i for i in range(len(linkDefinitions))]

nodes = []
for i in range(len(linkDefinitions)):
	links = linkDefinitions[i]
	s = settings.Settings()
	s.RPCURL = "dummy"
	s.listenHost = "localhost"
	s.listenPort = ports[i]
	s.advertizedHost = s.listenHost
	s.advertizedPort = s.listenPort
	s.stateFile = "state_%d.dat" % i
	s.payLogFile = "payments_%d.log" % i

	linkStates = []
	for link in links:
		localID = "link_to_%d" % link
		remoteID = "link_to_%d" % i
		linkStates.append(
			{
			"name": localID,
			"localID": localID,
			"remoteID": remoteID,
			"remoteURL": "amikolink://localhost:%d/%s" % (ports[link], remoteID),
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
			)

	state = \
	{
	"links": linkStates,

	"meetingPoints":
	[
		{
		"ID": "meetingPoint_%d" % i
		}
	],

	"payees": []
	}

	state = json.dumps(state, sort_keys=True, ensure_ascii=True,
		indent=4, separators=(',', ': '))

	with open(s.stateFile, "wb") as f:
		f.write(state)

	newNode = node.Node(s)
	newNode.start()
	nodes.append(newNode)

#Allow links to connect
time.sleep(3)

print "Before payment:"
for i in range(len(nodes)):
	print
	print "==========================="
	print "Node %d:" % i
	print "==========================="
	pprint.pprint(nodes[i].list())


#Pay from 0 to 6:
URL = nodes[6].request(123, "receipt")
print "Payment URL:", URL

payer = nodes[0].pay(URL)
nodes[0].confirmPayment(payer, True)
print "Payment is ", payer.state

#Allow paylink to disconnect
time.sleep(0.5)


print "After payment:"
for i in range(len(nodes)):
	print
	print "==========================="
	print "Node %d:" % i
	print "==========================="
	pprint.pprint(nodes[i].list())


for n in nodes:
	n.stop()

