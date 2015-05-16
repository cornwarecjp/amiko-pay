#!/usr/bin/env python
#    timestamp.py
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

import sys
sys.path.append(".")
sys.path.append("..")


def help(args):
	if len(args) == 0:
		print "Usage: %s command [args]" % sys.argv[0]
		print "Command can be one of:"
		for fn in funcNames:
			print fn

	if "help" in args:
		print "Usage: %s help [command]" % sys.argv[0]

	if "make" in args:
		print "Usage: %s make to_be_timestamped_file output_certificate_file" % sys.argv[0]

	if "verify" in args:
		print "Usage: %s verify timestamped_file input_certificate_file" % sys.argv[0]


def make(args):
	if len(args) != 2:
		help(["make"])
		sys.exit(1)

	print "Not Yet Implemented" #TODO


def verify(args):
	if len(args) != 2:
		help(["verify"])
		sys.exit(1)

	print "Not Yet Implemented" #TODO


funcs = \
{
"help": help,
"make": make,
"verify": verify
}
funcNames = funcs.keys()
funcNames.sort()

if len(sys.argv) < 2:
	help([])
	sys.exit(1)

funcs[sys.argv[1]](sys.argv[2:])

