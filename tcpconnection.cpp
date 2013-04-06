/*
    tcpconnection.cpp
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
#include <fcntl.h>
#include <errno.h>
#include <poll.h>

#include "timer.h"

#include "tcpconnection.h"


/*
Wrapper-class of getaddrinfo functionality, to have a RAII way of dealing
with its result data structure.
*/
class CAddrInfo
{
public:
	CAddrInfo(const CString &hostname, const CString &service, const struct addrinfo &hints)
	{
		int s = getaddrinfo(hostname.c_str(), service.c_str(), &hints, &m_Info);
		if (s != 0)
			throw CTCPConnection::CConnectException(CString::format("getaddrinfo() failed: %s", 256, gai_strerror(s)));
	}

	~CAddrInfo()
	{
		freeaddrinfo(m_Info);
	}

	struct addrinfo *m_Info;
};


CTCPConnection::CTCPConnection(const CString &hostname, const CString &service)
{
	struct addrinfo hints;

	// Obtain address(es) matching host/port
	memset(&hints, 0, sizeof(struct addrinfo));
	hints.ai_family = AF_UNSPEC;     // Allow IPv4 or IPv6
	hints.ai_socktype = SOCK_STREAM; // TCP
	hints.ai_flags = 0;
	hints.ai_protocol = 0;           // Any protocol

	CAddrInfo result(hostname, service, hints);

	/*
	getaddrinfo() returns a list of address structures.
	Try each address until we successfully connect().
	If socket() (or connect()) fails, we (close the socket
	and) try the next address.
	*/
	struct addrinfo *rp;
	for(rp = result.m_Info; rp != NULL; rp = rp->ai_next)
	{
		m_FD = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
		if(m_FD == -1)
			continue;

		if(connect(m_FD, rp->ai_addr, rp->ai_addrlen) != -1)
			break; // Success

		close(m_FD);
	}

	if(rp == NULL) // No address succeeded
		throw CConnectException("Failed to connect");

	//Set non-blocking
	fcntl(m_FD, F_SETFL, O_NONBLOCK);
}


CTCPConnection::CTCPConnection(const CTCPListener &listener)
{
	//TODO: use this client info if needed
	struct sockaddr addr;
	socklen_t addrlen;

	m_FD = accept(listener.getFD(), &addr, &addrlen);
	if(m_FD == -1)
	{
		if(errno == EAGAIN || errno == EWOULDBLOCK)
			throw CTimeoutException("No incoming connection requests");

		throw CConnectException(CString::format("accept() failed: error code: %d", 256, errno));
	}

	//Set non-blocking
	fcntl(m_FD, F_SETFL, O_NONBLOCK);
}


CTCPConnection::~CTCPConnection()
{
	//TODO: check return values and log (not throw) errors
	shutdown(m_FD, SHUT_RDWR);
	close(m_FD);
}


void CTCPConnection::send(const CBinBuffer &buffer) const
{
	size_t start = 0;
	while(start < buffer.size())
	{
		ssize_t ret = write(m_FD, &(buffer[start]), buffer.size() - start);

		if(ret < 0)
			throw CSendException(CString::format("Error sending to TCP connection; error code: %d", 256, errno));

		if(ret > ssize_t(buffer.size() - start))
			throw CSendException(CString::format(
				"Error sending to TCP connection; tried to send %d bytes, but result says %d bytes were sent",
				256, buffer.size() - start, ret));

		start += ret;
	}
}


void CTCPConnection::receive(CBinBuffer &buffer, int timeout)
{
	if(m_ReceiveBuffer.size() >= buffer.size())
	{
		buffer.assign(
			m_ReceiveBuffer.begin(), m_ReceiveBuffer.begin()+buffer.size());
		m_ReceiveBuffer.erase(
			m_ReceiveBuffer.begin(), m_ReceiveBuffer.begin()+buffer.size());
		return;
	}

	uint64_t endTime = CTimer::getTime() + timeout;

	pollfd pfd;
	pfd.fd = m_FD;
	pfd.events = POLLIN | POLLPRI | POLLRDHUP;

	while(true)
	{
		//Wait for data or timeout
		uint64_t startTime = CTimer::getTime();
		int64_t dt = int64_t(endTime) - startTime;
		if(dt < 0) dt = 0; //don't wait infinitely if time has passed
		if(timeout < 0) dt = timeout; //infinite wait if requested by caller
		int poll_ret = poll(&pfd, 1, dt);
		if(poll_ret == 0)
			throw CTimeoutException("CTCPConnection::receive(CBinBuffer &, int): timeout");
		if(poll_ret < 0)
			throw CReceiveException(CString::format(
				"Error in poll(); error code: %d", 256, errno));

		CBinBuffer newBytes; newBytes.resize(buffer.size() - m_ReceiveBuffer.size());
		ssize_t read_ret = read(m_FD, &(newBytes[0]), newBytes.size());

		if(read_ret == 0)
			throw CClosedException("Unexpected close of TCP connection");

		if(read_ret < 0)
		{
			if(errno == EAGAIN || errno == EWOULDBLOCK)
				continue; //another iteration

			throw CReceiveException(CString::format(
				"Error receiving from TCP connection; error code: %d", 256, errno));
		}

		if(read_ret > ssize_t(newBytes.size()))
			throw CReceiveException("Unexpected: received more than requested");

		newBytes.resize(read_ret);
		m_ReceiveBuffer += newBytes;

		if(m_ReceiveBuffer.size() >= buffer.size())
			break;
	}

	buffer = m_ReceiveBuffer;
	m_ReceiveBuffer.clear();
}


void CTCPConnection::unreceive(const CBinBuffer &data)
{
	m_ReceiveBuffer.insert(m_ReceiveBuffer.begin(), data.begin(), data.end());
}

