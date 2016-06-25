Introduction
============
Due to the fact that Amiko Pay is experimental and unfinished software,
a lot of analysis on its security has not yet been performed. Even the most
basic types of testing, such as an automated set of unit tests with full code
coverage, are still mostly missing. Because of this, you should expect Amiko Pay
to contain several unknown vulnerabilities, which may lead to worse consequences
than the ones listed below (e.g. they might lead to arbitrary code execution
with the privileges of the Amiko Pay process).

Therefore, the list below is far from exhaustive. At the present state of
development, the list below is mainly composed of issues related to
not-yet-implemented security features and to design issues.


General issues (e.g. arbitrary code execution)
==============================================

No checks on type and structure of incoming messages
----------------------------------------------------
For incoming message data, any message type and any type of attributes
(and sub-elements of composed data types) is accepted. It is unknown whether
this can be abused by an attacker to change the state of an Amiko Pay node in an
undesired way, or even to trigger arbitrary code execution.


Loss of Bitcoins
=================

No real microtransaction channel yet
------------------------------------
Currently, Amiko Pay only contains an "IOU" channel, which exchanges IOUs
issued by one of the two parties. On closing the channel, the IOU issuing
party should perform a Bitcoin transaction to settle the final balance of the
IOU channel. However, this can not be enforced by technological means, so the
IOU issuing party can choose not to do this. As a result, the IOU issuing party
can steal his direct neighbor's balance in a channel, simply by disappearing
without settling the channel balance.

**solution**: implement a proper Lightning channel.


Links accept creation of all types of channels
----------------------------------------------
In particular, a link accepts creation of new channels that trade IOUs issued
by the peer. This makes all links vulnerable to the inherent vulnerability of
IOU channels.

**solution**: implement a (configurable) filter of acceptable new channel types.


No transaction checks
---------------------
Certain checks on transactions exchanged by neighbors are not yet implemented.
As a result, an attacker can not only steal bitcoins from a direct neighbor
(because of the inherent IOU vulnerability), but also hide the fact that the
bitcoins were stolen (it is not visible in the Amiko Pay user interface).

**solution**: implement the missing functionality.


No payment channel token check
------------------------------
A payer does not yet check the validity of the token received by the payee on
commit. As a result, an attacking payee can trick the payer into releasing the
payment amount to the payer's first neighbor in the transaction route. If the
token is used as proof of payment, the payer does not have a valid proof, so the
payee can claim the transaction has failed, and refuse to transfer corresponding
goods/services.

**solution**: implement the missing functionality.


Blocking of time-out events
---------------------------
It might be possible for an attacker to send so many messages to a node that the
node is kept completely busy processing network messages, and will not process
its time-out events. The possible results are currently not well analyzed.

**solution**: always give priority to local events (like time-outs) over
network events.


Loss of privacy
===============

No encrypted communication
--------------------------
Communication takes place over non-encrypted TCP connections. As a result, an
attacker who has access to network traffic can see which transactions
(transaction tokens and amounts) take place between a user and his neighbors.
This is also true for the payment link between payer and payee. An attacker who
has access to network traffic of all links in a transaction route can see which
nodes send which transactions (including amounts) to which nodes. The receipt is
also visible, since it's sent over the non-encrypted payment link between payer
and payee.

**solution**: implement the missing functionality.


No link authentication
----------------------
When an incoming link connection arrives, the neighbor is not authenticated.
As a result, an attacker who knows the URL of a link of a node can connect to
that node, pretending to be the other side of the link. The node then
incorrectly believes to be connected, and does not attempt to connect to its
real neigbor. The attacker can then perform a Denial of Service on all
operations that involve the link; also, all operations that are attempted by the
node may reveal information to the attacker, leading to a loss of privacy.

If an attacker knows the URLs of both sides of the link, the attacker can
connect to both sides of the link, and position himself as a man-in-the-middle.
This is even possible by an attacker who has no lower-level methods of
re-routing traffic, such as influencing IP routing or changing DNS responses.

**solution**: implement the missing functionality.


Denial of Service
=================

Meeting point ID spoofing
-------------------------
There is no method for guaranteeing meeting point ID uniqueness; when two nodes
use the same meeting point ID on the same network, transactions which route
towards that ID can fail to find a route. As a result, an attacker can make
transaction routing on the Amiko network unreliable.

**solution**: ICANN-style assignment of meeting point IDs is considered
unacceptable, since it introduces a central authority. IDs might be linked to
identities through digital signatures. If a route requires meeting point
signatures, then intermediate nodes can detect and work around routing problems.


Unreasonable time-out values
----------------------------
Amiko Pay does not yet put boundaries on incoming time-out values. As a result,
an attacker can keep funds locked for an arbitrarily long amount of time.

**solution**: put a limit on incoming time-out values.


Unlimited creation of new channels
----------------------------------
A peer can repeatedly request a node to create a new channel, and the node will
always comply. As a result, when this process is repeated at a fast pace, so
many channels can be created that a node will be severely slowed down, or even
run out of memory.

**solution**: limit the number of channels in a link.


Unlimited message buffer size
-----------------------------
A peer can send data to a node, without ever sending the message separator
character (newline). The node will store all this data in memory. As a result, a
direct neighbor of a node can create an out of memory situation.

**solution**: limit the size of the message buffer.

