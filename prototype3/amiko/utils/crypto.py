#    crypto.py
#    Copyright (C) 2009-2012 by the Bitcoin developers
#    Copyright (C) 2013-2015 by CJP
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
#
#    Additional permission under GNU GPL version 3 section 7
#
#    If you modify this Program, or any covered work, by linking or combining it
#    with the OpenSSL library (or a modified version of that library),
#    containing parts covered by the terms of the OpenSSL License and the SSLeay
#    License, the licensors of this Program grant you additional permission to
#    convey the resulting work. Corresponding Source for a non-source form of
#    such a combination shall include the source code for the parts of the
#    OpenSSL library used as well as that of the covered work.

import threading
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


#Callback types:
#Maybe WINFUNCTYPE in windows?
lockingCallbackType = ctypes.CFUNCTYPE(None,
	ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
	use_errno=True, use_last_error=True)
threadIDCallbackType = ctypes.CFUNCTYPE(ctypes.c_ulong,
	use_errno=True, use_last_error=True)

#Constants:
CRYPTO_LOCK = 1

NID_secp256k1 = 714

POINT_CONVERSION_COMPRESSED = 2
POINT_CONVERSION_UNCOMPRESSED = 4


#Function prototype modifications:
libssl.CRYPTO_set_locking_callback.argtypes = [ctypes.c_void_p]
libssl.CRYPTO_set_locking_callback.restype = None

libssl.CRYPTO_set_id_callback.argtypes = [ctypes.c_void_p]
libssl.CRYPTO_set_id_callback.restype = None

libssl.CRYPTO_num_locks.argtypes = []
libssl.CRYPTO_num_locks.restype = ctypes.c_int

libssl.EC_KEY_new_by_curve_name.argtypes = [ctypes.c_int]
libssl.EC_KEY_new_by_curve_name.restype = ctypes.c_void_p

libssl.EC_KEY_free.argtypes = [ctypes.c_void_p]

libssl.EC_KEY_generate_key.argtypes = [ctypes.c_void_p]
libssl.EC_KEY_generate_key.restype = ctypes.c_int

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


mutexes = []
def lockingCallback(mode, i, file, line):
	global mutexes

	if mode & CRYPTO_LOCK:
		mutexes[int(i)].acquire()
	else:
		mutexes[int(i)].release()
ctypes_lockingCallback = lockingCallbackType(lockingCallback)


def threadIDCallback():
	return long(threading.currentThread().ident)
ctypes_threadIDCallback = threadIDCallbackType(threadIDCallback)


libssl.SSL_load_error_strings()
libssl.SSL_library_init()

for i in range(libssl.CRYPTO_num_locks()):
	mutexes.append(threading.Lock())

libssl.CRYPTO_set_locking_callback(ctypes_lockingCallback)
libssl.CRYPTO_set_id_callback(ctypes_threadIDCallback)

#Note: it might be possible to register this with Python's atexit module, but
#it might be necessary to make sure that all constructed objects (such as keys)
#are freed before calling this. Calling this at program termination shouldn't be
#that essential anyway, so wel'll leave it to the application code.
def cleanup():
	"""
	Clean up. Should be called on program termination.
	After cleanup(), no more crypto.py functions should be called.
	"""

	libssl.ERR_free_strings()
	#TODO: maybe clean up the callbacks?


def SHA256(data):
	"""
	Calculate the SHA256 hash of given data

	Arguments:
	data : str; the data of which to calculate the SHA256 hash

	Return value:
	str; the SHA256 hash.
	Note: this is in binary form (not hexadecimal).
	Note 2: this is in OpenSSL's byte order, which is the reverse of
	        (at least some cases of) the byte order used in Bitcoin.
	"""

	b = ctypes.create_string_buffer(32)
	libssl.SHA256(data, len(data), b)
	return ''.join(b)


def RIPEMD160(data):
	"""
	Calculate the RIPEMD160 hash of given data

	Arguments:
	data : str; the data of which to calculate the RIPEMD160 hash

	Return value:
	str; the RIPEMD160 hash.
	Note: this is in binary form (not hexadecimal).
	"""

	b = ctypes.create_string_buffer(20)
	libssl.RIPEMD160(data, len(data), b)
	return ''.join(b)


class Key:
	"""
	An ECDSA key object.

	Contains either no keys, a public key or a public/private key pair.
	Supports both "compressed" and "non-compressed" public keys, in the same way
	as Bitcoin.
	"""

	def __init__(self):
		"""
		Constructor.
		The constructed object does not contain any key data.
		"""

		self.keyData = ctypes.c_void_p(libssl.EC_KEY_new_by_curve_name(NID_secp256k1))
		self.hasPublicKey = False
		self.hasPrivateKey = False
		self.hasCompressedPublicKey = False

		#keep a reference to ensure that we're deleted before libssl:
		self.libssl = libssl


	def __del__(self):
		"""
		Destructor.
		"""

		#Somehow, the module-level libssl becomes None at some point in time
		#during shutdown. Use the local reference instead.
		self.libssl.EC_KEY_free(self.keyData)


	#TODO: copy behavior
	#TODO: comparison behavior


	def makeNewKey(self, compressed=True):
		"""
		Generates a new public/private key pair.

		Arguments:
		compressed: bool; use compressed public keys (default: True)

		Exceptions:
		Exception: key generating failed
		"""

		if not libssl.EC_KEY_generate_key(self.keyData):
			raise Exception("EC_KEY_generate_key failed")

		self.setPublicKeyCompression(compressed)
		self.hasPublicKey = True
		self.hasPrivateKey = True


	def setPublicKeyCompression(self, compressed):
		"""
		Choose between compressed and non-compressed public keys.
		Note: only intended for internal use in the Key class.

		Arguments:
		compressed: bool; use compressed public keys
		"""

		libssl.EC_KEY_set_conv_form(self.keyData,
			POINT_CONVERSION_COMPRESSED if compressed else POINT_CONVERSION_UNCOMPRESSED
			)
		self.hasCompressedPublicKey = compressed


	def setPublicKey(self, key):
		"""
		Sets a public key.
		Previous key data (if any) is discarded.

		Arguments:
		key: str; the public key data
		     Note: should be 33 bytes for compressed public keys, or 65 bytes
		     for non-compressed public keys.

		Exceptions:
		Exception: setting the key failed
		"""

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
		"""
		Gets a public key.

		Return value:
		str; the public key data.

		Exceptions:
		Exception: getting the key failed
		"""

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
		"""
		Sets a private key.
		Previous key data (if any) is discarded.

		Arguments:
		key: str; the private key data
		     Note: should be 33 bytes for compressed public keys, or 32 bytes
		     for non-compressed public keys.

		Exceptions:
		Exception: setting the key failed
		"""

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
		"""
		Gets a private key.

		Return value:
		str; the private key data.

		Exceptions:
		Exception: getting the key failed
		"""

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
		"""
		Sign the given data
		Note: private key must be available.

		Arguments:
		data : str; the data to be signed.

		Return value:
		str; the signature.

		Exceptions:
		Exception: signing failed
		"""

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
		"""
		Verify the given signature.
		Note: public key must be available.

		Arguments:
		data : str; the data to which the signature applies.
		signature : str; the signature.

		Return value:
		bool; indicates whether the signature is correct (True) or not (False)

		Exceptions:
		Exception: signature verification failed
		"""

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


