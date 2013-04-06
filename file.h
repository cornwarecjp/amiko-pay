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

#include "cstring.h"
#include "exception.h"

class CFile
{
public:
	SIMPLEEXCEPTIONCLASS(CError)

	//TODO: spec
	CFile(const CString &path, const CString &mode);

	//TODO: spec
	~CFile();

	//TODO: spec
	static void makeDirectory(const CString &dir);

	//TODO: spec
	static void rename(const CString &from, const CString &to);


	//TODO: spec
	FILE *m_FP;
};

#endif

