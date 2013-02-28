/*
    tlsconnection.h
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

#ifndef TLS_CONNECTION_H
#define TLS_CONNECTION_H

#include <openssl/ssl.h>

#include "tcpconnection.h"

/*
A TLS-protected connection
*/
class CTLSConnection : public CTCPConnection
{
public:

	/*
	hostname:
	Reference to properly formed CString object (NOT CHECKED)
	ASCII encoded (TODO: check whether UTF-8 is supported) (NOT CHECKED)

	service:
	Reference to properly formed CString object (NOT CHECKED)
	ASCII encoded (TODO: check whether UTF-8 is supported) (NOT CHECKED)
	This can be for instance a decimal port number

	Constructed object:
	TLS connection object, connected to TCP hostname:service
	*/
	CTLSConnection(const CString &hostname, const CString &service)
		throw(CTCPConnection::CConnectException);

	/*
	listener:
	Reference to properly formed CTCPListener object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	TODO: lifetime at least as long as lifetime of this object??

	Constructed object:
	TLS Connection object, connected corresponding to the next connection
	request received by listener
	*/
	CTLSConnection(const CTCPListener &listener)
		throw(CTCPConnection::CConnectException);

	~CTLSConnection() throw();

	/*
	buffer:
	Reference to properly formed CBinBuffer object (NOT CHECKED)

	Function behavior:
	Sends the contents of buffer.
	*/
	virtual void send(const CBinBuffer &buffer) const
		throw(CTCPConnection::CSendException);

	/*
	buffer:
	Reference to properly formed CBinBuffer object (NOT CHECKED)

	Function behavior:
	Receives at most buffer.size() bytes.
	The received bytes are written into buffer.
	If less than buffer.size() bytes are received, buffer is resized to match
	the number of received bytes.
	*/
	virtual void receive(CBinBuffer &buffer) const
		throw(CTCPConnection::CReceiveException);

private:

	void initialize() throw(CTCPConnection::CConnectException);
	void deallocate() throw();

	/*
	ret:
	return value of an openSSL function, as accepted by SSL_get_error

	Returned value:
	CString object, containin error message corresponding to ret
	*/
	CString getError(int ret) const throw();

	/*
	We have a different context object for each connection.
	TODO: find out whether this is a good idea.
	*/
	SSL_CTX *m_TLSContext;
	SSL *m_TLSConnection;
};

#endif


