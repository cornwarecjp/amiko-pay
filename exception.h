/*
    exception.h
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

#ifndef EXCEPTION_H
#define EXCEPTION_H

#include <exception>

class CString;

/*
Base class for all exceptions in the application
*/
class CException : public std:: exception
{
public:
	/*
	text:
	Reference to properly formed CString object (NOT CHECKED)
	UTF-8 encoded (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	CException with an error message that equals text

	Exceptions:
	none
	*/
	CException(const CString &text);

	virtual ~CException() throw();

	/*
	Return value:
	Valid pointer
	Pointed memory contains null-terminated C string
	UTF-8 encoded
	String contents is the error message of this object
	Pointer ownership: remains with this object
	Pointer lifetime: equal to lifetime of this object

	Exceptions:
	none
	*/
	virtual const char *what() const throw();

private:
	/*
	This is a pointer so that we can live with the incomplete class definition
	*/
	CString *m_Text;
};

#define SIMPLEEXCEPTIONCLASS(name) class name : public CException {public: name(const CString &text) throw() : CException(text) {} };

#endif


