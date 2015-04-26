#!/usr/bin/env python
#    test_log.py
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

import unittest
import sys
sys.path.append('../..')

import testenvironment

from amiko.core import log


class DummyFile:
	def __init__(self):
		self.data = []


	def __enter__(self):
		self.oldFile = log.logfile
		log.logfile = self
		return self


	def __exit__(self, exc_type, exc_val, exc_tb):
		log.logfile = self.oldFile


	def write(self, line):
		self.data.append(line)


	def flush(self):
		self.data.append(self.flush)


class Test(unittest.TestCase):
	def test_logFileMode(self):
		"Test whether log file is opened in append mode"
		self.assertEqual(log.logfile.mode, "a")


	def test_logFileName(self):
		"Test whether log filename is debug.log"
		self.assertEqual(log.logfile.name, "debug.log")


	def test_log(self):
		"Test the log function"
		with DummyFile() as f:
			log.log("foobar")

			#A single item has been written, and then flushed:
			self.assertEqual(len(f.data), 2)
			self.assertEqual(type(f.data[0]), str)
			self.assertEqual(f.data[1], f.flush)

			line = f.data[0]

			#The expected data is present, including a trailing newline:
			self.assertTrue(line.endswith("foobar\n"))
			#TODO: test the timestamp


	def test_logException(self):
		"Test the logException function"
		with DummyFile() as f:
			try:
				x = 1 / 0
			except:
				log.logException()

			#A single item has been written, and then flushed:
			self.assertEqual(len(f.data), 2)
			self.assertEqual(type(f.data[0]), str)
			self.assertEqual(f.data[1], f.flush)

			lines = f.data[0].split('\n')

			#The expected data is present, including a trailing newline:
			self.assertTrue("Traceback" in lines[0])
			self.assertTrue('File "test_log.py", line' in lines[1])
			self.assertTrue("x = 1 / 0" in lines[2])
			self.assertTrue("ZeroDivisionError: integer division or modulo by zero" in lines[3])
			self.assertGreater(len(lines), 4)


if __name__ == "__main__":
	unittest.main(verbosity=2)

