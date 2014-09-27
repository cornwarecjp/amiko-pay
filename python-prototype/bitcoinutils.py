#    bitcoinutils.py
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



def getInputsForAmount(bitcoind, amount):
	unspent = bitcoind.listUnspent()

	#TODO: think about the best policy here.
	#Possible objectives:
	# - minimizing taint between addresses (privacy protection)
	# - minimizing coin fragmentation (transaction size, related to fee costs)
	# - choosing old coins (related to fee costs)
	#For now, an attempt is made to minimize coin fragmentation.

	unspent.sort(cmp=lambda a,b: cmp(a["amount"], b["amount"]))

	used = None
	total = 0
	for u in unspent:
		if u["amount"] >= amount:
			used = [u]
			total = u["amount"]
			break
	if used is None:
		used = []
		while total < amount:
			try:
				u = unspent.pop()
			except IndexError:
				raise Exception("Insufficient funds")
			used.append(u)
			total += u["amount"]

	return total, [
		(u["txid"], u["vout"], u["scriptPubKey"])
		for u in used]

