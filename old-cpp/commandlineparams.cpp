/*
    commandlineparams.cpp
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

#include "log.h"

#include "commandlineparams.h"


CCommandlineParams::CCommandlineParams(const std::vector<CString> &arguments)
{
	for(size_t i=0; i < arguments.size(); i++)
	{
		const CString &arg = arguments[i];

		//Key/value pairs
		size_t pos = arg.find('=');
		if(pos == std::string::npos)
		{
			log(CString::format(
				"Warning: commandline argument does not contain '='"
				" and will be ignored: \"%s\"\n", 1024,
				arg.c_str()));
			continue;
		}

		CString key = arg.substr(0, pos);
		key.strip();
		CString value = arg.substr(pos+1);
		value.strip();

		pos = key.find('.');
		if(pos == std::string::npos)
		{
			log(CString::format(
				"Warning: commandline argument key does not contain '.'"
				" and will be ignored: \"%s\"\n", 1024,
				key.c_str()));
			continue;
		}

		CString section = key.substr(0, pos);
		section.strip();
		key = key.substr(pos+1);
		key.strip();

		m_Data[section][key] = value;
	}
}


CCommandlineParams::~CCommandlineParams()
{
}

