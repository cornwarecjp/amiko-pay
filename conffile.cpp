/*
    conffile.cpp
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

#include <cstdio>

#include "conffile.h"

//RAII file pointer micro-class:
class CFilePointer
{
public:
	CFilePointer(FILE *fp)
		{m_FP = fp;}
	~CFilePointer()
		{if(m_FP != NULL) fclose(m_FP);}
	FILE *m_FP;
};

CConfFile::CConfFile()
{
}


CConfFile::CConfFile(const CString &filename)
{
	load(filename);
}


CConfFile::~CConfFile()
{
}


void CConfFile::load(const CString &filename)
{
	CFilePointer f(fopen(filename.c_str(), "rb"));

	if(f.m_FP == NULL)
		throw COpenError("CConfFile::load(const CString &): could not open file");

	try
	{
		CString currentSection = "";
		while(true)
		{
			CString line = readLine(f.m_FP);

			//Remove comment
			size_t pos = line.find('#');
			if(pos != std::string::npos)
				line.resize(pos);

			//Remove surrounding whitespace
			line.strip();

			//Empty lines
			if(line.empty()) continue;

			//Section headers
			if(line[0] == '[' && line[line.length()-1] == ']')
			{
				currentSection = line.substr(1, line.length()-2);
				continue;
			}

			//Key/value pairs
			pos = line.find('=');
			if(pos == std::string::npos)
				//TODO: please be a little more userfriendly than this
				throw CSyntaxError("Syntax error in configuration file");

			CString key = line.substr(0, pos);
			key.strip();
			CString value = line.substr(pos+1);
			value.strip();

			m_Data[currentSection][key] = value;
		}
	}
	catch(CEndOfFile &e)
	{}
}


CString CConfFile::readLine(FILE *fp)
{
	CString ret;

	int c = fgetc(fp);
	if(c == EOF) throw CEndOfFile("");
	if(c == '\n' || c == '\r') return ret;

	ret += char(c);

	while(true)
	{
		c = fgetc(fp);
		if(c == EOF || c == '\n' || c == '\r') break;
		ret += char(c);
	}

	return ret;
}


CString CConfFile::getValue(const CString &section, const CString &key, const CString &deflt) const
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



