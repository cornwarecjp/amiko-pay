#    bitcointransaction.py
#    Copyright (C) 2014 by CJP
#
#    This file is part of Amiko Pay.
#
#    Amiko Pay is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Amiko Pay is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.

"""
See multisigchannel.py.
For now, we need support for transactions with the following:

Bitcoin standard:
	ScriptPubKey: OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
	ScriptSig:    <sig> <pubKey>

2-of-2 multisig:
	ScriptPubKey: 2 <pubKey1> <pubKey2> 2 CHECKMULTISIGVERIFY
	ScriptSig:    <sig1> <sig2>

Signature and secret:
	ScriptPubKey: <pubKey> CHECKSIGVERIFY SHA256 <secretHash> EQUALVERIFY
	ScriptSig:    <secret> <sig>
"""



class BitcoinTransaction:
	pass #TODO

