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

#include <cstdio>

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


CURI::~CURI()
{
	uriFreeUriMembersA(&m_URI);
}


CString CURI::getText(const UriTextRangeA &range) const
{
	if(range.first == NULL || range.afterLast == NULL)
	{
		throw CNotFound("URI section not found");
	}

	size_t length = range.afterLast - range.first;
	size_t position = range.first - m_URIText.c_str();

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

