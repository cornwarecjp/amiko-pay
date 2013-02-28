/*
    tcpconnection.h
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

#ifndef TCPCONNECTION_H
#define TCPCONNECTION_H

#include <stdint.h>

#include "exception.h"
#include "cstring.h"
#include "binbuffer.h"

#include "tcplistener.h"

/*
TCP connection class, both for client and server
*/
class CTCPConnection
{
public:
	SIMPLEEXCEPTIONCLASS(CConnectException)
	SIMPLEEXCEPTIONCLASS(CReceiveException)
	SIMPLEEXCEPTIONCLASS(CSendException)

	/*
	hostname:
	Reference to properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	ASCII encoded (TODO: check whether UTF-8 is supported) (NOT CHECKED)

	service:
	Reference to properly formed CString object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	ASCII encoded (TODO: check whether UTF-8 is supported) (NOT CHECKED)
	This can be for instance a decimal port number

	Constructed object:
	Connection object, connected to TCP hostname:service

	Exceptions:
	CConnectException
	*/
	CTCPConnection(const CString &hostname, const CString &service);

	/*
	listener:
	Reference to properly formed CTCPListener object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	TODO: lifetime at least as long as lifetime of this object??

	Constructed object:
	Connection object, connected corresponding to the next connection request
	received by listener

	Exceptions:
	CConnectException
	*/
	CTCPConnection(const CTCPListener &listener);

	~CTCPConnection();

	/*
	buffer:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Function behavior:
	Sends the contents of buffer.

	Exceptions:
	CSendException
	*/
	virtual void send(const CBinBuffer &buffer) const;

	/*
	buffer:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Function behavior:
	Receives at most buffer.size() bytes.
	The received bytes are written into buffer.
	If less than buffer.size() bytes are received, buffer is resized to match
	the number of received bytes.

	Exceptions:
	CReceiveException
	*/
	virtual void receive(CBinBuffer &buffer) const;

protected:

	/*
	Return value:
	The file descriptor of the socket
	*/
	inline int getFD() const
		{return m_FD;}

private:
	int m_FD;
};

#endif


