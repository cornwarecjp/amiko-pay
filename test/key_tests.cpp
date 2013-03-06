/*
    key_tests.cpp
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

#include "key.h"

#include "test.h"

/*
TODO: document and expand
*/
class CKeyTest : public CTest
{
	virtual void run()
	{
		CKey privKey;
		privKey.makeNewKey();
		CKey pubKey;
		pubKey.setPublicKey(privKey.getPublicKey());

		CBinBuffer data("blablabla");
		CBinBuffer goodSig = privKey.sign(data);

		CKey otherKey;
		otherKey.makeNewKey();
		CBinBuffer badSig1 = otherKey.sign(data);

		CBinBuffer badSig2 = privKey.sign(CBinBuffer("bad data"));

		if(pubKey.verify(data, goodSig))
			{printf("test 1: ok\n");}
		else
			{printf("test 1: not ok\n");}

		if(!pubKey.verify(data, badSig1))
			{printf("test 2: ok\n");}
		else
			{printf("test 2: not ok\n");}

		if(!pubKey.verify(data, badSig2))
			{printf("test 3: ok\n");}
		else
			{printf("test 3: not ok\n");}
	}
} keyTest;

