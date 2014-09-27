#    crypto.py
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

import ctypes

libssl = ctypes.cdll.LoadLibrary("libssl.so") #Will be different on windows

#Constants:
NID_secp256k1 = 714


#Function prototype modifications:
libssl.EC_KEY_new_by_curve_name.argtypes = [ctypes.c_int]
libssl.EC_KEY_new_by_curve_name.restype = ctypes.c_void_p

libssl.EC_KEY_free.argtypes = [ctypes.c_void_p]

libssl.EC_KEY_generate_key.argtypes = [ctypes.c_void_p]
libssl.EC_KEY_new_by_curve_name.restype = ctypes.c_int

libssl.o2i_ECPublicKey.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
libssl.o2i_ECPublicKey.restype = ctypes.c_void_p

libssl.i2o_ECPublicKey.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
libssl.i2o_ECPublicKey.restype = ctypes.c_int

libssl.ECDSA_size.argtypes = [ctypes.c_void_p]
libssl.ECDSA_size.restype = ctypes.c_int

libssl.ECDSA_sign.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
	ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p] 
libssl.ECDSA_sign.restype = ctypes.c_int



libssl.SSL_load_error_strings()
libssl.SSL_library_init()



def cleanup():
	libssl.ERR_free_strings()



class Key:
	def __init__(self):
		self.keyData = ctypes.c_void_p(libssl.EC_KEY_new_by_curve_name(NID_secp256k1))
		self.hasPublicKey = False
		self.hasPrivateKey = False


	def __del__(self):
		libssl.EC_KEY_free(self.keyData)


	#TODO: copy behavior
	#TODO: comparison behavior


	def makeNewKey(self):
		if not libssl.EC_KEY_generate_key(self.keyData):
			raise Exception("EC_KEY_generate_key failed")
		self.hasPublicKey = True
		self.hasPrivateKey = True


	def setPublicKey(self, key):

		b = ctypes.create_string_buffer(key)

		if not libssl.o2i_ECPublicKey(
				ctypes.byref(self.keyData), ctypes.byref(ctypes.pointer(b)),
				len(key)):
			#TODO: reset key state
			raise Exception("o2i_ECPublicKey failed")

		self.hasPublicKey = True
		self.hasPrivateKey = False


	def getPublicKey(self):
		if not self.hasPublicKey:
			raise Exception("Public key unknown")

		size = libssl.i2o_ECPublicKey(self.keyData, None)
		if not size:
			raise Exception("i2o_ECPublicKey failed")

		b = ctypes.create_string_buffer(size)
		if libssl.i2o_ECPublicKey(self.keyData, ctypes.byref(ctypes.pointer(b))) != size:
			raise Exception("i2o_ECPublicKey returned unexpected size")

		return ''.join([c for c in b])


	#TODO: get/set private key


	def sign(self, data):
		if not self.hasPrivateKey:
			raise Exception("private key unknown")

		size = ctypes.c_int(libssl.ECDSA_size(self.keyData))

		b_data = ctypes.create_string_buffer(data)

		b_sig = ctypes.create_string_buffer(size.value)

		if not libssl.ECDSA_sign(0, ctypes.byref(b_data), len(data), ctypes.byref(b_sig), ctypes.byref(size), self.keyData):
			raise Exception("ECDSA_sign failed")

		return ''.join([b_sig[i] for i in range(size.value)]) #size contains actual size



#Test:
privKey = Key()
privKey.makeNewKey()

pubKey = Key()
pubKey.setPublicKey(privKey.getPublicKey())

data = "blablabla"

sig = privKey.sign(data)

print repr(sig)

cleanup()


