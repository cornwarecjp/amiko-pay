/*
    conffile.h
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

#ifndef CONFFILE_H
#define CONFFILE_H

#include <cstdio>

#include "cstring.h"
#include "exception.h"
#include "settingssource.h"


class CConfFile : public CSettingsSource
{
public:
	SIMPLEEXCEPTIONCLASS(COpenError)
	SIMPLEEXCEPTIONCLASS(CSyntaxError)
	SIMPLEEXCEPTIONCLASS(CEndOfFile)

	/*
	Constructed object:
	empty CConfFile object

	Exceptions:
	none
	*/
	CConfFile();

	/*
	filename:
	Reference to properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	CConfFile object filled with values from file

	Exceptions:
	COpenError
	CSyntaxError
	*/
	CConfFile(const CString &filename);

	~CConfFile();

	/*
	filename:
	Reference to properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	COpenError
	CSyntaxError
	*/
	void load(const CString &filename);

private:

	/*
	fp:
	File pointer of open file (NOT CHECKED)

	Exceptions:
	CEndOfFile
	*/
	CString readLine(FILE *fp);
};

#endif

