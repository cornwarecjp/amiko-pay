#    multisigchannel.py
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

import channel
import bitcointransaction

"""
We use a variation of the following. The variation basically consists of having
outputs that depend on having the transaction token, of which the hash is in a
scriptPubKey.

https://en.bitcoin.it/wiki/Contracts#Example_7:_Rapidly-adjusted_.28micro.29payments_to_a_pre-determined_party

This protocol relies upon a different behavior of nLockTime to the original
design. Starting around 2013 time-locked transactions were made non standard
and no longer enter the memory pool, thus cannot be broadcast before the
timelock expires. When the behaviour of nLockTime is restored to the original
design from Satoshi, a variant of this protocol is required which is discussed
below.

We define the client to be the party sending value, and the server to be the
party receiving it. This is written from the clients perspective.

1	Create a public key (K1). Request a public key from the server (K2).
2	Create and sign but do not broadcast a transaction (T1) that sets up a
	payment of (for example) 10 BTC to an output requiring both the server's
	private key and one of your own to be used. A good way to do this is use
	OP_CHECKMULTISIG. The value to be used is chosen as an efficiency tradeoff.
3	Create a refund transaction (T2) that is connected to the output of T1 which
	sends all the money back to yourself. It has a time lock set for some time
	in the future, for instance a few hours. Don't sign it, and provide the
	unsigned transaction to the server. By convention, the output script is
	"2 K1 K2 2 CHECKMULTISIG"
4	The server signs T2 using its private key associated with K2 and returns the
	signature to the client. Note that it has not seen T1 at this point, just
	the hash (which is in the unsigned T2).
5	The client verifies the servers signature is correct and aborts if not.
6	The client signs T1 and passes the signature to the server, which now
	broadcasts the transaction (either party can do this if they both have
	connectivity). This locks in the money.
7	The client then creates a new transaction, T3, which connects to T1 like the
	refund transaction does and has two outputs. One goes to K1 and the other
	goes to K2. It starts out with all value allocated to the first output (K1),
	ie, it does the same thing as the refund transaction but is not time locked.
	The client signs T3 and provides the transaction and signature to the
	server.
8	The server verifies the output to itself is of the expected size and
	verifies the client's provided signature is correct.
9	When the client wishes to pay the server, it adjusts its copy of T3 to
	allocate more value to the server's output and less to its own. It then
	re-signs the new T3 and sends the signature to the server. It does not have
	to send the whole transaction, just the signature and the amount to
	increment by is sufficient. The server adjusts its copy of T3 to match the
	new amounts, verifies the signature and continues.

This continues until the session ends, or the 1-day period is getting close to
expiry. The AP then signs and broadcasts the last transaction it saw, allocating
the final amount to itself. The refund transaction is needed to handle the case
where the server disappears or halts at any point, leaving the allocated value
in limbo. If this happens then once the time lock has expired the client can
broadcast the refund transaction and get back all the money.

[..]

When nLockTime'd transactions are able to enter the memory pool (once more) and
transaction replacement has been re-enabled, a variant on the protocol must be
used. In this case, no refund transaction is used. Instead each T3 has a
sequence number one higher than the previous and all T3's have a time lock set
to the same period as above. Each time a payment is made the sequence number is
incremented, ensuring that the last version will take precedence. If the channel
protocol is not closed cleanly, this means the value transfer won't commit until
the time lock expires. To avoid this both parties can cooperate by signing a T3
that has a sequence number of 0xFFFFFFFF resulting in immediate confirmation
regardless of the value of nLockTime.

The lock time and sequence numbers avoid an attack in which the AP provides
connectivity, and then the user double-spends the output back to themselves
using the first version of TX2, thus preventing the cafe from claiming the bill.
If the user does try this, the TX won't be included right away, giving the
access point a window of time in which it can observe the TX broadcast, and then
broadcast the last version it saw, overriding the user's attempted double-spend.

The latter protocol that relies on transaction replacement is more flexible
because it allows the value allocated to go down as well as up during the
lifetime of the channel as long as the client receives signatures from the
server, but for many use cases this functionality is not required. Replacement
also allows for more complex configurations of channels that involve more than
two parties. Elaboration on such use cases is a left as an exercise for the
reader. 
"""



class MultiSigChannel(channel.Channel):
	"""
	Payment channel with Bitcoin multi-signature transaction protection.
	"""

	def __init__(self, state):
		channel.Channel.__init__(self, state)


	def getType(self):
		return "multisig"



def constructFromDeposit(amount):
	state = \
	{
    "amountLocal" : amount,
    "amountRemote": 0,
    "transactionsIncomingLocked"  : {},
    "transactionsIncomingReserved": {},
    "transactionsOutgoingLocked"  : {},
    "transactionsOutgoingReserved": {}
	}
	return MultiSigChannel(state)
