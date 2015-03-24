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


Unassisted withdrawing
======================
Scenario: Alice wishes to withdraw and close the channel.

* Alice signs CA
* Alice publishes CA
* Alice waits 40 days
* Alice signs RA
* Alice publishes RA
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
- in: CA2[0]
- out: Alice
- 40-day lock time


_Refund to Bob (RB2)_
- in: CB2[0]
- out: Bob
- 40-day lock time


_Timeout on Alice commit (TA2)_
- in: CA2[1] (time-out)
- out: 2-of-2 Alice+Bob
- 3-day lock time


_Timeout on Bob commit (TB2)_
- in: CB2[1] (time-out)
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
- in: CA2[1] (hash value)
- out: 2-of-2 Alice+Bob


_Settlement on Bob commit (SB2)_
- in: CB2[1] (hash value)
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
* Alice signs CRB2, SA2, SB2, SDA2, SDB2; sent to Bob.
* Bob signs RA2, TA2, TB2, TRA2, TRB2, CA2; sent to Alice.

At this point, Alice is able to broadcast CA2 or CA1.

* Alice signs CB2; sent to Bob

At this point Bob is able to broadcast CB2 or CB1.

* Alice sends Bob the private key for CA1[1]
MAKES NO SENSE (that is Bob's key). Maybe should be:
* Alice sends Bob the *private key* for CA1[0] (refund to Alice)

By giving her private key for C1a, Alice repudiates transaction C1a, assuring
Bob that she will not broadcast it.


* Bob sends Alice the *private key* for (assumed) CB1[0] (refund to Bob)



