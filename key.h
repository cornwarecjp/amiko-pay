/*
    key.h
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

#ifndef KEY_H
#define KEY_H

#include <openssl/ec.h>

#include "exception.h"
#include "binbuffer.h"
#include "sha256.h"

/*
Contains public key, private key or both
*/
class CKey
{
public:
	SIMPLEEXCEPTIONCLASS(CConstructError)
	SIMPLEEXCEPTIONCLASS(CKeyError)

	/*
	Constructed object:
	Empty key object

	Exceptions:
	CConstructError
	*/
	CKey();

	/*
	b:
	Reference to properly formed CKey object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	Copy of b

	Exceptions:
	CConstructError
	*/
	CKey(const CKey &b);

	~CKey();

	/*
	b:
	Reference to properly formed CKey object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	Reference to this object

	Exceptions:
	CKeyError
	*/
	CKey &operator=(const CKey& b);

	/*
	Exceptions:
	CKeyError
	*/
	void makeNewKey();

	/*
	key:
	Reference to properly formed CBinBuffer object
	Reference lifetime: at least until the end of this function

	Exceptions:
	CKeyError
	*/
	void setPublicKey(const CBinBuffer &key);

	/*
	This object:
	Contains a public key (NOT CHECKED/TODO)

	Return value:
	CBinBuffer object
	Contains a copy of the public key

	Exceptions:
	CKeyError
	*/
	CBinBuffer getPublicKey() const;

	/*
	key:
	Reference to properly formed CBinBuffer object
	Reference lifetime: at least until the end of this function

	Exceptions:
	CKeyError
	*/
	void setPrivateKey(const CBinBuffer &key);

	/*
	This object:
	Contains a private key (CHECKED/TODO)

	Return value:
	CBinBuffer object
	Contains a copy of the private key

	Exceptions:
	CKeyError
	*/
	CBinBuffer getPrivateKey() const;

	/*
	This object:
	Contains a private key (CHECKED/TODO)

	hash:
	Reference to properly formed CSHA256 object
	Reference lifetime: at least until the end of this function

	Return value:
	CBinBuffer object
	Contains the signature of this key of hash

	Exceptions:
	CKeyError
	*/
	CBinBuffer sign(const CSHA256 &hash) const;

	/*
	This object:
	Contains a public key (CHECKED/TODO)

	hash:
	Reference to properly formed CSHA256 object
	Reference lifetime: at least until the end of this function

	signature:
	Reference to properly formed CBinBuffer object
	Reference lifetime: at least until the end of this function

	Return value:
	true if the signature is valid
	false if the signature is invalid

	Exceptions:
	CKeyError
	*/
	bool verify(const CSHA256 &hash, const CBinBuffer &signature) const;

private:

	//TODO: secure memory allocation
    EC_KEY *m_KeyData;
};

#endif

