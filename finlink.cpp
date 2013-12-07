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
#include "messages.h"
#include "file.h"
#include "pointerowner.h"

#include "finlink.h"

#define LINKFILE_FORMAT_VERSION 1


CFinLink::CFinLink(const CString &filename) :
	//m_LocalKey(linkInfo.m_localKey),
	//m_RemoteKey(linkInfo.m_remoteKey),
	m_Filename(filename)
{
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

	CFile f(m_Filename.m_Value, "rb");
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
		CFile f(tmpfile, "wb");
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
	try
	{
		CFile::rename(tmpfile, m_Filename.m_Value);
	}
	catch(CFile::CError &e)
	{
		throw CSaveError(CString::format(
			"ERROR while storing in %s; new data can be found in %s!!!",
			1024, m_Filename.m_Value.c_str(), tmpfile.c_str()
			));
	}
}


CBinBuffer CFinLink::serialize()
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

	//TODO: transactions

	//Route table
	{
		CMutexLocker lock(m_RouteTable);
		CRouteTable &t = m_RouteTable.m_Value;

		ret.appendUint<uint32_t>(t.size());
		for(CRouteTable::iterator i = t.begin(); i != t.end(); i++)
		{
			ret.appendBinBuffer(i->first);
			ret.appendUint<uint16_t>(i->second.m_minHopCount);
			ret.appendUint<uint16_t>(i->second.m_maxSendHopCount);
			ret.appendUint<uint16_t>(i->second.m_maxReceiveHopCount);
			ret.appendUint<uint64_t>(i->second.m_maxSend);
			ret.appendUint<uint64_t>(i->second.m_maxReceive);
		}

		if(!t.m_ChangedDestinations.empty())
			log("Warning: not all route table changes were processed. "
				"It might be possible that neighbors will not be informed "
				"about the most recent route changes.\n");
	}

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
		m_myMessages.clear();
		for(uint32_t i=0; i < numMessages; i++)
			m_myMessages.push_back(data.readBinBuffer(pos));

		numMessages = data.readUint<uint32_t>(pos);
		//TODO: check whether numMessages makes sense
		m_yourMessages.clear();
		for(uint32_t i=0; i < numMessages; i++)
			m_yourMessages.push_back(data.readBinBuffer(pos));

		//TODO: transactions

		//Route table
		{
			CMutexLocker lock(m_RouteTable);
			CRouteTable &t = m_RouteTable.m_Value;

			uint32_t numEntries = data.readUint<uint32_t>(pos);
			for(uint32_t i=0; i < numEntries; i++)
			{
				CBinBuffer destination(data.readBinBuffer(pos));
				CRouteTableEntry entry;
				entry.m_minHopCount        = data.readUint<uint16_t>(pos);
				entry.m_maxSendHopCount    = data.readUint<uint16_t>(pos);
				entry.m_maxReceiveHopCount = data.readUint<uint16_t>(pos);
				entry.m_maxSend    = data.readUint<uint64_t>(pos);
				entry.m_maxReceive = data.readUint<uint64_t>(pos);
				t.updateRoute(destination, entry);
			}

			t.m_ChangedDestinations.clear();
		}
	}
	catch(CBinBuffer::CReadError &e)
	{
		throw CLoadError(CString(e.what()));
	}
}


