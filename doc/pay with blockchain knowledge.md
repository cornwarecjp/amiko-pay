Introduction
============

To make a Bitcoin-based Ripple system completely trust-free, there must be a
way to reach consensus on whether a Ripple-style transaction has been committed.

The paper provides a solution in section 2.4.3:
https://github.com/cornwarecjp/amiko-pay/raw/master/doc/amiko_draft_2.pdf

However, a remaining issue is that this solution makes the "commit decision"
conditions extremely complicated, and, to make the system completely trust-free
(even between direct neighbors), the commit decision has to be encoded in the
form of a Bitcoin script. Until now, it was considered impossible to implement
such a script without creating a major extension to the Bitcoin scripting
language. Also, such an extension could conflict with the idea of "block chain
pruning":
https://bitcointalk.org/index.php?topic=94674.msg1715276#msg1715276

This document provides a partial solution, in the form of a script that
determines whether a certain hash input is given in a specific transaction in a
specific block. No Bitcoin scripting extension is needed, besides enabling the
currently disabled op-codes used in this script. Since the required block and
transaction data is given in the scriptSig, this partial solution does not
prevent block chain pruning.


Remaining issues
================

The script assumes the transaction to be in one specific location in a Merkle
tree of one specific depth. The solution can be generalized to an arbitrary
location in a Merkle tree of unknown depth, by using conditional execution
(OP_IF .. OP_ELSE .. OP_ENDIF). Since Bitcoin scripts are not Turing-complete,
there will always remain a maximum Merkle tree depth, but a reasonable value for
this maximum depth can be estimated from the maximum block size.

The script assumes the transaction to be accepted in a block with a specific
block height. This can also be generalized to a range of block heights, by using
conditional execution.

The transaction and block chain information supplied in scriptSig does not have
to match the main chain: it can also be an alt chain, with less total difficulty
than the main chain. It is assumed that solo-mining such an alt chain is more
expensive than the value of the transaction, and therefore not profitable.
However, if this kind of transaction remains unspent (or replaced) for too long,
Moore's law will haunt you, making the attack arbitrarily cheap.

Finally, this is only a partial solution: it only allows the spender to prove
PRESENCE (commit), not to prove ABSENCE (rollback) of the hash input in a
certain block (range). To prove ABSENCE, ALL transactions in a block (range)
must be inspected, meaning that
* the scriptSig must contain all transaction data of a certain block (range).
  Since scriptSig itself must be included in some other block, this will quickly
  lead to an explosion of required space in blocks, making this solution
  practically impossible.
* since there is no looping in Bitcoin scripts, scriptPubKey has to contain
  "unrolled loops" which traverse the entire Merkle trees of several blocks.
  This will make the scriptPubKey orders of magnitude larger than the script
  provided here.
For these reasons, it is considered impossible to extend this partial solution
to a full solution. It remains To Be Determined whether the partial solution is
good enough to be useful.


scriptSig:
==========

h3 #Block grandparent header
h2 #Block parent header
h1 #Block header

m3 #Merkle tree neighbor 3
m2 #Merkle tree neighbor 2
m1 #Merkle tree neighbor 1

tx #Serialized transaction that contains the token

offset #Byte offset in the transaction where the token is located
size #Size of the token (bytes)


scriptPubKey:
=============

#stack: h3 h2 h1 m3 m2 m1 tx offset size


OP_3DUP 
#stack: h3 h2 h1 m3 m2 m1 tx offset size tx offset size
OP_SUBSTR #Note: currently DISABLED!!!
#stack: h3 h2 h1 m3 m2 m1 tx offset size token
OP_SHA256
#stack: h3 h2 h1 m3 m2 m1 tx offset size SHA256(token)
required_hash
#stack: h3 h2 h1 m3 m2 m1 tx offset size SHA256(token) required_hash
OP_EQUALVERIFY #SHA256(token) must match required_hash in scriptPubKey
#stack: h3 h2 h1 m3 m2 m1 tx offset size
OP_2DROP
#stack: h3 h2 h1 m3 m2 m1 tx


