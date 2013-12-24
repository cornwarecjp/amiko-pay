/*
    paylink.h
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

#ifndef PAYLINK_H
#define PAYLINK_H

#include <stdint.h>

#include "tcpconnection.h"
#include "cthread.h"
#include "transaction.h"

#include "uriparser.h"


/*
A PayLink object received payments from a remote payer.
It contains its own thread which manages sending and receiving of messages.
*/
class CPayLink : public CThread
{
public:
	/*
	listener:
	Reference to properly formed CTCPListener object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	TODO: lifetime at least as long as lifetime of this object??

	Constructed object:
	TODO

	Exceptions:
	CTCPConnection::CConnectException
	CTCPConnection::CTimeoutException
	*/
	CPayLink(const CTCPListener &listener);

	/*
	paymentURL:
	Reference to properly formed CURI object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	TODO

	Exceptions:
	CTCPConnection::CConnectException
	CURI::CNotFound
	CString::CFormatException
	*/
	CPayLink(const CURI &paymentURL);

	~CPayLink();

	void threadFunc();

private:
	CTCPConnection m_connection;
	CString m_transactionID;
};

#endif

