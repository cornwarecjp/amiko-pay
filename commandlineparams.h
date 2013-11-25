/*
    commandlineparams.h
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

#ifndef COMMANDLINEPARAMS_H
#define COMMANDLINEPARAMS_H

#include <vector>

#include "cstring.h"
#include "settingssource.h"

class CCommandlineParams : public CSettingsSource
{
public:
	/*
	arguments:
	Reference to properly formed std::vector<CString> object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	CCommandlineParams object filled with values from argument

	Exceptions:
	none
	*/
	CCommandlineParams(const std::vector<CString> &arguments);

	~CCommandlineParams();
};

#endif

