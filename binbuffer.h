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

#include <vector>

class CString;

/*
Buffer for arbitrary-content binary data
*/
class CBinBuffer : public std::vector<unsigned char>
{
public:

	/*
	Constructed object:
	Empty buffer object
	*/
	CBinBuffer() throw();

	/*
	str:
	Reference to properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	
	Constructed object:
	Buffer object containing a copy of the contents of str
	(not including null character at the end)
	*/
	CBinBuffer(const CString &str) throw();
};

#endif


