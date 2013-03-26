/*
    ripemd160.h
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

#ifndef RIPEMD160_H
#define RIPEMD160_H

#include "binbuffer.h"

class CRIPEMD160 : protected CBinBuffer
{
public:
	/*
	Constructed object:
	Uninitialized CRIPEMD160 object

	Exceptions:
	none
	*/
	CRIPEMD160();

	/*
	data:
	Reference to properly formed CBinBuffer object
	Reference lifetime: at least until the end of this function

	Constructed object:
	RIPEMD160 hash of data

	Exceptions:
	none (TODO)
	*/
	CRIPEMD160(const CBinBuffer &data);

	/*
	hash2:
	Reference to properly formed CRIPEMD160 object
	Reference lifetime: at least until the end of this function
	
	Exceptions:
	none
	*/
	inline bool operator==(const CRIPEMD160 &hash2) const
		{return CBinBuffer::operator==(hash2.toBinBuffer());}
	inline bool operator!=(const CRIPEMD160 &hash2) const
		{return CBinBuffer::operator!=(hash2.toBinBuffer());}

	/*
	Return value:
	Valid pointer
	Pointed memory contains at least getSize() bytes
	Pointed memory contains RIPEMD160 hash
	Pointer ownership: remains with this object
	Pointer lifetime: equal to the lifetime of this object

	Exceptions:
	none
	*/
	inline const unsigned char *getData() const
		{return &(*this)[0];}

	/*
	Return value:
	20

	Exceptions:
	none
	*/
	inline static size_t getSize()
		{return 20;}

	/*
	Return value:
	Reference to properly formed CBinBuffer object
	Reference lifetime: equal to the lifetime of this object

	Exceptions:
	none
	*/
	inline const CBinBuffer &toBinBuffer() const
		{return *this;}

	/*
	buffer:
	Reference to properly formed CBinBuffer object
	Reference lifetime: at least until the end of this function
	buffer.size() == 20 (CHECKED)

	Return value:
	RIPEMD160 hash containing the data of buffer

	Exceptions:
	CBinBuffer::CReadError
	*/
	static CRIPEMD160 fromBinBuffer(const CBinBuffer &buffer);
};

#endif

