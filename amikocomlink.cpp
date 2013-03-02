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

#include "amikocomlink.h"

//With 32-bit protocol version numbers, we'll never exceed this:
#define MAX_NEGOTIATION_STRING_LENGTH 32

CAmikoComLink::CAmikoComLink(const CURI &uri)
	: m_Connection(uri.getHost(), uri.getPort(AMIKO_DEFAULT_PORT))
{
	//TODO: catch exceptions

	sendNegotiationString(AMIKO_MIN_PROTOCOL_VERSION, AMIKO_MAX_PROTOCOL_VERSION);

	uint32_t minVersion, maxVersion;
	receiveNegotiationString(minVersion, maxVersion);

	if(minVersion > maxVersion)
		throw CVersionNegotiationFailure("No matching protocol version");

	if(minVersion < maxVersion)
		throw CProtocolError("Protocol negotiation gave weird result");

	//TODO: remember protocol version
}


CAmikoComLink::CAmikoComLink(const CTCPListener &listener)
	: m_Connection(listener)
{
	//TODO: catch exceptions

	uint32_t minVersion, maxVersion;
	receiveNegotiationString(minVersion, maxVersion);

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
	//TODO: remember protocol version
	sendNegotiationString(maxVersion, maxVersion);
}


CLink *CAmikoComLink::makeNewInstance(const CURI &uri)
{
	return new CAmikoComLink(uri);
}


void CAmikoComLink::registerForScheme(const CString &scheme)
{
	registerSchemeHandler(scheme, makeNewInstance);
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
	CString receivedString;
	CBinBuffer buf; buf.resize(1);
	bool finished = false;

	for(unsigned int i=0; i < MAX_NEGOTIATION_STRING_LENGTH; i++)
	{
		m_Connection.receive(buf);
		if(buf.size() != 1)
			throw CProtocolError(
				"Error receiving protocol negotiation");

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



