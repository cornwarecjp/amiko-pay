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


CAmikoComLink::CAmikoComLink(const CURI &uri) :
	CComLink(uri)
{
}


CAmikoComLink::CAmikoComLink(const CTCPListener &listener) :
	CComLink(listener)
{
}


CAmikoComLink::~CAmikoComLink()
{
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

