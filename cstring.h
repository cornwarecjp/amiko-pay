/*
    amikolink.h
    Copyright (C) 2002 by bones
    Copyright (C) 2003-2007, 2013 by CJP

    This file is part of Amiko Pay.

    Amiko Pay is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Amiko Pay is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef CSTRING_H
#define CSTRING_H

#include <stdint.h>
#include <string>

#include "exception.h"
//#include "binbuffer.h"

/*
String class.
The string data is assumed to be null-terminated, so the user of this class
should never insert null characters in the string contents.

Unless specified otherwise, string contents is assumed to be UTF-8 encoded.
*/
class CString : public std::string
{
public:
	SIMPLEEXCEPTIONCLASS(CFormatException)

	/*
	Constructed object:
	Empty string object

	Exceptions:
	none
	*/
	CString()
		: std::string()
		{}

	/*
	s:
	Reference to properly formed std::string object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	String object containing a copy of the string contents of s

	Exceptions:
	none
	*/
	CString(const std::string &s)
		: std::string(s)
		{}

	/*
	s:
	Valid pointer (NOT CHECKED)
	Pointed memory contains null-terminated C string (NOT CHECKED)
	Pointer ownership: remains with the caller
	Pointer lifetime: at least until the end of this function

	Constructed object:
	String object containing a copy of the string contents of s

	Exceptions:
	none
	*/
	CString(const char *s);

	/*
	str:
	Valid pointer (NOT CHECKED)
	Pointed memory contains null-terminated C string (NOT CHECKED)
	Pointer ownership: remains with the caller
	Pointer lifetime: at least until the end of this function

	Function behavior:
	Replaces the contents of this object with a copy of the string contents
	of str.

	Return value:
	Reference to this object

	Exceptions:
	none
	*/
	CString &operator=(const char *str);

	/*
	val:
	Properly formed CString object (NOT CHECKED)

	Return value:
	String concatenation of this object and val

	Exceptions:
	none
	*/
	CString operator+(CString const &val) const;

	/*
	val:
	Valid pointer (NOT CHECKED)
	Pointed memory contains null-terminated C string (NOT CHECKED)
	Pointer ownership: remains with the caller
	Pointer lifetime: at least until the end of this function

	Return value:
	String concatenation of this object and val

	Exceptions:
	none
	*/
	CString operator+(const char *val) const;

	/*
	str:
	Valid pointer (NOT CHECKED)
	Pointed memory contains null-terminated C string (NOT CHECKED)
	Pointer ownership: remains with the caller
	Pointer lifetime: at least until the end of this function

	Return value:
	The negation of operator==(str)

	Exceptions:
	none
	*/
	bool operator!=(const char *str) const;

	/*
	val:
	Reference to properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	The negation of operator==(val)

	Exceptions:
	none
	*/
	bool operator!=(const CString &val) const;

	/*
	This object:
	Only contains characters '0'..'9' (CHECKED)
	"big endian" (as you'd expect)
	Represented value fits in 32-bit unsigned integer (NOT CHECKED)

	Return value:
	The value as represented by this object

	Exceptions:
	CFormatException
	*/
	uint32_t parseAsDecimalInteger() const;

	/*
	Exceptions:
	none
	*/
	void strip();

	/*
	format:
	Valid pointer (NOT CHECKED)
	Pointed memory contains null-terminated C string (NOT CHECKED)
	Pointer ownership: remains with the caller
	Pointer lifetime: at least until the end of this function
	C-style format string (printf-style)

	...:
	arguments corresponding to format

	Return value:
	String object

	Exceptions:
	CFormatException
	*/
	static CString format(const char *format, size_t maxsize, ...);
};

/*
val1:
Valid pointer (NOT CHECKED)
Pointed memory contains null-terminated C string (NOT CHECKED)
Pointer ownership: remains with the caller
Pointer lifetime: at least until the end of this function

val2:
Reference to properly formed CString object (NOT CHECKED)
Reference lifetime: at least until the end of this function

Return value:
String concatenation of val1 and val2

Exceptions:
none
*/
CString operator+(const char *val1, CString const &val2);

#endif

