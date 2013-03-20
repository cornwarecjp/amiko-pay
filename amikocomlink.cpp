/*
    amikocomlink.cpp
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
#include <algorithm>

#include "log.h"

#include "amikocomlink.h"

//With 32-bit protocol version numbers, we'll never exceed this:
#define MAX_NEGOTIATION_STRING_LENGTH 32

CAmikoComLink::CAmikoComLink(const CURI &uri) :
	m_Connection(uri.getHost(), uri.getPort(AMIKO_DEFAULT_PORT)),
	m_URI(uri.getURI())
{
	m_isServerSide = false;
}


CAmikoComLink::CAmikoComLink(const CTCPListener &listener) :
	m_Connection(listener)
{
	m_isServerSide = true;
}


CComLink *CAmikoComLink::makeNewInstance(const CURI &uri)
{
	return new CAmikoComLink(uri);
}


void CAmikoComLink::registerForScheme(const CString &scheme)
{
	registerSchemeHandler(scheme, makeNewInstance);
}


void CAmikoComLink::initialize()
{
	//TODO: catch exceptions
	if(m_isServerSide)
	{
		uint32_t minVersion, maxVersion;
		receiveNegotiationString(minVersion, maxVersion);

		if(minVersion > maxVersion)
			throw CProtocolError("Protocol negotiation gave weird result");

		//Version matching
		minVersion = std::max<uint32_t>(minVersion, AMIKO_MIN_PROTOCOL_VERSION);
		maxVersion = std::min<uint32_t>(maxVersion, AMIKO_MAX_PROTOCOL_VERSION);

		if(minVersion > maxVersion)
		{
			//No matching version found
			//Inform other side
			sendNegotiationString(minVersion, maxVersion);
			throw CVersionNegotiationFailure("No matching protocol version");
		}

		//Choose the highest version supported by both parties
		m_ProtocolVersion = maxVersion;
		sendNegotiationString(m_ProtocolVersion, m_ProtocolVersion);

		log(CString::format("Connected as server with protocol version %d\n",
			1024, m_ProtocolVersion));
	}
	else
	{
		sendNegotiationString(AMIKO_MIN_PROTOCOL_VERSION, AMIKO_MAX_PROTOCOL_VERSION);

		uint32_t minVersion, maxVersion;
		receiveNegotiationString(minVersion, maxVersion);

		if(minVersion < AMIKO_MIN_PROTOCOL_VERSION || maxVersion > AMIKO_MAX_PROTOCOL_VERSION)
			throw CProtocolError("Peer returned illegal protocol negotiation result");

		if(minVersion < maxVersion)
			throw CProtocolError("Protocol negotiation gave weird result");

		if(minVersion > maxVersion)
			throw CVersionNegotiationFailure("No matching protocol version");

		m_ProtocolVersion = minVersion;
		log(CString::format("Connected as client to %s with protocol version %d\n",
			1024, m_URI.c_str(), m_ProtocolVersion));
	}
}


void CAmikoComLink::sendNegotiationString(uint32_t minVersion, uint32_t maxVersion)
{
	m_Connection.send(CBinBuffer(
		CString::format(
			"AMIKOPAY/%d/%d\n", MAX_NEGOTIATION_STRING_LENGTH,
			minVersion, maxVersion
			)
		));
}


void CAmikoComLink::receiveNegotiationString(uint32_t &minVersion, uint32_t &maxVersion)
{
	//TODO: more efficient than one-byte-at-a-time

	CString receivedString;
	CBinBuffer buf(1);
	bool finished = false;

	for(unsigned int i=0; i < MAX_NEGOTIATION_STRING_LENGTH; i++)
	{
		m_Connection.receive(buf, -1); //TODO: set time-out on receiving
		unsigned char c = buf[0];

		if(c == '\n')
		{
			finished = true;
			break;
		}

		if(c < '/' || c > 'Z')
			throw CProtocolError(
				"Illegal character in protocol negotiation");

		receivedString += c;
	}

	if(!finished)
		throw CProtocolError(
			"Received protocol negotiation exceeds maximum length");

	size_t slash1 = receivedString.find('/', 0);
	if(slash1 == std::string::npos || slash1 >= receivedString.length()-1)
		throw CProtocolError(
			"Protocol negotiation syntax error: first slash not found");

	size_t slash2 = receivedString.find('/', slash1+1);
	if(slash2 == std::string::npos || slash2 >= receivedString.length()-1)
		throw CProtocolError(
			"Protocol negotiation syntax error: second slash not found");

	CString protocolName = receivedString.substr(0, slash1);
	CString minVerStr = receivedString.substr(slash1+1, slash2-slash1-1);
	CString maxVerStr = receivedString.substr(slash2+1);

	if(protocolName != "AMIKOPAY")
		throw CProtocolError(
			"Protocol name mismatch");

	if(minVerStr.length() > 9)
		throw CProtocolError(
			"Received minimum version number is close to or above integer overflow");

	if(maxVerStr.length() > 9)
		throw CProtocolError(
			"Received maximum version number is close to or above integer overflow");

	minVersion = minVerStr.parseAsDecimalInteger();
	maxVersion = maxVerStr.parseAsDecimalInteger();
}


void CAmikoComLink::sendMessageDirect(const CBinBuffer &message)
{
	//TODO: check whether everything fits in the integer data types
	CBinBuffer sizebuffer;
	sizebuffer.appendUint<uint32_t>(message.size());
	m_Connection.send(sizebuffer);
	m_Connection.send(message);
}

CBinBuffer CAmikoComLink::receiveMessageDirect()
{
	CBinBuffer sizebuffer(4);
	try
	{
		m_Connection.receive(sizebuffer, 0); //immediate time-out
	}
	catch(CTCPConnection::CTimeoutException &e)
	{
		throw CNoDataAvailable("Timeout when reading size");
	}

	size_t pos = 0;
	uint32_t size = sizebuffer.readUint<uint32_t>(pos);

	//TODO: check whether size is unreasonably large
	CBinBuffer ret; ret.resize(size);

	try
	{
		m_Connection.receive(ret, 0); //immediate time-out
	}
	catch(CTCPConnection::CTimeoutException &e)
	{
		/*
		If receiving the message body gives a timeout, then we have to put
		back the size data, so it can be re-read the next time this method is
		called.
		*/
		m_Connection.unreceive(sizebuffer);
		throw CNoDataAvailable("Timeout when reading message body");
	}

	return ret;
}

