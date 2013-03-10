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
	virtual const char *getName()
		{return "bitcoinaddress";}

	virtual void run()
	{
		/*
		I just took some random key from the block chain
		(thanks to blockexplorer.com for the service).
		I have no idea whose key this is.
		*/

		//address = 1ALk99MqTNc9ifW1DhbUa8g39FTiHuyr3L
		//hash160 = 66750c10f3f64d0e4b8d6d80fa3d9f08cb59cdd3
		CBinBuffer pubkey = CBinBuffer::fromHex(
			"0406e4a5c2a5f8dcfbfbadd86dd4fc908e4de1068599f2a818677f8eb0f4e375"
			"b220fb7c0845960d0ec2c11cdffa4b22dbb264e6f2e8c0b90d196985aa11cfd435"
			);

		CKey key;
		key.setPublicKey(pubkey);

		CString address = getBitcoinAddress(key);
		test("  The address of a public key corresponds to the known value",
			address == "1ALk99MqTNc9ifW1DhbUa8g39FTiHuyr3L");
	}

} bitcoinAddressTest;

