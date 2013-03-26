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

	//TODO
}


