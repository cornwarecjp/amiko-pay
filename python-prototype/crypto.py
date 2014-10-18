#    crypto.py
#    Copyright (C) 2009-2012 by the Bitcoin developers
#    Copyright (C) 2013-2014 by CJP
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



#Structs:
class BIGNUM(ctypes.Structure):
	_fields_ = \
	[
	("d", ctypes.c_void_p),	# Pointer to an array of 'BN_BITS2' bit chunks.
	("top", ctypes.c_int),	# Index of last used d +1.
	# The next are internal book keeping for bn_expand.
	("dmax", ctypes.c_int),	# Size of the d array.
	("neg", ctypes.c_int),	# one if the number is negative
	("flags", ctypes.c_int)
	]


#Constants:
NID_secp256k1 = 714

POINT_CONVERSION_COMPRESSED = 2
POINT_CONVERSION_UNCOMPRESSED = 4


#Function prototype modifications:
libssl.EC_KEY_new_by_curve_name.argtypes = [ctypes.c_int]
libssl.EC_KEY_new_by_curve_name.restype = ctypes.c_void_p

libssl.EC_KEY_free.argtypes = [ctypes.c_void_p]

libssl.EC_KEY_generate_key.argtypes = [ctypes.c_void_p]
libssl.EC_KEY_new_by_curve_name.restype = ctypes.c_int

libssl.EC_KEY_get0_group.argtypes = [ctypes.c_void_p]
libssl.EC_KEY_get0_group.restype = ctypes.c_void_p

libssl.EC_KEY_get0_private_key.argtypes = [ctypes.c_void_p]
libssl.EC_KEY_get0_private_key.restype = ctypes.c_void_p

libssl.EC_KEY_check_key.argtypes = [ctypes.c_void_p]
libssl.EC_KEY_check_key.restype = ctypes.c_int

libssl.EC_KEY_set_conv_form.argtypes = [ctypes.c_void_p, ctypes.c_int]

libssl.EC_KEY_set_private_key.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
libssl.EC_KEY_set_private_key.restype = ctypes.c_int

libssl.EC_KEY_set_public_key.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
libssl.EC_KEY_set_public_key.restype = ctypes.c_int

libssl.EC_POINT_new.argtypes = [ctypes.c_void_p]
libssl.EC_POINT_new.restype = ctypes.c_void_p

libssl.EC_POINT_free.argtypes = [ctypes.c_void_p]

libssl.EC_POINT_mul.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
	ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
libssl.EC_POINT_mul.restype = ctypes.c_int

libssl.o2i_ECPublicKey.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
libssl.o2i_ECPublicKey.restype = ctypes.c_void_p

libssl.i2o_ECPublicKey.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
libssl.i2o_ECPublicKey.restype = ctypes.c_int

libssl.ECDSA_size.argtypes = [ctypes.c_void_p]
libssl.ECDSA_size.restype = ctypes.c_int

libssl.ECDSA_sign.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
	ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p] 
libssl.ECDSA_sign.restype = ctypes.c_int

libssl.ECDSA_verify.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int, 
	ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
libssl.ECDSA_verify.restype = ctypes.c_int

libssl.SHA256.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
libssl.SHA256.restype = ctypes.c_char_p

libssl.RIPEMD160.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
libssl.RIPEMD160.restype = ctypes.c_char_p

libssl.d2i_ECPrivateKey.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
libssl.d2i_ECPrivateKey.restype = ctypes.c_void_p

libssl.BN_init.argtypes = [ctypes.c_void_p]

libssl.BN_bin2bn.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p]
libssl.BN_bin2bn.restype = ctypes.c_void_p

libssl.BN_bn2bin.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
libssl.BN_bn2bin.restype = ctypes.c_int

libssl.BN_clear_free.argtypes = [ctypes.c_void_p]

libssl.BN_CTX_new.argtypes = []
libssl.BN_CTX_new.restype = ctypes.c_void_p

libssl.BN_CTX_free.argtypes = [ctypes.c_void_p]

libssl.BN_num_bits.argtypes = [ctypes.c_void_p]
libssl.BN_num_bits.restype = ctypes.c_int

def BN_num_bytes(a):
	return (libssl.BN_num_bits(a)+7)/8



libssl.SSL_load_error_strings()
libssl.SSL_library_init()


#Note: it might be possible to register this with Python's atexit module, but
#it might be necessary to make sure that all constructed objects (such as keys)
#are freed before calling this.Calling this at program termination shouldn't be
#that essential anyway, so wel'll leave it to the application code.
def cleanup():
	libssl.ERR_free_strings()


def SHA256(data):
	b = ctypes.create_string_buffer(32)
	libssl.SHA256(data, len(data), b)
	return ''.join(b)


def RIPEMD160(data):
	b = ctypes.create_string_buffer(20)
	libssl.RIPEMD160(data, len(data), b)
	return ''.join(b)


