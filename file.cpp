/*
    file.cpp
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

#include <sys/stat.h>
#include <sys/types.h>
#include <cstdio>
#include <errno.h>

#include "file.h"


CFile::CFile(const CString &path, const CString &mode)
{
	m_FP = fopen(path.c_str(), mode.c_str());
}


CFile::~CFile()
{
	if(m_FP != NULL) fclose(m_FP);
}


void CFile::makeDirectory(const CString &dir)
{
	if(mkdir(dir.c_str(), S_IRUSR | S_IWUSR | S_IXUSR) != 0 && errno != EEXIST)
		throw CError(CString::format(
			"Error when creating directory %s", 256, dir.c_str()
			));
}


void CFile::rename(const CString &from, const CString &to)
{
	if(::rename(from.c_str(), to.c_str()) != 0)
		throw CError(CString::format(
			"ERROR while renaming %s to %s",
			1024, from.c_str(), to.c_str()
			));
}


