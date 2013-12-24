/*
    paylink.cpp
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

#include "amikosettings.h"

#include "paylink.h"


CPayLink::CPayLink(const CTCPListener &listener) :
	m_connection(listener),
	m_transactionID("")
{
}


CPayLink::CPayLink(const CURI &paymentURL) :
	m_connection(paymentURL.getHost(), paymentURL.getPort(AMIKO_DEFAULT_PAYMENT_PORT)),
	m_transactionID(paymentURL.getPath())
{
}


CPayLink::~CPayLink()
{
}


void CPayLink::threadFunc()
{
	//TODO
	//Fall-through: for now, the thread stops immediately
}


