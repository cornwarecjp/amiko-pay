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

from amiko.channels import plainchannel

from amiko import node
from amiko.core import settings



"""
The network has the following shape:

            (3)         (6)
             |           |
(0) - (1) - (2) - (4) - (5) - (7)
             |           |
            (8)         (10)
             |           |
            (9)         (11)

Payment is between 0 and 7
Meeting point is 4
"""

linkDefinitions = \
[
	[1],          #0
	[0, 2],       #1
	[1, 3, 4, 8], #2
	[2],          #3
	[2, 5],       #4
	[4, 6, 7, 10],#5
	[5],          #6
	[5],          #7
	[2, 9],       #8
	[8],          #9
	[5, 11],     #10
	[10]         #11
]

ports = [4321+i for i in range(len(linkDefinitions))]

nodes = []
for i in range(len(linkDefinitions)):
	links = linkDefinitions[i]
	s = settings.Settings()
	s.bitcoinRPCURL = "dummy"
	s.listenHost = "localhost"
	s.listenPort = ports[i]
	s.advertizedHost = s.listenHost
	s.advertizedPort = s.listenPort
	s.stateFile = "state_%d.dat" % i
	s.payLogFile = "payments_%d.log" % i
	s.externalMeetingPoints = ["Node4"]

	meetingPoints = '{}'
	if i == 4:
		meetingPoints = '{"Node4": null}'

	linkStates = []
	linkConnections = []
	for link in links:
		localID = "link_to_%d" % link
		remoteID = "link_to_%d" % i
		linkStates.append(
			""""%s":
			{
				"_class": "Link",
				"channels":
				[
				{
				"_class": "PlainChannel",
				"state": "ready",
				"amountLocal": 1000,
				"amountRemote": 1000,
				"transactionsIncomingLocked": {},
				"transactionsOutgoingLocked": {},
				"transactionsIncomingReserved": {},
				"transactionsOutgoingReserved": {}
				}
				],
				"remoteID": "%s"
			}""" % (localID, remoteID)
			)
		linkConnections.append(
			""""%s":
			{
				"_class": "PersistentConnection",
				"connectMessage":
				{
					"_class": "ConnectLink",
					"ID": "%s",
					"callbackHost": "localhost", "callbackPort": %d, "callbackID": "%s"
				},
				"messages": [], "lastIndex": -1, "notYetTransmitted": 0,
				"host": "localhost", "port": %d,
				"closing": false
			}""" % (localID, remoteID, ports[i], localID, ports[link])
			)

	linkStates = ",\n".join(linkStates)
	linkConnections = ",\n".join(linkConnections)

	state = \
	"""{
		"_class": "NodeState",
		"links":
		{
		%s
		},
		"connections":
		{
		%s
		},
		"transactions": {},
		"meetingPoints": %s,
		"payeeLinks": {},
		"payerLink": null,
		"timeoutMessages": []
	}""" % (linkStates, linkConnections, meetingPoints)

	with open(s.stateFile, "wb") as f:
		f.write(state)

	newNode = node.Node(s)
	newNode.start()
	nodes.append(newNode)



def printNodeInfo():
	for i in range(len(nodes)):
		print
		print "==========================="
		print "Node %d:" % i
		print "==========================="
		data = nodes[i].list()

		data['links'] = \
			{
			ID :
			{
				'amountLocal' : sum([chn['amountLocal'] for chn in lnk['channels']]),
				'amountRemote': sum([chn['amountRemote'] for chn in lnk['channels']]),
			}

			for ID, lnk in data['links'].iteritems()
			}
		del data['connections']
		pprint.pprint(data)



#Allow links to connect
time.sleep(3)

print "Before payment:"
printNodeInfo()

t0 = time.time()
#Pay from 0 to 7:
URL = nodes[7].request(123, "receipt")
print "Payment URL:", URL

amount, receipt = nodes[0].pay(URL)
paymentState = nodes[0].confirmPayment(True)
print "Payment is ", paymentState
t1 = time.time()

print "Payment took %f seconds" % (t1-t0)

#Allow paylink to disconnect
time.sleep(0.5)


print "After payment:"
printNodeInfo()


for n in nodes:
	n.stop()

