/*
    finlink.cpp
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
#include <errno.h>

#include <cstdio>

#include "log.h"
#include "bitcoinaddress.h"

#include "finlink.h"

//TODO: make this a setting:
#define LINKSDIR "./links/"

//RAII file pointer micro-class:
//TODO: put in separate file with FS utilities
class CFilePointer
{
public:
	CFilePointer(FILE *fp)
		{m_FP = fp;}
	~CFilePointer()
		{if(m_FP != NULL) fclose(m_FP);}
	FILE *m_FP;
};


CFinLink::CFinLink(const CAmikoSettings::CLink &linkInfo) :
	m_LocalKey(linkInfo.m_localKey),
	m_RemoteKey(linkInfo.m_remoteKey),
	m_Filename(CString(LINKSDIR) + getBitcoinAddress(m_LocalKey))
{
	if(mkdir(LINKSDIR, S_IRUSR | S_IWUSR | S_IXUSR) != 0 && errno != EEXIST)
		log(CString::format("Error when creating directory %s\n", 256, LINKSDIR));

	load();

	//To make sure we can save, we try it once here:
	save();
}


CFinLink::~CFinLink()
{
	//Should already be saved; just do it one final time just to be sure
	save();
}


void CFinLink::sendMessage(const CBinBuffer &message)
{
	//TODO (for now, the message is thrown away)
}


void CFinLink::load()
{
	CFilePointer f(fopen(m_Filename.c_str(), "rb"));
	if(f.m_FP == NULL)
	{
		log(CString::format("Could not load %s; assuming this is a new link\n",
			256, m_Filename.c_str()));
		return;
	}

	CBinBuffer data, chunk;
	chunk.resize(1024);
	while(true)
	{
		size_t ret = fread(&chunk[0], chunk.size(), 1, f.m_FP);
		if(ret < chunk.size())
		{
			//TODO: distinguish between EOF and error
			chunk.resize(ret);
			data.appendRawBinBuffer(chunk);
			break;
		}
		data.appendRawBinBuffer(chunk);
	}

	deserialize(data);
}


void CFinLink::save() const
{
	CBinBuffer data = serialize();

	//TODO: use tmp file to prevent overwriting with unfinished data
	CFilePointer f(fopen(m_Filename.c_str(), "wb"));
	if(f.m_FP == NULL)
	{
		//TODO: make this an exception?
		//In that case, catch the exception in the destructor
		log(CString::format("ERROR: Could not store %s!!!\n",
			256, m_Filename.c_str()));
		return;
	}	

	size_t ret = fwrite(&data[0], data.size(), 1, f.m_FP);
	if(ret != 1)
	{
		//TODO: make this an exception?
		//In that case, catch the exception in the destructor
		log(CString::format("ERROR while storing in %s!!!\n",
			256, m_Filename.c_str()));
		return;
	}
}


CBinBuffer CFinLink::serialize() const
{
	return CBinBuffer("dummy data");
}


void CFinLink::deserialize(const CBinBuffer &data)
{
}


