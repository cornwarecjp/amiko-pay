#!/usr/bin/env python
#    largenetwork_haveNoRoute.py
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
import copy
sys.path.append('..')

from amiko.channels import plainchannel

from amiko import node


import largenetwork_setup

verbose = '-v' in sys.argv



class Test(unittest.TestCase):
	def setUp(self):
		self.nodes = []


	def tearDown(self):
		for n in self.nodes:
			n.stop()


	def printNodeInfo(self, i, data):
		print
		print '==========================='
		print 'Node %d:' % i
		print '==========================='

		data = copy.deepcopy(data)

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


	def getBalance(self, data):
		return sum( \
			[
			sum([chn['amountLocal'] for chn in lnk['channels']])
			for lnk in data['links'].values()
			])


	def test_payerSide(self):
		'Test behavior when no route is found on the payer side'

		#Make a copy, where the link between 2 and 4 is broken:
		linkDefinitions = largenetwork_setup.linkDefinitions_global[:]
		linkDefinitions[2].remove(4)
		linkDefinitions[4].remove(2)

		for s in largenetwork_setup.makeNodes(linkDefinitions):
			newNode = node.Node(s)
			newNode.start()
			self.nodes.append(newNode)

		#Allow links to connect
		time.sleep(3)

		self.checkCancelledState()


	def test_payeeSide(self):
		'Test behavior when no route is found on the payee side'

		#Make a copy, where the link between 4 and 5 is broken:
		linkDefinitions = largenetwork_setup.linkDefinitions_global[:]
		linkDefinitions[4].remove(5)
		linkDefinitions[5].remove(4)

		for s in largenetwork_setup.makeNodes(linkDefinitions):
			newNode = node.Node(s)
			newNode.start()
			self.nodes.append(newNode)

		#Allow links to connect
		time.sleep(3)

		self.checkCancelledState()


	def checkCancelledState(self):
		data = [n.list() for n in self.nodes]
		if verbose:
			print 'Before payment:'
			for i, d in enumerate(data):
				self.printNodeInfo(i, d)
		beforeBalances = [self.getBalance(d) for d in data]

		t0 = time.time()
		#Pay from 0 to 7:
		URL = self.nodes[7].request(123, 'receipt')
		if verbose:
			print 'Payment URL:', URL

		amount, receipt = self.nodes[0].pay(URL)
		paymentState = self.nodes[0].confirmPayment(True)
		if verbose:
			print 'Payment is ', paymentState
		self.assertEqual(paymentState, 'cancelled')
		t1 = time.time()

		if verbose:
			print 'Payment took %f seconds' % (t1-t0)

		#Allow paylink to disconnect
		time.sleep(0.5)

		data = [n.list() for n in self.nodes]
		if verbose:
			print 'After payment:'
			for i, d in enumerate(data):
				self.printNodeInfo(i, d)

		#Check balance changes:
		afterBalances = [self.getBalance(d) for d in data]
		balanceChanges = [afterBalances[i] - beforeBalances[i] for i in range(len(self.nodes))]
		for i, change in enumerate(balanceChanges):
			self.assertEqual(change, 0)

		#Check channel consistency between peers:
		for i, d in enumerate(data):
			for name, link_a in d['links'].iteritems():
				p = len('link_to_')
				j = int(name[p:])
				link_b = data[j]['links']['link_to_%d' % i]
				chn_a = link_a['channels'][0]
				chn_b = link_b['channels'][0]
				self.assertEqual(chn_a['amountLocal'], chn_b['amountRemote'])
				self.assertEqual(chn_a['amountRemote'], chn_b['amountLocal'])

		#Check whether state is cleaned up:
		for d in data:
			self.assertEqual(d['transactions'], [])
			self.assertEqual(d['timeoutMessages'], [])
			self.assertEqual(d['payeeLinks'], {})
			self.assertEqual(d['payerLink'], None)
			for lnk in d['links'].values():
				self.assertEqual(len(lnk['channels']), 1)
				chn = lnk['channels'][0]
				self.assertEqual(chn['transactionsIncomingReserved'], {})
				self.assertEqual(chn['transactionsOutgoingReserved'], {})
				self.assertEqual(chn['transactionsIncomingLocked'], {})
				self.assertEqual(chn['transactionsOutgoingLocked'], {})


if __name__ == '__main__':
	unittest.main(verbosity=2)

