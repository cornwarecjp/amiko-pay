/*
    file.h
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

#ifndef FILE_H
#define FILE_H

#include <cstdio>

#include <vector>

#include "cstring.h"
#include "exception.h"

class CFile
{
public:
	SIMPLEEXCEPTIONCLASS(CError)

	/*
	path:
	Reference to properly formed std::string object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	mode:
	Reference to properly formed std::string object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Opens a file with the standard C function fopen.

	Constructed object:
	CFile object
	If file opening succeeded:
		m_FP is the file pointer of the opened file
	Else:
		m_FP is NULL
	Pointer ownership of m_FP belong to this object.

	Exceptions:
	None
	*/
	CFile(const CString &path, const CString &mode);

	/*
	If m_FP is non-NULL:
		closes m_FP with the standard C function fclose.
	*/
	~CFile();

	/*
	dir:
	Reference to properly formed std::string object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Creates a directory.

	Exceptions:
	CError
	*/
	static void makeDirectory(const CString &dir);

	/*
	dir:
	Reference to properly formed std::string object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	directory contents of dir
	Not necessarily sorted!
	Contains the full contents (files, directories and other objects)

	Exceptions:
	CError
	*/
	static std::vector<CString> getDirectoryContents(const CString &dir);

	/*
	from:
	Reference to properly formed std::string object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	to:
	Reference to properly formed std::string object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Renames a file.

	Exceptions:
	CError
	*/
	static void rename(const CString &from, const CString &to);


	/*
	File pointer to an open file,
	or NULL if the file is not open.
	*/
	FILE *m_FP;
};

#endif

