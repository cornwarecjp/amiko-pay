/*
    settingssource.cpp
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

#include "settingssource.h"


CString CSettingsSource::getValue(const CString &section, const CString &key, const CString &deflt) const
{
	//find section
	std::map<CString, std::map<CString, CString> >::const_iterator s =
		m_Data.find(section);
	if(s == m_Data.end()) return deflt;
	const std::map<CString, CString> &sect = (*s).second;

	//find key
	std::map<CString, CString>::const_iterator v =
		sect.find(key);
	if(v == sect.end()) return deflt;

	//return value
	return (*v).second;
}

