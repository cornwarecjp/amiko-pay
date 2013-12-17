/*
    bitcoinaddress_tests.cpp
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

#include "bitcoinaddress.h"
#include "test.h"

/*
TODO: document and expand
*/
class CBitcoinAddressTest : public CTest
{
	virtual const char *getName() const
		{return "bitcoinaddress";}

	virtual void run()
	{
		/*
		I just took some random keys from the block chain
		(thanks to blockexplorer.com for the service).
		I have no idea whose keys they are.
		*/

		//hash160 = 66750c10f3f64d0e4b8d6d80fa3d9f08cb59cdd3
		testPubKey("  The address of a public key corresponds to the known value",
			"0406e4a5c2a5f8dcfbfbadd86dd4fc908e4de1068599f2a818677f8eb0f4e375"
			"b220fb7c0845960d0ec2c11cdffa4b22dbb264e6f2e8c0b90d196985aa11cfd435",
			"1ALk99MqTNc9ifW1DhbUa8g39FTiHuyr3L"
			);

		//hash160 = 0000a21b7e708c3816f18be8cfce5f6740f94c2b
		testPubKey("  Leading zeroes are processed as required",
			"04791ee6c09049ba1c7a3db01b563d0a3ad580a4e2ce232fa7eb017ea7384194"
			"aecd156054a3186bd405363936715c6216e73980ff03f2c9eeec74ec132a32f7c4",
			"111kzsNZ1w27kSGXwyov1ZvUGVLJMvLmJ"
			);
	}

	void testPubKey(const char *testDescr, const CString &hexPubKey, const CString &address)
	{
		CBinBuffer pubkey = CBinBuffer::fromHex(hexPubKey);

		CKey key;
		key.setPublicKey(pubkey);

		test(testDescr, getBitcoinAddress(key) == address);
	}

} bitcoinAddressTest;

