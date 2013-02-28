/*
    tcplistener.h
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

#ifndef TCPLISTENER_H
#define TCPLISTENER_H

#include <stdint.h>

#include "exception.h"
#include "cstring.h"
#include "binbuffer.h"

/*
TCP listener class: listens for incoming connection requests
*/
class CTCPListener
{
public:
	SIMPLEEXCEPTIONCLASS(CConnectException)

	/*
	service:
	Reference to properly formed CString object (NOT CHECKED)
	ASCII encoded (TODO: check whether UTF-8 is supported) (NOT CHECKED)
	This can be for instance a decimal port number

	Constructed object:
	TCP listener object,
	listening for incoming TCP connection requests on port number indicated by service

	Exceptions:
	CConnectException
	*/
	CTCPListener(const CString &service);

	~CTCPListener();

	friend class CTCPConnection;

protected:

	/*
	Return value:
	The file descriptor of the socket

	Exceptions:
	none
	*/
	inline int getFD() const throw()
		{return m_FD;}

private:
	int m_FD;
};

#endif


