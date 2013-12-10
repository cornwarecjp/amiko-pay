/*
    finlink_tests.cpp
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
#include <vector>

#include "amikosettings.h"

#include "finlink.h"

#include "test.h"

/*
TODO: document and expand
*/

class CPublicFinLink : public CFinLink
{
public:
	CPublicFinLink(const CString &filename) :
		CFinLink(filename) {}

	CPublicFinLink(const CString &filename, const CKey &localKey, const CString &remoteURI) :
		CFinLink(filename, localKey, remoteURI) {}

	CBinBuffer serialize()
		{return CFinLink::serialize();}

	void deserialize(const CBinBuffer &data)
		{CFinLink::deserialize(data);}
};

class CFinLinkTest : public CTest
{
	virtual const char *getName()
		{return "finlink";}

	virtual void run()
	{
		CString filename = "./links/16JN1AMdX7h7fb7ZFwXkV8JrtmcntZoJH5";

		CBinBuffer serialized1;
		{
			CLinkConfig linkConfig;
			linkConfig.m_remoteURI = "amikolink://localhost/16JN1AMdX7h7fb7ZFwXkV8JrtmcntZoJH5";
			linkConfig.m_localKey.setPrivateKey(CBinBuffer::fromHex("3082011302010104209e3dafcee8fe2ae4f28117c03d338c3013d4e776a20f79a7b8b84a5ac7e1fc3fa081a53081a2020101302c06072a8648ce3d0101022100fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f300604010004010704410479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8022100fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141020101a14403420004b9056eb938f5d3436f2a08fa505dd3d0b5f70972ff2d44ed0d06ca5b38579d46fce8adcc2e653e6f7a8c94bce3c4b3d3082c724bb642963cfaa9f3bd608c8136"));
			linkConfig.m_remoteKey.setPublicKey(CBinBuffer::fromHex("04249e92aed4a8469afad35611eb954056439c5be71595e2838049089da69fb71796de9fc88a76af78ec57fb0f77db1383930edfc75aa9836f76577d419b6412c4"));

			CPublicFinLink f(filename, linkConfig.m_localKey, linkConfig.m_remoteURI);
			serialized1 = f.serialize();
		}

		CBinBuffer serialized2;
		{
			CPublicFinLink f(filename);
			f.deserialize(serialized1);
			serialized2 = f.serialize();
		}

		test("  serialization remains intact",
			serialized1 == serialized2);

	}
} finLinkTest;


