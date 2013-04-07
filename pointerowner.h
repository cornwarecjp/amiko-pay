/*
    pointerowner.h
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

#ifndef POINTEROWNER_H
#define POINTEROWNER_H

/*
A pointer owner object "owns" the pointer given to is:
it deletes the pointed object when it is deleted itself.
This is useful for dealing with pointers in an exception-safe way: to
automatically delete pointers in all cases of exceptions and function returns,
simply create pointer owner objects on the stack for them.
*/
template<class T> class CPointerOwner
{
public:
	/*
	pointer:
	NULL, or
	Valid pointer (NOT CHECKED)
	Pointer ownership: passed to this object

	Constructed object:
	Owns the passed pointer

	Exceptions:
	none
	*/
	CPointerOwner(T *pointer) : m_Pointer(pointer)
		{}

	~CPointerOwner()
	{
		if(m_Pointer != NULL) delete m_Pointer;
	}

	/*
	Exceptions:
	none
	*/
	void endOwnership()
	{
		m_Pointer = NULL;
	}

private:
	T *m_Pointer;
};

#endif

