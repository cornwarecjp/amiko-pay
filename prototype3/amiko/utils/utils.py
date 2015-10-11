#    utils.py
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

import copy



class Enum(set):
	"""
	An enumeration class.
	It can be used as an iterable (in fact, it's derived from the set class),
	and its elements can be accessed as attributes.
	"""

	def __getattr__(self, name):
		if name in self:
			return name
		raise AttributeError


def inheritDocString(cls):
	"""
	Function decorator which lets a method inherit its doc string from a method
	with the same name in the given class.
	"""

	def docstring_inheriting_decorator(fn):
		fn.__doc__ = getattr(cls,fn.__name__).__doc__
		return fn
	return docstring_inheriting_decorator


def dictSum(a, b):
	"""
	Returns a dictionary that contains the elements of both a and b.
	In case of equal keys, the values in b get included.
	"""

	ret = copy.copy(a) #shallow copy
	ret.update(b)
	return ret

