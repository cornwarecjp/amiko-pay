#    persistentobject.py
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

import os

import log
from ..utils import serializable
from ..utils import uid



class PersistentObject:
	def __init__(self, filename, defaultObject):
		self.__UIDContext = uid.Context()
		self.__filename = filename
		self.__object = None

		self.__oldState = None
		self.__withBlockCount = 0

		try:
			self.load()
		except IOError:
			log.log("Failed to load from %s" % self.__filename)
			log.log("Starting with default state")

			self.__object = defaultObject

			#Store the default state:
			self.save()


	def load(self):
		oldFile = self.__filename + ".old"
		if os.access(oldFile, os.F_OK):
			if os.access(self.__filename, os.F_OK):
				#Remove old file if normal state file exists:
				os.remove(oldFile)
			else:
				#Use old file if state file does not exist:
				os.rename(oldFile, self.__filename)

		with open(self.__filename, 'rb') as fp:
			stateData = fp.read()

		self.__setState(serializable.deserializeState(stateData))


	def save(self):
		stateData = serializable.serializeState(self.__getState())

		newFile = self.__filename + ".new"
		log.log("Saving in " + newFile)
		with open(newFile, 'wb') as fp:
			fp.write(stateData)

		oldFile = self.__filename + ".old"

		#Replace old data with new data
		try:
			os.rename(self.__filename, oldFile)
		except OSError:
			log.log("Got OSError on renaming old state file; probably it didn't exist yet, which is OK in a fresh installation.")
		os.rename(newFile, self.__filename)
		try:
			os.remove(oldFile)
		except OSError:
			log.log("Got OSError on removing old state file; probably it didn't exist, which is OK in a fresh installation.")


	def getUIDContext(self):
		return self.__UIDContext

	def __getState(self):
		return serializable.object2State(self.__object)


	def __setState(self, s):
		self.__object = serializable.state2Object(s, self.__UIDContext)


	def __enter__(self):
		if self.__withBlockCount == 0:
			self.__oldState = self.__getState()

		self.__withBlockCount += 1
		return self


	def __exit__(self, exceptionType, value, traceback):
		self.__withBlockCount -= 1

		if self.__withBlockCount == 0:
			if exceptionType is None:
				#Save state in case of no exception
				self.save()
			else:
				#Restore old state in case of an exception
				self.__setState(self.__oldState)

			self.__oldState = None

		return False #False = don't silence exceptions


	def __getattr__(self, name):
		#TODO: only allow within 'with block'
		#For all attributes not defined here, forward the object's attributes:
		return getattr(self.__object, name)


	def __setattr__(self, name, value):
		#TODO: only allow within 'with block'
		#For all attributes not defined here, forward the object's attributes:
		if name.startswith('_PersistentObject'):
			self.__dict__[name] = value
		else:
			setattr(self.__object, name, value)

