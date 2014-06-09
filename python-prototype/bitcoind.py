from bitcoinrpc.authproxy import AuthServiceProxy

import log



class Bitcoind:
	def __init__(self, settings):
		log.log("Connecting to Bitcoin daemon...")
		self.access = AuthServiceProxy(settings.bitcoinRPCURL)
		log.log("...connected to Bitcoin daemon")
		
		print self.getInfo()


	def getInfo(self):
		return self.access.getinfo()

