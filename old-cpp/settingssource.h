/*
    settingssource.h
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

#ifndef SETTINGSSOURCE_H
#define SETTINGSSOURCE_H

#include <map>

#include "cstring.h"

/*
Base-class for anything that acts as a source of setting values
*/
class CSettingsSource
{
public:
	/*
	section:
	key:
	deflt:
	Reference to properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	The value corresponding to section,key, or
	deflt if section,key does not exist.

	Exceptions:
	none
	*/
	CString getValue(const CString &section, const CString &key, const CString &deflt) const;

protected:
	/*
	Outer-level key is section name
	Inner-level key is variable name
	Inner-level value is variable value
	*/
	std::map<CString, std::map<CString, CString> > m_Data;
};

#endif

