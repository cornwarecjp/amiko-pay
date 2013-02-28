/*
    tcplistener.cpp
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
#include <cstdlib>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <unistd.h>
#include <errno.h>

#include "tcplistener.h"

/*
Wrapper-class of getaddrinfo functionality, to have a RAII way of dealing
with its result data structure.
*/
class CAddrInfo
{
public:
	CAddrInfo(const CString &service, const struct addrinfo &hints)
	{
		int s = getaddrinfo(NULL, service.c_str(), &hints, &m_Info);
		if (s != 0)
			throw CTCPListener::CConnectException(CString::format("getaddrinfo() failed: %s", 256, gai_strerror(s)));
	}

	~CAddrInfo()
	{
		freeaddrinfo(m_Info);
	}

	struct addrinfo *m_Info;
};


CTCPListener::CTCPListener(const CString &service)
{
	struct addrinfo hints;

	// Obtain address(es) matching host/port
	memset(&hints, 0, sizeof(struct addrinfo));
	hints.ai_family = AF_UNSPEC;     // Allow IPv4 or IPv6
	hints.ai_socktype = SOCK_STREAM; // TCP
	hints.ai_flags = AI_PASSIVE;     // For wildcard IP address
	hints.ai_protocol = 0;           // Any protocol
	hints.ai_canonname = NULL;
	hints.ai_addr = NULL;
	hints.ai_next = NULL;

	CAddrInfo result(service, hints);

	/*
	getaddrinfo() returns a list of address structures.
	Try each address until we successfully bind(2).
	If socket(2) (or bind(2)) fails, we (close the socket
	and) try the next address.
	*/
	struct addrinfo *rp;
	for(rp = result.m_Info; rp != NULL; rp = rp->ai_next)
	{
		m_FD = socket(rp->ai_family, rp->ai_socktype,
		rp->ai_protocol);
		if(m_FD == -1)
			continue;

		if(bind(m_FD, rp->ai_addr, rp->ai_addrlen) == 0)
			break; // Success

		close(m_FD);
	}

	if(rp == NULL) // No address succeeded
		throw CConnectException("Failed to bind to port");

	//TODO: make the '100' configurable (see listen manpage)
	if(listen(m_FD, 100) == -1)
		throw CConnectException(CString::format("listen() failed: error code: %d", 256, errno));
}


CTCPListener::~CTCPListener()
{
	close(m_FD);
}

