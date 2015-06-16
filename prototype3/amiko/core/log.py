#    log.py
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


import traceback
import time



logfile = open("debug.log", "a")

def log(data):
	"""
	Writes data to a log file.

	Arguments:
	data: str, to be written to the log file.
	      log() adds a timestamp and a trailing newline, so these do not need
	      to be present in data.
	"""

	t = time.time()
	ms = int(1000*t % 1000)
	t_str = time.strftime("%Y-%m-%d %H:%M:%S.", time.localtime(t)) + ("%03d" % ms)

	logfile.write(t_str + ' ' + data + '\n')
	logfile.flush()



def logException():
	"""
	Logs exception information, including traceback.
	Should only be called inside exception handling code.
	"""

	text = traceback.format_exc()
	log(text)


