/*
    cstring.cpp
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

#include <cstdio>
#include <cstdlib>
#include <cstdarg>

#include "cstring.h"

using namespace std;

/*
	Some code comes from cstring.h, originally written by bones
*/


CString::CString(const char *s)
{
	this->assign(s);
}


CString &CString::operator=(const char *str)
{
	this->assign(str);
	return *this;
}


CString CString::operator+(CString const &val) const
{
	CString ret(*this);
	ret.append(val);
	return ret;
}


CString CString::operator+(const char *val) const
{
	CString ret(*this);
	ret.append(val);
	return ret;
}


CString operator+(const char *val1, CString const &val2)
{
	CString ret(val1);
	ret.append(val2);
	return ret;
}


bool CString::operator!=(const char *str) const
{
	return !(*this == str);
}


bool CString::operator!=(const CString &val) const
{
	return !(*this == val);
}


uint32_t CString::parseAsDecimalInteger() const
{
	uint32_t ret = 0;
	for(size_t i=0; i<length(); i++)
	{
		unsigned char c = (*this)[i];
		if(c < '0' || c > '9')
			throw CString::CFormatException(
				"Illegal character in decimal integer");
		ret = 10*ret + (c - '0');
	}
	return ret;
}


CString CString::format(const char *format, size_t maxsize, ...)
{
	char buffer[maxsize];

	va_list ap;
	va_start(ap, maxsize);
	int ret = vsnprintf(buffer, maxsize, format, ap);
	va_end(ap);

	if(ret < 0)
		throw CString::CFormatException("Format error");

	return CString(buffer);
}

