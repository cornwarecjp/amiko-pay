/*
    binbuffer.h
    Copyright (C) 2013 by CJP

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

#ifndef BINBUFFER_H
#define BINBUFFER_H

#include <cstdio>
#include <vector>

#include "cstring.h"
#include "exception.h"

/*
Buffer for arbitrary-content binary data
*/
class CBinBuffer : public std::vector<unsigned char>
{
public:
	SIMPLEEXCEPTIONCLASS(CReadError)
	SIMPLEEXCEPTIONCLASS(CWriteError)

	/*
	Constructed object:
	Empty buffer object

	Exceptions:
	none
	*/
	CBinBuffer();

	/*
	str:
	Reference to properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	
	Constructed object:
	Buffer object containing a copy of the contents of str
	(not including null character at the end)

	Exceptions:
	none
	*/
	CBinBuffer(const CString &str);

	/*
	data:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	none
	*/
	bool operator==(const CBinBuffer &data) const;

	/*
	this object:
	Does not contain null characters (CHECKED)
	
	Return value:
	String object containing a copy of the contents of this object

	Exceptions:
	CReadError
	*/
	CString toString() const;

	/*
	T:
	unsigned integer type (NOT CHECKED)

	Exceptions:
	none
	*/
	template<class T> void appendUint(T value)
	{
		//big endian
		for(unsigned int i=sizeof(T); i != 0; i--)
			push_back((
				value >> ( 8 * (i-1) )
				) & 0xff);
	}

	/*
	value:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	CWriteError
	*/
	void appendBinBuffer(const CBinBuffer &value);
	void appendRawBinBuffer(const CBinBuffer &value);

	/*
	T:
	unsigned integer type (NOT CHECKED)

	pos:
	Reference to integer (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	pos <= size() - {size of return value} (CHECKED)
	The value of pos will be incremented with {size of return value}

	Return value:
	Data read from this object at position pos

	Exceptions:
	CReadError
	*/
	template<class T> T readUint(size_t &pos) const
	{
		if(pos+sizeof(T) < pos)
			throw CReadError("CBinBuffer::readUint(size_t &): integer overflow");
		if(pos+sizeof(T) > size())
			throw CReadError("CBinBuffer::readUint(size_t &): end of buffer");

		//big endian
		T ret = 0;
		for(unsigned int i=0; i < sizeof(T); i++)
			ret |= (  T((*this)[pos+i]) << (8*(sizeof(T)-i-1))  );

		pos += sizeof(T);
		return ret;
	}

	/*
	pos:
	Reference to integer (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	pos <= size() - 4 (CHECKED)
	The value of pos will be incremented with the amount of data read

	Return value:
	Data read from this object at position pos

	Exceptions:
	CReadError
	*/
	CBinBuffer readBinBuffer(size_t &pos) const;

	/*
	pos:
	Reference to integer (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	pos <= size() (CHECKED)
	The value of pos will be incremented with length

	length:
	length <= size() - pos (CHECKED)

	Return value:
	Data read from this object at position pos

	Exceptions:
	CReadError
	*/
	CBinBuffer readRawBinBuffer(size_t &pos, size_t length) const;

	/*
	Return value:
	Hexadecimal representation of this object

	Exceptions:
	none
	*/
	CString hexDump() const;
};

#endif


