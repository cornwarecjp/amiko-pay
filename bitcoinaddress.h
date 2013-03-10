/*
    bitcoinaddress.h
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

#ifndef BITCOINADDRESS_H
#define BITCOINADDRESS_H

#include "key.h"
#include "sha256.h"

CString getBitcoinAddress(const CSHA256 &hashedPublicKey);

inline CString getBitcoinAddress(const CBinBuffer &publicKey)
{
	return getBitcoinAddress(CSHA256(publicKey));
}

inline CString getBitcoinAddress(const CKey &key)
{
	return getBitcoinAddress(key.getPublicKey());
}

#endif

