from bitcoinrpc.authproxy import AuthServiceProxy

import log



class Bitcoind:
	def __init__(self, settings):
		log.log("Making connection to Bitcoin daemon...")
		self.access = AuthServiceProxy(settings.bitcoinRPCURL)
		log.log("...done")
		

	def getBalance(self):
		return self.DecimaltoAmount(self.access.getbalance())


	def DecimaltoAmount(self, value):
		return int(value*100000000)




