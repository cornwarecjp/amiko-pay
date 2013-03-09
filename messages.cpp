/*
    messages.cpp
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

#include "messages.h"


//=====================================
CPublicKeyMessage::~CPublicKeyMessage()
{}

CBinBuffer CPublicKeyMessage::getSerializedBody() const
{return m_publicKey;}

void CPublicKeyMessage::setSerializedBody(const CBinBuffer &data)
{m_publicKey = data;}


//=====================================
CAckMessage::~CAckMessage()
{}

CBinBuffer CAckMessage::getSerializedBody() const
{return CBinBuffer();}

void CAckMessage::setSerializedBody(const CBinBuffer &data)
{}


//=====================================
CNackMessage::~CNackMessage()
{}

CBinBuffer CNackMessage::getSerializedBody() const
{
	CBinBuffer ret;
	ret.appendBinBuffer(m_rejectedBySource.toBinBuffer());
	ret.appendBinBuffer(CString(m_reason));
	return ret;
}

void CNackMessage::setSerializedBody(const CBinBuffer &data)
{
	size_t pos = 0;
	m_rejectedBySource = CSHA256::fromBinBuffer(data.readBinBuffer(pos));
	m_reason = data.readBinBuffer(pos).toString();
}


//=====================================
CFinStateMessage::~CFinStateMessage()
{}

CBinBuffer CFinStateMessage::getSerializedBody() const
{
	//TODO
	return CBinBuffer();
}

void CFinStateMessage::setSerializedBody(const CBinBuffer &data)
{
	//TODO
}