class Key:
	def __init__(self):
		self.keyData = ctypes.c_void_p(libssl.EC_KEY_new_by_curve_name(NID_secp256k1))
		self.hasPublicKey = False
		self.hasPrivateKey = False
		self.hasCompressedPublicKey = False

		#keep a reference to ensure that we're deleted before libssl:
		self.libssl = libssl


	def __del__(self):
		#Somehow, the module-level libssl becomes None at some point in time
		#during shutdown. Use the local reference instead.
		self.libssl.EC_KEY_free(self.keyData)


	#TODO: copy behavior
	#TODO: comparison behavior


	def makeNewKey(self, compressed=True):
		if not libssl.EC_KEY_generate_key(self.keyData):
			raise Exception("EC_KEY_generate_key failed")

		self.setPublicKeyCompression(compressed)
		self.hasPublicKey = True
		self.hasPrivateKey = True


	def setPublicKeyCompression(self, compressed):
		libssl.EC_KEY_set_conv_form(self.keyData,
			POINT_CONVERSION_COMPRESSED if compressed else POINT_CONVERSION_UNCOMPRESSED
			)
		self.hasCompressedPublicKey = compressed


	def setPublicKey(self, key):
		compressed = len(key) == 33

		b = ctypes.create_string_buffer(key)

		if not libssl.o2i_ECPublicKey(
				ctypes.byref(self.keyData), ctypes.byref(ctypes.pointer(b)),
				len(key)):
			#TODO: reset key state
			raise Exception("o2i_ECPublicKey failed")

		self.setPublicKeyCompression(compressed)
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

		return ''.join(c for c in b)


	def setPrivateKey(self, key):
		compressed = len(key) == 33
		key = key[:32]

		priv_key = BIGNUM()
		libssl.BN_init(ctypes.byref(priv_key))
		if not libssl.BN_bin2bn(key, len(key), ctypes.byref(priv_key)):
			raise Exception("BN_bin2bn failed")

		# Generate a private key from just the secret parameter
		ctx = None
		pub_key = None

		if not self.keyData:
			raise Exception("Key structure not initialized")

		group = ctypes.c_void_p(libssl.EC_KEY_get0_group(self.keyData))

		try:
			ctx = ctypes.c_void_p(libssl.BN_CTX_new())
			if not ctx:
				raise Exception("BN_CTX_new failed")

			pub_key = ctypes.c_void_p(libssl.EC_POINT_new(group))
			if not pub_key:
				raise Exception("EC_POINT_new failed")

			if not libssl.EC_POINT_mul(group, pub_key, ctypes.byref(priv_key), None, None, ctx):
				raise Exception("EC_POINT_mul failed")

			libssl.EC_KEY_set_private_key(self.keyData, ctypes.byref(priv_key))
			libssl.EC_KEY_set_public_key(self.keyData, pub_key)

		finally:
			if pub_key:
				libssl.EC_POINT_free(pub_key)
			if ctx:
				libssl.BN_CTX_free(ctx)

			libssl.BN_clear_free(ctypes.byref(priv_key))

		self.setPublicKeyCompression(compressed)
		self.hasPublicKey = True
		self.hasPrivateKey = True



	def getPrivateKey(self):
		if not self.hasPrivateKey:
			raise Exception("private key unknown")

		bn = libssl.EC_KEY_get0_private_key(self.keyData)
		if not bn:
			raise Exception("EC_KEY_get0_private_key failed")

		nBytes = BN_num_bytes(bn)
		b = ctypes.create_string_buffer(nBytes)

		n = libssl.BN_bn2bin(bn, b)
		if n != nBytes:
			raise Exception("BN_bn2bin failed")

		ret = "\0"*(32-nBytes) + ''.join(c for c in b)
		if self.hasCompressedPublicKey:
			ret += chr(1)
		return ret


	def sign(self, data):
		if not self.hasPrivateKey:
			raise Exception("private key unknown")

		size = ctypes.c_int(libssl.ECDSA_size(self.keyData))

		b_data = ctypes.create_string_buffer(data)

		b_sig = ctypes.create_string_buffer(size.value)

		if not libssl.ECDSA_sign(0, ctypes.byref(b_data), len(data),
				ctypes.byref(b_sig), ctypes.byref(size), self.keyData):
			raise Exception("ECDSA_sign failed")

		return ''.join([b_sig[i] for i in range(size.value)]) #size contains actual size


	def verify(self, data, signature):
		if not self.hasPublicKey:
			raise Exception("public key unknown")

		b_data = ctypes.create_string_buffer(data)

		# -1 = error, 0 = bad sig, 1 = good
		result = libssl.ECDSA_verify(0, b_data, len(data), signature, len(signature), self.keyData)
		if result == 1:
			return True
		if result == 0:
			return False
		raise Exception("ECDSA_verify failed")



if __name__ == "__main__":
	#Test:
	for compression in [False, True]:
		print "Public key compression: ", compression
		privKey = Key()
		privKey.makeNewKey(compression)

		pubKey = Key()
		pubKey.setPublicKey(privKey.getPublicKey())

		data = "blablabla"

		goodSig = privKey.sign(data)
		print "Good signature:", pubKey.verify(data, goodSig)

		otherKey = Key()
		otherKey.makeNewKey()
		badSig1 = otherKey.sign(data)

		badSig2 = privKey.sign("bad data")

		print "Bad signature 1:", pubKey.verify(data, badSig1)
		print "Bad signature 2:", pubKey.verify(data, badSig2)

		priv = privKey.getPrivateKey()
		privKey2 = Key()
		privKey2.setPrivateKey(priv)
		print "Private key is constant:", privKey2.getPrivateKey() == priv

		goodSig = privKey2.sign(data)
		print "Good signature 2:", pubKey.verify(data, goodSig)

	cleanup()


