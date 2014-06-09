#TODO:
import sys
sys.path += ['..']

from bitcoinrpc.authproxy import AuthServiceProxy

import settings



class Bitcoind:
	def __init__(self, settings):
		self.access = AuthServiceProxy(settings.bitcoinRPCURL)

	def getInfo(self):
		return self.access.getinfo()


settings = settings.Settings("amikopay.conf")

bd = Bitcoind(settings)
print bd.getInfo()


