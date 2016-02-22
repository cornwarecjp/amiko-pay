#!/usr/bin/env python
#    twonodes.py
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

import unittest

import time
import pprint
import sys
sys.path.append('..')

from amiko.channels import plainchannel

from amiko import node
from amiko.core import settings



class Test(unittest.TestCase):
	def setUp(self):
		settings1 = settings.Settings()
		settings1.name = 'Node 1'
		settings1.bitcoinRPCURL = 'dummy'
		settings1.listenHost = 'localhost'
		settings1.listenPort = 4322
		settings1.advertizedHost = settings1.listenHost
		settings1.advertizedPort = settings1.listenPort
		settings1.stateFile = 'twonodes_1.dat'
		settings1.payLogFile = 'payments1.log'
		settings1.externalMeetingPoints = ['MeetingPoint2']
		with open(settings1.stateFile, 'wb') as f:
			f.write('''
				{
					"_class": "NodeState",
					"links":
					{
						"node1":
						{
							"_class": "Link",
							"channels":
							[
							{
							"_class": "PlainChannel",
							"state": "open",
							"amountLocal": 1000,
							"amountRemote": 0,
							"transactionsIncomingLocked": {},
							"transactionsOutgoingLocked": {},
							"transactionsIncomingReserved": {},
							"transactionsOutgoingReserved": {}
							}
							],
							"localID": "node1",
							"remoteID": "node2"
						}
					},
					"connections":
					{
						"node1":
						{
							"_class": "PersistentConnection",
							"connectMessage":
							{
								"_class": "ConnectLink",
								"ID": "node2",
								"callbackHost": "localhost", "callbackPort": 4322, "callbackID": "node1"
							},
							"messages": [], "lastIndex": -1, "notYetTransmitted": 0,
							"host": "localhost", "port": 4323,
							"closing": false
						}
					},
					"transactions": [],
					"meetingPoints": {},
					"payeeLinks": {},
					"payerLink": null,
					"timeoutMessages": []
				}
				''')
		self.node1 = node.Node(settings1)
		self.node1.start()

		settings2 = settings.Settings()
		settings2.name = 'Node 2'
		settings2.bitcoinRPCURL = 'dummy'
		settings2.listenHost = 'localhost'
		settings2.listenPort = 4323
		settings2.advertizedHost = settings2.listenHost
		settings2.advertizedPort = settings2.listenPort
		settings2.stateFile = 'twonodes_2.dat'
		settings2.payLogFile = 'payments2.log'
		with open(settings2.stateFile, 'wb') as f:
			f.write('''
				{
					"_class": "NodeState",
					"links":
					{
						"node2":
						{
							"_class": "Link",
							"channels":
							[
							{
							"_class": "PlainChannel",
							"state": "open",
							"amountLocal": 0,
							"amountRemote": 1000,
							"transactionsIncomingLocked": {},
							"transactionsOutgoingLocked": {},
							"transactionsIncomingReserved": {},
							"transactionsOutgoingReserved": {}
							}
							],
							"localID": "node2",
							"remoteID": "node1"
						}
					},
					"connections":
					{
						"node2":
						{
							"_class": "PersistentConnection",
							"connectMessage":
							{
								"_class": "ConnectLink",
								"ID": "node1",
								"callbackHost": "localhost", "callbackPort": 4323, "callbackID": "node2"
							},
							"messages": [], "lastIndex": -1, "notYetTransmitted": 0,
							"host": "localhost", "port": 4322,
							"closing": false
						}
					},
					"transactions": [],
					"meetingPoints": {"MeetingPoint2": {"_class": "MeetingPoint", "transactions": {}, "ID": "MeetingPoint2"}},
					"payeeLinks": {},
					"payerLink": null,
					"timeoutMessages": []
				}
				''')
		self.node2 = node.Node(settings2)
		self.node2.start()

		#Allow links to connect
		time.sleep(3)


	def tearDown(self):
		self.node1.stop()
		self.node2.stop()


	def test_success(self):
		'Test successfully performing a transaction between neighboring nodes'

		verbose = '-v' in sys.argv

		if verbose:
			print 'Node 1:'
			pprint.pprint(self.node1.list())

			print 'Node 2:'
			pprint.pprint(self.node2.list())

		URL = self.node2.request(123, 'receipt')
		if verbose:
			print 'Payment URL:', URL

		amount, receipt = self.node1.pay(URL)
		if verbose:
			print 'Amount: ', amount
			print 'Receipt: ', receipt
		self.assertEqual(amount, 123)
		self.assertEqual(receipt, 'receipt')

		paymentState = self.node1.confirmPayment(True)
		if verbose:
			print 'Payment is ', paymentState
		self.assertEqual(paymentState, 'committed')

		#Allow paylink to disconnect
		time.sleep(0.5)

		state1 = self.node1.list()
		state2 = self.node2.list()
		if verbose:
			print 'Node 1:'
			pprint.pprint(state1)

			print 'Node 2:'
			pprint.pprint(state2)
		del state1['connections']['node1']['connectMessage']['dice']
		del state2['connections']['node2']['connectMessage']['dice']
		self.assertEqual(state1,
			{'_class': 'NodeState',
			'connections':
				{
				'node1':
					{'_class': 'PersistentConnection',
					'closing': False,
					'connectMessage':
						{'_class': 'ConnectLink',
						'ID': 'node2',
						'callbackHost': 'localhost',
						'callbackID': 'node1',
						'callbackPort': 4322
						},
					'host': 'localhost',
					'lastIndex': 2,
					'messages': [],
					'notYetTransmitted': 0,
					'port': 4323
					}
				},
			'links':
				{
				'node1':
					{'_class': 'Link',
					'channels':
						[
						{'_class': 'PlainChannel',
						'amountLocal': 877,
						'amountRemote': 123,
						'state': 'open',
						'transactionsIncomingLocked': {},
						'transactionsIncomingReserved': {},
						'transactionsOutgoingLocked': {},
						'transactionsOutgoingReserved': {}
						}
						],
					'localID': 'node1',
					'remoteID': 'node2'
					}
				},
			'meetingPoints': {},
			'payeeLinks': {},
			'payerLink': None,
			'timeoutMessages': [],
			'transactions': []
			})
		self.assertEqual(state2,
			{'_class': 'NodeState',
			'connections':
				{
				'node2':
					{'_class': 'PersistentConnection',
					'closing': False,
					'connectMessage':
						{'_class': 'ConnectLink',
						'ID': 'node1',
						'callbackHost': 'localhost',
						'callbackID': 'node2',
						'callbackPort': 4323,
						},
					'host': 'localhost',
					'lastIndex': 1,
					'messages': [],
					'notYetTransmitted': 0,
					'port': 4322
					}
				},
			'links':
				{
				'node2':
					{'_class': 'Link',
					'channels':
						[
						{'_class': 'PlainChannel',
						'amountLocal': 123,
						'amountRemote': 877,
						'state': 'open',
						'transactionsIncomingLocked': {},
						'transactionsIncomingReserved': {},
						'transactionsOutgoingLocked': {},
						'transactionsOutgoingReserved': {}
						}
						],
					'localID': 'node2',
					'remoteID': 'node1'
					}
				},
			'meetingPoints':
				{
				'MeetingPoint2':
					{'_class': 'MeetingPoint',
					'ID': 'MeetingPoint2'
					}
				},
			'payeeLinks': {},
			'payerLink': None,
			'timeoutMessages': [],
			'transactions': []
			})



if __name__ == '__main__':
	unittest.main(verbosity=2)

