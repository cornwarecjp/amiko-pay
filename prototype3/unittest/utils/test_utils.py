#!/usr/bin/env python
#    test_utils.py
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

import testenvironment

from amiko.utils import utils



class Test(unittest.TestCase):
	def test_inheritDocString(self):
		"Test doc string inheritance function decorator"

		class A:
			def f(self):
				"foo"
				pass

		class B(A):
			@utils.inheritDocString(A)
			def f(self):
				pass

		self.assertEqual(B.f.__doc__, "foo")


	def test_enum(self):
		"Test enum class"

		enum = utils.Enum(["foo", "bar"])

		elements = [e for e in enum]
		elements.sort()
		self.assertEqual(elements, ["bar", "foo"])

		self.assertEqual(enum.foo, "foo")
		self.assertEqual(enum.bar, "bar")
		with self.assertRaises(AttributeError):
			e = enum.foobar



if __name__ == "__main__":
	unittest.main(verbosity=2)