OP_HASH256
#stack: h3 h2 h1 m3 m2 m1 HASH256(tx)
OP_CAT #Note: currently DISABLED!!!
#stack: h3 h2 h1 m3 m2 (m1 . HASH256(tx))
OP_HASH256
#stack: h3 h2 h1 m3 m2 HASH256(m1 . HASH256(tx))
OP_CAT #Note: currently DISABLED!!!
#stack: h3 h2 h1 m3 (m2 . HASH256(m1 . HASH256(tx)))
OP_HASH256
#stack: h3 h2 h1 m3 HASH256(m2 . HASH256(m1 . HASH256(tx)))
OP_CAT #Note: currently DISABLED!!!
#stack: h3 h2 h1 (m3 . HASH256(m2 . HASH256(m1 . HASH256(tx))))
OP_HASH256
#stack: h3 h2 h1 HASH256(m3 . HASH256(m2 . HASH256(m1 . HASH256(tx))))
#Since the top stack item should now be the Merkle tree root, we'll now simplify
#the description of the stack to:
#stack: h3 h2 h1 merkle_root


OP_OVER
#stack: h3 h2 h1 merkle_root h1
40
32
#stack: h3 h2 h1 merkle_root h1 40 32
OP_SUBSTR #Note: currently DISABLED!!!
#stack: h3 h2 h1 merkle_root root_in_header
OP_EQUALVERIFY #The calculated Merkle root must match the one in the header
#stack: h3 h2 h1


OP_DUP
#stack: h3 h2 h1 h1
OP_HASH256
#stack: h3 h2 h1 HASH256(h1)
OP_DUP
#stack: h3 h2 h1 HASH256(h1)
required_difficulty
#stack: h3 h2 h1 HASH256(h1) required_difficulty
OP_LESSTHANOREQUAL
#stack: h3 h2 h1 (HASH256(h1) <= required_difficulty)
OP_VERIFY #h1 must meet the minimum difficulty requirement
#stack: h3 h2 h1


4
32
#stack: h3 h2 h1 4 32
OP_SUBSTR #Note: currently DISABLED!!!
#stack: h3 h2 parent_hash_of_h1
OP_OVER
#stack: h3 h2 parent_hash_of_h1 h2
OP_HASH256
#stack: h3 h2 parent_hash_of_h1 HASH256(h2)
OP_DUP
#stack: h3 h2 parent_hash_of_h1 HASH256(h2) HASH256(h2)
required_difficulty
#stack: h3 h2 parent_hash_of_h1 HASH256(h2) HASH256(h2) required_difficulty
OP_LESSTHANOREQUAL
#stack: h3 h2 parent_hash_of_h1 HASH256(h2) (HASH256(h2) <= required_difficulty)
OP_VERIFY #h2 must meet the minimum difficulty requirement
#stack: h3 h2 parent_hash_of_h1 HASH256(h2)
OP_EQUALVERIFY #h2 must be the parent of h1
#stack: h3 h2


4
32
#stack: h3 h2 4 32
OP_SUBSTR #Note: currently DISABLED!!!
#stack: h3 parent_hash_of_h2
OP_OVER
#stack: h3 parent_hash_of_h2 h3
OP_HASH256
#stack: h3 parent_hash_of_h2 HASH256(h3)
OP_DUP
#stack: h3 parent_hash_of_h2 HASH256(h3) HASH256(h3)
required_difficulty
#stack: h3 parent_hash_of_h2 HASH256(h3) HASH256(h3) required_difficulty
OP_LESSTHANOREQUAL
#stack: h3 parent_hash_of_h2 HASH256(h3) (HASH256(h3) <= required_difficulty)
OP_VERIFY #h3 must meet the minimum difficulty requirement
#stack: h3 parent_hash_of_h2 HASH256(h3)
OP_EQUALVERIFY #h3 must be the parent of h2
#stack: h3


4
32
#stack: h3 4 32
OP_SUBSTR #Note: currently DISABLED!!!
#stack: parent_hash_of_h3
base_block_hash
#stack: parent_hash_of_h3 base_block_hash
OP_EQUALVERIFY #base block must be the parent of h3

