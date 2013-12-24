/*
    uriparser.cpp
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

#include "log.h"

#include "uriparser.h"

CURI::CURI(const CString &uri)
	: m_URIText(uri)
{
	UriParserStateA state;
	state.uri = &m_URI;
	if (uriParseUriA(&state, m_URIText.c_str()) != URI_SUCCESS)
	{
		//TODO: maybe free some structures?
		throw CParseFailure("Failed to parse URI");
	}
}


CURI::CURI(const CURI &uri)
	: m_URIText(uri.getURI())
{
	UriParserStateA state;
	state.uri = &m_URI;
	if (uriParseUriA(&state, m_URIText.c_str()) != URI_SUCCESS)
	{
		//Note: this code path should never be triggered
		//TODO: maybe free some structures?
		throw CParseFailure("Failed to parse URI in copy constructor");
	}
}


CURI::~CURI()
{
	uriFreeUriMembersA(&m_URI);
}


const CURI &CURI::operator=(const CURI &uri)
{
	uriFreeUriMembersA(&m_URI);

	m_URIText = uri.getURI();
	UriParserStateA state;
	state.uri = &m_URI;
	if (uriParseUriA(&state, m_URIText.c_str()) != URI_SUCCESS)
	{
		//Note: this code path should never be triggered
		//TODO: maybe free some structures?
		throw CParseFailure("Failed to parse URI in assignment operator");
	}

	return *this;
}


CString CURI::getText(const UriTextRangeA &range) const
{
	if(range.first == NULL || range.afterLast == NULL)
		throw CNotFound("URI section not found");

	size_t length = range.afterLast - range.first;
	size_t position = range.first - m_URIText.c_str();

	//This special case is necessary because sometimes, when an URI section
	//is present but empty, liburiparser returns strange ranges
	if(length == 0)
		return "";

	CString ret;
	ret.assign(m_URIText, position, length);
	return ret;
}


CString CURI::getText(const UriTextRangeA &range, const CString &dflt) const
{
	try
	{
		return getText(range);
	}
	catch(CNotFound &e)
	{} //ignore exception and fall through

	return dflt;
}


CString CURI::getText(const UriPathSegmentA *head, const UriPathSegmentA *tail) const
{
	if(head == NULL || tail == NULL)
		throw CNotFound("URI section not found");

	UriTextRangeA range;
	range.first = head->text.first;
	range.afterLast = tail->text.afterLast;
	return getText(range);
}

