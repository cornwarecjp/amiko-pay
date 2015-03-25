Transaction structure
=====================

	           RA1 - Alice
	          /
	    |- CA1
	    |     \
	    |       Bob
	F - |
	    |      RB1 - Bob
	    |     /
	    |- CB1
	          \
	            Alice


_Funding (F)_
- in: from Alice
- in: from Bob
- out 0: 2-of-2 Alice+Bob


_Commit by Alice (CA1)_
- in: F[0]
- out 0: 2-of-2 Alice+Bob
- out 1: Bob


_Commit by Bob (CB1)_
- in: F[0]
- out 0: 2-of-2 Alice+Bob
- out 1: Alice


_Refund to Alice (RA1)_
- in: CA1[0]
- out: Alice
- 40-day lock time


_Refund to Bob (RB1)_
- in: CB1[0]
- out: Bob
- 40-day lock time


Depositing
==========
Scenario: Alice and Bob wish to create the channel.

* Alice and Bob make F (without signing)
* Alice makes + signs CB1, RB1; sent to Bob
* Bob makes + signs CA1, RA1; sent to Alice
* Alice checks CA1, RA1
* Bob checks CB1, RB1
* Alice signs F; sent to Bob
* Bob signs F; sent to Alice
* Alice + Bob publish F
* F gets confirmed by the block chain


Unassisted withdrawing
======================
Scenario: Alice wishes to withdraw and close the channel.

* Alice signs CA
* Alice publishes CA
* CA gets confirmed by the block chain
* Alice waits 40 days
* Alice signs RA
* Alice publishes RA
* RA gets confirmed by the block chain
(Equivalent scenario for Bob with CB, RB)


Transaction structure
=====================

	       Alice
	      /
	F - CC
	      \
	       Bob


_Close Commit (CC)_
- in: F[0]
- out 0: Alice
- out 1: Bob


Assisted withdrawing
====================
Scenario: Alice, Bob or both wish to withdraw and close the channel.

* Alice and Bob make CC (without signing)
* Alice signs CC; sent to Bob
* Bob signs CC; sent to Alice
* Alice + Bob publish CC
* CC gets confirmed by the block chain


Transaction structure
=====================
	           RA2 - Alice
	          /             |- TA2 - TRA2 - Alice
	    |- CA2 -------------|
	    |     \             |- SA2 - SDA2 - Bob
	    |       Bob
	F - |
	    |      RB2 - Bob
	    |     /             |- TB2 - TRB2 - Alice
	    |- CB2 -------------|
	          \             |- SB2 - SDB2 - Bob
	            Alice


_Commit by Alice (CA2)_
- in: F[0]
- out 0: 2-of-2 Alice+Bob (NEW KEYS!)
- out 1: HTLC Alice+Bob (NEW KEYS!)
- out 2: Bob (NEW KEY!)


_Commit by Bob (CB2)_
- in: F[0]
- out 0: 2-of-2 Alice+Bob (NEW KEYS!)
- out 1: HTLC Alice+Bob (NEW KEYS!)
- out 2: Alice (NEW KEY!)


_Refund to Alice (RA2)_

like RA1


_Refund to Bob (RB2)_

like RB1


_Timeout on Alice commit (TA2)_
- in: CA2[1]: time-out
- out: 2-of-2 Alice+Bob
- 3-day lock time


_Timeout on Bob commit (TB2)_
- in: CB2[1]: time-out
- out: 2-of-2 Alice+Bob
- 3-day lock time


_Timeout Refund on Alice commit (TRA2)_
- in: TA2[0]
- out: Alice
- 40-day lock time


_Timeout Refund on Bob commit (TRB2)_
- in: TB2[0]
- out: Alice
- 40-day lock time


_Settlement on Alice commit (SA2)_
- in: CA2[1]: hash value
- out: 2-of-2 Alice+Bob


_Settlement on Bob commit (SB2)_
- in: CB2[1]: hash value
- out: 2-of-2 Alice+Bob