void CFinLink::processInbox()
{
	CMutexLocker lock(m_Inbox);

	while(!m_Inbox.m_Value.empty())
	{
		CBinBuffer msgData = m_Inbox.m_Value.front();
		m_Inbox.m_Value.pop();

		CMessage *msg = NULL;
		try
		{
			msg = CMessage::constructMessage(msgData);
		}
		catch(CMessage::CSerializationError &e)
		{
			sendNackMessage(
				CNackMessage::eFormatError,
				"Message format error",
				CSHA256(msgData),
				e.what());

			//Ignore the incorrect message
			return;
		}

		//This object will take care of deleting msg:
		CPointerOwner<CMessage> messageOwner(msg);

		//Check source address
		if(msg->m_source != CRIPEMD160(
			CSHA256(getRemoteKey().getPublicKey()).toBinBuffer()
			))
		{
			sendNackMessage(
				CNackMessage::eAddressError,
				"Source address incorrect",
				CSHA256(msgData));

			//Ignore the incorrect message
			return;
		}

		//Check destination address
		if(msg->m_destination != CRIPEMD160(
			CSHA256(getLocalKey().getPublicKey()).toBinBuffer()
			))
		{
			sendNackMessage(
				CNackMessage::eAddressError,
				"Destination address incorrect",
				CSHA256(msgData));

			//Ignore the incorrect message
			return;
		}

		if(!msg->verifySignature(getRemoteKey()))
		{
			sendNackMessage(
				CNackMessage::eBadSignature,
				"Signature is incorrect",
				CSHA256(msgData));

			//Ignore the incorrect message
			return;
		}

		//TODO: ignore known messages

		if(msg->m_previousMessage != CSHA256(
			m_yourMessages.empty()? CBinBuffer() : m_yourMessages.back()
			))
		{
			sendNackMessage(
				CNackMessage::eUnknownPreviousMessage,
				"Unknown previous message",
				CSHA256(msgData));

			//Ignore the incorrect message
			return;
		}

		//Process message contents
		switch(msg->getTypeID())
		{
		case CMessage::eRouteInfo:
			processRouteInfoMessage((const CRouteInfoMessage *)msg);
			break;
		default:
			sendNackMessage(
				CNackMessage::eNonstandardReason,
				"Message type not supported",
				CSHA256(msgData));
		}

		//If all went well, we can add the message to the list:
		m_yourMessages.push_back(msgData);

		//TODO: ack if necessary

		save();
	}
}


void CFinLink::sendOutboundMessage(CMessage &msg)
{
	setOutboundMessageFields(msg);
	CBinBuffer data = msg.serialize();
	m_myMessages.push_back(data);
	try
	{
		deliverMessage(data);
	}
	catch(CComInterface::CMessageLost &e)
	{
		log("Could not send message now; "
			"will be re-sent as soon as the link is restored\n");
	}
}


void CFinLink::processRouteInfoMessage(const CRouteInfoMessage *msg)
{
	//TODO: can we completely trust route info of the peer?

	CMutexLocker lock(m_RouteTable);
	for(size_t i=0; i < msg->m_entries.size(); i++)
		m_RouteTable.m_Value.updateRoute(
			msg->m_entries[i].first, msg->m_entries[i].second);
}


void CFinLink::sendNackMessage(
	CNackMessage::eReason reasonCode,
	const CString &reason,
	const CSHA256 &rejectedMessage,
	const CString &reasonInLog)
{
	log(CString::format("Refused message on %s: %s : %s\n",
		1024,
		getBitcoinAddress(getLocalKey()).c_str(),
		reason.c_str(),
		reasonInLog.c_str()
		));

	CNackMessage nack;
	nack.m_reasonCode = reasonCode;
	nack.m_reason = reason;
	nack.m_acceptedBySource = CSHA256(
		m_yourMessages.empty()? CBinBuffer() : m_yourMessages.back()
		);
	nack.m_rejectedBySource = rejectedMessage;
	setOutboundMessageFields(nack);
	deliverMessage(nack.serialize());
}


void CFinLink::setOutboundMessageFields(CMessage &msg)
{
	msg.m_source = CRIPEMD160(
		CSHA256(getLocalKey().getPublicKey()).toBinBuffer()
		);
	msg.m_destination = CRIPEMD160(
		CSHA256(getRemoteKey().getPublicKey()).toBinBuffer()
		);

	msg.m_previousMessage = CSHA256(
		m_myMessages.empty()? CBinBuffer() : m_myMessages.back()
		);

	//TODO: timestamp

	msg.sign(getLocalKey());
}


