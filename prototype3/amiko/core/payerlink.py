#    payerlink.py
#    Copyright (C) 2015 by CJP
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

from urlparse import urlparse
import threading

from ..utils import utils

import settings



class PayerLink:
	states = utils.Enum([
		"initial", "hasReceipt", "confirmed", "hasRoute",
		"locked", "cancelled", "committed"
		])


	def __init__(self, URL):
		URL = urlparse(URL)
		self.remoteHost = URL.hostname
		self.remotePort = settings.defaultPort if URL.port == None else URL.port
		self.ID = URL.path[1:] #remove initial slash

		self.amount  = None #unknown
		self.receipt = None #unknown
		self.hash    = None #unknown
		self.token   = None #unknown

		self.meetingPointID = None #unknown
		self.transactionID = None

		# Will be set when receipt message is received from payee
		self.__receiptReceived = threading.Event()

		# Will be set when transaction is committed or cancelled
		self.__finished = threading.Event()

		self.state = self.states.initial


	def waitForReceipt(self):
		#TODO: timeout mechanism
		self.__receiptReceived.wait()


	def waitForFinished(self):
		#TODO: timeout mechanism
		self.__finished.wait()

