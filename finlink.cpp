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

#define LINKFILE_FORMAT_VERSION 1

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
	try
	{
		save();
	}
	catch(CSaveError &e)
	{
		log(CString::format("An error occurred during final save: %s\n",
			1024, e.what()
			));
	}
}


void CFinLink::sendMessage(const CBinBuffer &message)
{
	CMutexLocker lock(m_Inbox);
	m_Inbox.m_Value.push(message);
}


void CFinLink::load()
{
	CMutexLocker lock(m_Filename);

	CFilePointer f(fopen(m_Filename.m_Value.c_str(), "rb"));
	if(f.m_FP == NULL)
	{
		log(CString::format("Could not load %s; assuming this is a new link\n",
			256, m_Filename.m_Value.c_str()));
		return;
	}

	CBinBuffer data, chunk;
	chunk.resize(1024);
	while(true)
	{
		size_t ret = fread(&chunk[0], 1, chunk.size(), f.m_FP);
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


void CFinLink::save()
{
	CMutexLocker lock(m_Filename);

	CString tmpfile = m_Filename.m_Value + ".tmp";

	//Save as tmpfile
	{
		CBinBuffer data = serialize();

		//TODO: use tmp file to prevent overwriting with unfinished data
		CFilePointer f(fopen(tmpfile.c_str(), "wb"));
		if(f.m_FP == NULL)
			throw CSaveError(CString::format("ERROR: Could not store %s!!!",
				256, tmpfile.c_str()
				));

		size_t ret = fwrite(&data[0], data.size(), 1, f.m_FP);
		if(ret != 1)
			throw CSaveError(CString::format("ERROR while storing in %s!!!",
				256, tmpfile.c_str()
				));
	}

	//Overwrite file in m_Filename with tmpfile
	if(rename(tmpfile.c_str(), m_Filename.m_Value.c_str()) != 0)
		throw CSaveError(CString::format(
			"ERROR while storing in %s; new data can be found in %s!!!",
			1024, m_Filename.m_Value.c_str(), tmpfile.c_str()
			));
}


CBinBuffer CFinLink::serialize() const
{
	CBinBuffer ret;

	//Format version
	ret.appendUint<uint32_t>(LINKFILE_FORMAT_VERSION);

	//My messages
	ret.appendUint<uint32_t>(m_myMessages.size());
	for(std::list<CBinBuffer>::const_iterator i=m_myMessages.begin();
		i != m_myMessages.end(); i++)
			ret.appendBinBuffer(*i);

	//Your messages
	ret.appendUint<uint32_t>(m_yourMessages.size());
	for(std::list<CBinBuffer>::const_iterator i=m_yourMessages.begin();
		i != m_yourMessages.end(); i++)
			ret.appendBinBuffer(*i);

	return ret;
}


void CFinLink::deserialize(const CBinBuffer &data)
{
	try
	{
		size_t pos = 0;
		uint32_t formatVersion = data.readUint<uint32_t>(pos);
		if(formatVersion != LINKFILE_FORMAT_VERSION)
			throw CLoadError("File format version mismatch");

		uint32_t numMessages = data.readUint<uint32_t>(pos);
		//TODO: check whether numMessages makes sense
		for(uint32_t i=0; i < numMessages; i++)
			m_myMessages.push_back(data.readBinBuffer(pos));

		numMessages = data.readUint<uint32_t>(pos);
		//TODO: check whether numMessages makes sense
		for(uint32_t i=0; i < numMessages; i++)
			m_yourMessages.push_back(data.readBinBuffer(pos));
	}
	catch(CBinBuffer::CReadError &e)
	{
		throw CLoadError(CString(e.what()));
	}
}


