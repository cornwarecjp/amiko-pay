#    paylog.py
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



class PayLog:
	def __init__(self, settings):
		self.__file = open(settings.payLogFile, "a")


	def writePayer(self, p):
		self.__write(-1, p)


	def writePayee(self, p):
		self.__write(1, p)


	def __write(self, sign, p):
		if p.state == p.states.committed:
			self.__writeLogLine(sign*p.amount, p.receipt, p.state, p.ID, p.hash, p.token)
		else:
			#Don't write the token even if we know it:
			#It might be abused by someone who as read access to the log file,
			#to partially commit the transaction.
			#TODO: analyze this scenario to see whether this precaution is necessary.
			self.__writeLogLine(sign*p.amount, p.receipt, p.state, p.ID, p.hash, None)


	def __writeLogLine(self, amount, receipt, status, ID, hash, token):
		#TODO: add timestamp
		line = ", ".join([
			str(amount),
			repr(receipt), #TODO: better dealing with special characters
			status,
			ID,
			hash.encode("hex"),
			"" if token==None else token.encode("hex")
			])
		self.__file.write(line + '\n')


