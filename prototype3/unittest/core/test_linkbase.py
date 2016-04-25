#!/usr/bin/env python
#    test_linkbase.py
#    Copyright (C) 2016 by CJP
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

import testenvironment

from amiko.core import messages

from amiko.core import linkbase



class Test(unittest.TestCase):
	def setUp(self):
		self.linkBase = linkbase.LinkBase()


	def test_makeRouteOutgoing(self):
		'Test makeRouteOutgoing'
		self.assertEqual(self.linkBase.makeRouteOutgoing(None), [])


	def test_makeRouteIncoming(self):
		'Test makeRouteIncoming'
		self.assertEqual(self.linkBase.makeRouteIncoming(None), [])


	def test_haveNoRouteOutgoing(self):
		'Test haveNoRouteOutgoing'
		self.assertEqual(self.linkBase.haveNoRouteOutgoing(None, None), [])


	def test_haveNoRouteIncoming(self):
		'Test haveNoRouteIncoming'
		self.assertEqual(self.linkBase.haveNoRouteIncoming(None), [])


	def test_cancelOutgoing(self):
		'Test cancelOutgoing'
		self.assertEqual(self.linkBase.cancelOutgoing(None), [])


	def test_cancelIncoming(self):
		'Test cancelIncoming'
		self.assertEqual(self.linkBase.cancelIncoming(None), [])


	def test_lockOutgoing(self):
		'Test lockOutgoing'
		self.assertEqual(self.linkBase.lockOutgoing(None), [])


	def test_lockIncoming(self):
		'Test lockIncoming'
		self.assertEqual(self.linkBase.lockIncoming(None), [])


	def test_requestCommitOutgoing(self):
		'Test requestCommitOutgoing'
		self.assertEqual(self.linkBase.requestCommitOutgoing(None), [])


	def test_requestCommitIncoming(self):
		'Test requestCommitIncoming'
		self.assertEqual(self.linkBase.requestCommitIncoming(None), [])


	def test_settleCommitOutgoing(self):
		'Test settleCommitOutgoing'
		self.assertEqual(self.linkBase.settleCommitOutgoing(None), [])


	def test_settleCommitIncoming(self):
		'Test settleCommitIncoming'
		self.assertEqual(self.linkBase.settleCommitIncoming(None), [])


	def test_settleRollbackOutgoing(self):
		'Test settleRollbackOutgoing'
		self.assertEqual(self.linkBase.settleRollbackOutgoing(None), [])


	def test_settleRollbackIncoming(self):
		'Test settleRollbackIncoming'
		self.assertEqual(self.linkBase.settleRollbackIncoming(None), [])



if __name__ == '__main__':
	unittest.main(verbosity=2)

