#    paylink.py
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

from urlparse import urlparse
import threading

import network
import messages
import event
import utils



class Payer(event.Handler):
	states = utils.Enum([
		"initial", "hasReceipt", "confirmed", "cancelled", "completed"
		])

	def __init__(self, context, URL):
		event.Handler.__init__(self, context)

		URL = urlparse(URL)
		self.remoteHost = URL.hostname
		self.remotePort = 4321 if URL.port == None else URL.port
		self.ID = URL.path[1:] #remove initial slash

		print self.remoteHost
		print self.remotePort
		print self.ID

		self.amount = None #unknown
		self.receipt = None #unknown
		self.meetingPoint = None #unknown

		# Will be set when receipt message is received from payee
		self.__receiptReceived = threading.Event()

		self.connection = network.Connection(self.context,
			(self.remoteHost, self.remotePort))

		self.connect(self.connection, event.signals.message,
			self.__messageHandler)
		# TODO: register other event handlers
		# TODO: find some way to un-register on close

		self.connection.sendMessage(messages.Pay(self.ID))

		self.state = self.states.initial


	def waitForReceipt(self):
		#TODO: timeout mechanism
		self.__receiptReceived.wait()


	def confirmPayment(self, payerAgrees):
		if self.state != self.states.hasReceipt:
			raise Exception(
				"confirmPayment should not be called in state %s" % \
					self.state
				)

		if payerAgrees:
			self.connection.sendMessage(
				messages.String("OK:" + self.meetingPoint))
			#TODO: start payment routing
			self.state = self.states.confirmed
		else:
			self.connection.sendMessage(messages.String("NOK"))
			#TODO: close everything
			self.state = self.states.cancelled


	def __messageHandler(self, message):
		situation = (self.state, message.__class__)

		if situation == (self.states.initial, messages.Receipt):

			self.amount = message.amount
			self.receipt = message.receipt

			# for now, always select the first suggested meeting point.
			# Will automatically give an exception if 0 meeting points are given
			self.meetingPoint = message.meetingPoints[0]

			#TODO: hash

			self.state = self.states.hasReceipt
			self.__receiptReceived.set()

		else:
			print "Payer received unsupported message for state %s: %s" % \
				(self.state, message)
			# TODO: handle protocol error situation



class Payee(event.Handler):
	states = utils.Enum([
		"initial", "confirmed", "cancelled", "completed"
		])

	def __init__(self, context, ID, amount, receipt, meetingPoints):
		event.Handler.__init__(self, context)

		self.ID = ID
		self.amount = amount
		self.receipt = receipt
		self.meetingPoints = meetingPoints
		self.meetingPoint = None #unknown

		self.connection = None

		self.state = self.states.initial


	def connect(self, connection):
		if self.isConnected():
			print "Payee: Received a duplicate connection; closing it"
			connection.close()

		print "Payee: Connection established"
		self.connection = connection

		event.Handler.connect(self, self.connection, event.signals.message,
			self.__messageHandler)
		# TODO: register other event handlers
		# TODO: find some way to un-register on close

		# Send amount and receipt to payer:
		connection.sendMessage(messages.Receipt(
			self.amount, self.receipt, self.meetingPoints))


	def isConnected(self):
		return self.connection != None


	def __messageHandler(self, message):
		situation = (self.state, message.__class__)

		if situation == (self.states.initial, messages.String):
			if message.value == "NOK":
				print "Payee received NOK"
				self.state = self.states.cancelled
				#TODO: close everything
			elif message.value[:3] == "OK:":
				self.meetingPoint = message.value[3:]
				#TODO: check that meeting point is in self.meetingPoints
				self.state = self.states.confirmed
				print "Payee received OK: ", self.meetingPoint
				#TODO: start payment routing
			else:
				print "Payee received invalid confirmation string"
				# TODO: handle protocol error situation

		else:
			print "Payee received unsupported message for state %s: %s" % \
				(self.state, message)
			# TODO: handle protocol error situation