_Settlement Delivery on Alice commit (SDA2)_
- in: SA2[0]
- out: Bob
- 40-day lock time


_Settlement Delivery on Bob commit (SDB2)_
- in: SB2[0]
- out: Bob
- 40-day lock time


Locking funds for a payment
===========================
Scenario: locking for a payment from Alice to Bob

* Alice and Bob make + exchange all new transactions (without signing)
* Alice signs RB2, SA2, SB2, SDA2, SDB2; sent to Bob.
* Bob signs   RA2, TA2, TB2, TRB2, TRA2, CA2; sent to Alice.

At this point, Alice is able to broadcast CA2 or CA1.

* Alice signs CB2; sent to Bob

At this point Bob is able to broadcast CB2 or CB1.

* Alice sends Bob the private key for CA1[1]

MAKES NO SENSE (that is Bob's key). Maybe should be:

* Alice sends Bob the *private key* for CA1[0]: refund to Alice

By giving her private key for CA1, Alice repudiates transaction CA1, assuring
Bob that she will not broadcast it.


* Bob sends Alice the *private key* for (assumed) CB1[0]: refund to Bob


Unassisted withdrawing with payment rollback
============================================
Scenario: Alice wishes to withdraw and close the channel, while a payment
from Alice to Bob is locked.

* Alice signs and publishes CA2
* CA2 gets confirmed by the block chain
* Bob does NOT publish a signed SA2 before the lock time of TA2
* Alice signs and publishes TA2
* TA2 gets confirmed by the block chain
* Alice waits 40 days
* Alice signs and publishes RA2 and TRA2

Scenario: Bob wishes to withdraw and close the channel, while a payment
from Alice to Bob is locked.

* Bob signs and publishes CB2
* CB2 gets confirmed by the block chain
* Bob does NOT publish a signed SB2 before the lock time of TB2
* Alice signs and publishes TB2
* TB2 gets confirmed by the block chain
* Alice and Bob wait 40 days
* Alice signs and publishes TRB2
* (Bob signs and publishes RB2)


Unassisted withdrawing with payment commit
==========================================
Scenario: Alice wishes to withdraw and close the channel, while a payment
from Alice to Bob is locked.

* Alice signs and publishes CA2
* Bob signs and publishes SA2 before the lock time of TA2
* CA2 and SA2 get confirmed by the block chain
* Alice and Bob wait 40 days
* Alice signs and publishes RA2
* (Bob signs and publishes SDA2)

Scenario: Bob wishes to withdraw and close the channel, while a payment
from Alice to Bob is locked.

* Bob signs and publishes CB2
* Bob signs and publishes SB2 before the lock time of TB2
* CB2 and SB2 get confirmed by the block chain
* Bob waits 40 days
* Bob signs and publishes RB2 and SDB2


Transaction structure
=====================

	           RA3 - Alice
	          /
	    |- CA3
	    |     \
	    |       Bob
	F - |
	    |      RB3 - Bob
	    |     /
	    |- CB3
	          \
	            Alice


_Commit by Alice (CA3)_

like CA1 (NEW KEYS!)


_Commit by Bob (CB3)_

like CB1 (NEW KEYS!)


_Refund to Alice (RA3)_

like RA1


_Refund to Bob (RB3)_

like RB1


Payment settlement (either commit or rollback)
==============================================
Scenario: Alice and Bob agree on either commit or rollback

* Alice and Bob make + exchange all new transactions (without signing)
* Alice signs RB3; sent to Bob.
* Bob signs   RA3, CA3; sent to Alice.

At this point, Alice is able to broadcast CA3 or CA2.

* Alice signs CB3; sent to Bob

At this point Bob is able to broadcast CB3 or CB2.

* Alice sends Bob the *private key* for (assumed) CA2[0]: refund to Alice

By giving her private key for CA2, Alice repudiates transaction CA2, assuring
Bob that she will not broadcast it.

* Bob sends Alice the *private key* for (assumed) CB2[0]: refund to Bob


