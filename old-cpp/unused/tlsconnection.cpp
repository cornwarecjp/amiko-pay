/*
    tlsconnection.cpp
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

#include <openssl/err.h>

#include "tlsconnection.h"

CTLSConnection::CTLSConnection(const CString &hostname, const CString &service)
	throw(CTCPConnection::CConnectException)
	: CTCPConnection(hostname, service),
		m_TLSContext(NULL), m_TLSConnection(NULL)
{
	initialize();

	int ret = SSL_connect(m_TLSConnection);
	if(ret == 0)
	{
		deallocate();
		throw CConnectException(CString(
			"TLS handshake failed: ") + getError(ret));
	}
	if(ret < 0)
	{
		deallocate();
		throw CConnectException(CString(
			"TLS handshake failed because of protocol error or connection failure: "
			) + getError(ret));
	}
	if(ret != 1)
	{
		deallocate();
		throw CConnectException(CString::format(
			"TLS handshake returned unknown return value %d", 256, ret));
	}

	SSL_set_connect_state(m_TLSConnection);
}


CTLSConnection::CTLSConnection(const CTCPListener &listener)
	throw(CTCPConnection::CConnectException)
	: CTCPConnection(listener),
		m_TLSContext(NULL), m_TLSConnection(NULL)
{
	initialize();

	int ret = SSL_accept(m_TLSConnection);
	if(ret == 0)
	{
		deallocate();
		throw CConnectException(CString(
			"TLS handshake failed: ") + getError(ret));
	}
	if(ret < 0)
	{
		deallocate();
		throw CConnectException(CString(
			"TLS handshake failed because of protocol error or connection failure: "
			) + getError(ret));
	}
	if(ret != 1)
	{
		deallocate();
		throw CConnectException(CString::format(
			"TLS handshake returned unknown return value %d", 256, ret));
	}

	SSL_set_accept_state(m_TLSConnection);
}


void CTLSConnection::initialize() throw(CTCPConnection::CConnectException)
{
	//Use ONLY TLS 1.1: this is the latest version supported by libssl
	m_TLSContext = SSL_CTX_new(TLSv1_1_method());
	if(m_TLSContext == NULL)
	{
		deallocate();
		throw CConnectException(
			"Failed to create a new SSL/TLS context");
	}

	SSL_CTX_set_options(m_TLSContext,
		SSL_OP_SINGLE_DH_USE | //docs seem to indicate this improves security
		SSL_OP_NO_SSLv2 | //do not use old SSL v2 protocol
		SSL_OP_NO_SSLv3 | //do not use old SSL v3 protocol
		SSL_OP_NO_TLSv1 | //do not use old TLS v1.0 protocol
		SSL_MODE_AUTO_RETRY //send and receive implementations depend on this
		); //TODO

	m_TLSConnection = SSL_new(m_TLSContext);
	if(m_TLSConnection == NULL)
	{
		deallocate();
		throw CConnectException(
			"Failed to create a new SSL/TLS connection structure");
	}

	//TODO:
	if(!SSL_set_fd(m_TLSConnection, getFD()))
	{
		deallocate();
		throw CConnectException(
			"Failed to connect SSL/TLS object to file descriptor");
	}
}


CTLSConnection::~CTLSConnection() throw()
{
	//sends "close notify"
	int ret = SSL_shutdown(m_TLSConnection);

	//use bidirectional shutdown
	if(ret == 0) ret = SSL_shutdown(m_TLSConnection);

	//TODO: log error messages BUT DO NOT THROW EXCEPTIONS
	// in the following cases:
	//ret==-1 -> "TLS shutdown failed because of protocol error or connection failure"
	//ret!=1 -> "TLS shutdown returned unknown return value %d", ret
	//note: exception throwing in destructors is extremely dangerous:
	//http://www.parashift.com/c++-faq-lite/dtors-shouldnt-throw.html

	deallocate();
}


void CTLSConnection::deallocate() throw()
{
	if(m_TLSConnection != NULL) SSL_free(m_TLSConnection);
	m_TLSConnection = NULL;

	if(m_TLSContext != NULL) SSL_CTX_free(m_TLSContext);
	m_TLSContext = NULL;
}


void CTLSConnection::send(const CBinBuffer &buffer) const
	throw(CTCPConnection::CSendException)
{
	size_t start = 0;
	while(start < buffer.size())
	{
		int ret = SSL_write(m_TLSConnection,
			&(buffer[start]), int(buffer.size() - start));

		if(ret <= 0)
			//TODO: get detailed error info
			throw CSendException(CString::format(
				"Error sending to TLS connection; error code: %d", 256, ret));

		if(ret > ssize_t(buffer.size() - start))
			throw CSendException(CString::format(
				"Error sending to TLS connection; tried to send %d bytes, but result says %d bytes were sent",
				256, buffer.size() - start, ret));

		start += ret;
	}
}


void CTLSConnection::receive(CBinBuffer &buffer) const
	throw(CTCPConnection::CReceiveException)
{
	int ret = SSL_read(m_TLSConnection, &(buffer[0]), int(buffer.size()));

	if(ret == 0)
		//TODO: get detailed error info
		throw CReceiveException("Unexpected close of TLS connection");

	if(ret < 0)
		//TODO: get detailed error info
		throw CReceiveException(CString::format("Error receiving from TLS connection; error code: %d", 256, ret));

	if(ret < int(buffer.size()))
		buffer.resize(ret);
}


CString CTLSConnection::getError(int ret) const throw()
{
	//TODO: find a better place for error logging
	// (e.g. at the end of every function)
	while(unsigned long error = ERR_get_error() != 0)
	{
		char *errString = ERR_error_string(error, NULL);
		printf("TLS error: %s\n", errString);
	}
	printf("End of TLS errors");

	int error = SSL_get_error(m_TLSConnection, ret);
	switch(error)
	{
	case SSL_ERROR_NONE:
		return "SSL_ERROR_NONE: The TLS/SSL I/O operation completed.";
		break;
	case SSL_ERROR_ZERO_RETURN:
		return "SSL_ERROR_ZERO_RETURN: The TLS/SSL connection has been closed.";
		break;
	case SSL_ERROR_WANT_READ:
		return "SSL_ERROR_WANT_READ: The operation did not complete.";
		break;
	case SSL_ERROR_WANT_WRITE:
		return "SSL_ERROR_WANT_WRITE: The operation did not complete.";
		break;
	case SSL_ERROR_WANT_CONNECT:
		return "SSL_ERROR_WANT_CONNECT: The operation did not complete.";
		break;
	case SSL_ERROR_WANT_ACCEPT:
		return "SSL_ERROR_WANT_ACCEPT: The operation did not complete.";
		break;
	case SSL_ERROR_WANT_X509_LOOKUP:
		return "SSL_ERROR_WANT_X509_LOOKUP: The operation did not complete "
			"because an application callback set by SSL_CTX_set_client_cert_cb() "
			"has asked to be called again.";
		break;
	case SSL_ERROR_SYSCALL:
		return "SSL_ERROR_SYSCALL: Some I/O error occurred.";
		break;
	case SSL_ERROR_SSL:
		return "SSL_ERROR_SSL: A failure in the SSL library occurred, usually a protocol error.";
		break;
	}

	return CString::format("Unknown error code %d", 256, error);
}


