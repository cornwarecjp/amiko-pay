#!/usr/bin/env python
#    test_crypto.py
#    Copyright (C) 2015 by CJP
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

import unittest
import binascii
import sys
sys.path.append('../..')

import testenvironment

from amiko.core import crypto



class DummyLibSSL:
	def __init__(self):
		self.returnValues = {}

	def __enter__(self):
		self.oldLibSSL = crypto.libssl
		crypto.libssl = self
		return self


	def __exit__(self, exc_type, exc_val, exc_tb):
		crypto.libssl = self.oldLibSSL


	def __getattr__(self, name):
		def generic_method(*args, **kwargs):
			#print name, args, kwargs
			return self.returnValues[name].pop(0)

		return generic_method


	def EC_KEY_free(self, data):
		#Special case (won't pass through getattr)
		pass



class Test(unittest.TestCase):
	def test_cleanup(self):
		"Test the cleanup function"
		crypto.cleanup()

		#Now undo the cleanup:
		crypto.libssl.SSL_load_error_strings()


	def test_SHA256(self):
		"Test the SHA256 function"

		#Empty string example taken from Wikipedia:
		self.assertEqual(crypto.SHA256(
			""
			).encode("hex"),
			"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
			)
		#Pre-calculated using Linux sha256sum application:
		self.assertEqual(crypto.SHA256(
			"Amiko Pay"
			).encode("hex"),
			"81f50a37123696415c4e1ee6849faa09a6f8f355efcfa81992e850da07a834bd"
			)


	def test_RIPEMD160(self):
		"Test the RIPEMD160 function"

		#Examples from Wikipedia:
		self.assertEqual(crypto.RIPEMD160(
			""
			).encode("hex"),
			"9c1185a5c5e9fc54612808977ee8f548b2258d31"
			)
		self.assertEqual(crypto.RIPEMD160(
			"The quick brown fox jumps over the lazy dog"
			).encode("hex"),
			"37f332f68db77bd9d7edd4969571ad671cf9dd3b"
			)
		self.assertEqual(crypto.RIPEMD160(
			"The quick brown fox jumps over the lazy cog"
			).encode("hex"),
			"132072df690933835eb8b6ad0b77e7b6f14acad7"
			)


	def test_emptyKey(self):
		"Test behavior of an empty key object"
		key = crypto.Key()

		self.assertRaises(Exception, key.getPublicKey)
		self.assertRaises(Exception, key.getPrivateKey)
		self.assertRaises(Exception, key.sign, "foo")
		self.assertRaises(Exception, key.verify, "foo", "bar")


	def __testPrivateKey(self, key, lenPubKey, lenPrivKey):
		publicKey = key.getPublicKey()
		self.assertEqual(type(publicKey), str)
		self.assertEqual(len(publicKey), lenPubKey)

		privateKey = key.getPrivateKey()
		self.assertEqual(type(privateKey), str)
		self.assertEqual(len(privateKey), lenPrivKey)

		message = "foo"
		signature = key.sign(message)
		self.assertEqual(type(signature), str)
		self.assertLess(len(signature), 74)

		self.assertTrue(key.verify(message, signature))
		self.assertFalse(key.verify("bar", signature))

		key2 = crypto.Key()
		key2.setPublicKey(publicKey)
		self.assertTrue(key2.verify(message, signature))
		self.assertFalse(key2.verify("bar", signature))


	def test_newKey(self):
		"Test behavior of a new private key object"
		key = crypto.Key()
		key.makeNewKey(compressed=False)
		self.__testPrivateKey(key, 65, 32)

		key = crypto.Key()
		key.makeNewKey(compressed=True)
		self.__testPrivateKey(key, 33, 33)


	def __getKeyPair(self, compressed):
		#These are pre-generated using the crypto module itself.
		#So using these for testing is nothing more than a regression test.
		if compressed:
			return \
				binascii.unhexlify("024bccac7bf794f8dd3d165ff03d412d0a03628055bca4d1f64d37a2fd6ec0348b"), \
				binascii.unhexlify("abdc2d26c81366e95ccccb7b9cb1c64117126d2bdd6c745aace317b27d733f6601"), \
				binascii.unhexlify("3045022100f08fa87b0b7e500657d6fff1306e5c92928fada816168925f43a952f07caf0fc02200ca08dad7811874f49a481199e3c23b2fa719ec99d5abad092b6cf230bff7642")
		else:
			return \
				binascii.unhexlify("040329c4cdf0f29f9e44010fabe22d5c6c9ad8983429b192ebdb27d95435a092a9735aa54cd1cd4532d4b3dd0963b1d5ca9c7449af7098213347a2472ec1b2603b"), \
				binascii.unhexlify("a74550a2d67f817a7445a4a81665088379847a786ed20f7f736abd547b62e94f"), \
				binascii.unhexlify("30440220054d1c48dc5f4b013411239114f8521f76094158a21bceec6766949cde7a766602200655cfb1333cee44a3b8a33a4dec048412ae1bf790e704a1844d66e95b8b55f7")


	def test_privateKey(self):
		"Test behavior of an imported private key object"

		publicKey ,privateKey, fooSignature = self.__getKeyPair(compressed=False)
		key = crypto.Key()
		key.setPrivateKey(privateKey)
		self.__testPrivateKey(key, 65, 32)
		self.assertEqual(key.getPublicKey(), publicKey)
		self.assertEqual(key.getPrivateKey(), privateKey)
		self.assertTrue(key.verify("foo", fooSignature))
		self.assertFalse(key.verify("bar", fooSignature))


		publicKey ,privateKey, fooSignature = self.__getKeyPair(compressed=True)
		key = crypto.Key()
		key.setPrivateKey(privateKey)
		self.__testPrivateKey(key, 33, 33)
		self.assertEqual(key.getPublicKey(), publicKey)
		self.assertEqual(key.getPrivateKey(), privateKey)
		self.assertTrue(key.verify("foo", fooSignature))
		self.assertFalse(key.verify("bar", fooSignature))


	def test_publicKey(self):
		"Test behavior of a public key object"

		for compressed in (False, True):
			publicKey ,privateKey, fooSignature = self.__getKeyPair(compressed=compressed)
			key = crypto.Key()
			key.setPublicKey(publicKey)
			self.assertEqual(type(key.getPublicKey()), str)
			self.assertEqual(key.getPublicKey(), publicKey)
			self.assertRaises(Exception, key.getPrivateKey)
			self.assertTrue(key.verify("foo", fooSignature))
			self.assertFalse(key.verify("bar", fooSignature))


	def test_crossSigning(self):
		"Test whether one key's signature is accepted with another public key"

		for compressed in (False, True):
			priv1 = crypto.Key()
			priv1.makeNewKey(compressed=compressed)
			priv2 = crypto.Key()
			priv2.makeNewKey(compressed=compressed)
			self.assertNotEqual(priv1.getPrivateKey(), priv2.getPrivateKey())
			self.assertNotEqual(priv1.getPublicKey(), priv2.getPublicKey())

			message = "foo"
			sig1 = priv1.sign(message)
			sig2 = priv2.sign(message)

			pub1 = crypto.Key()
			pub1.setPublicKey(priv1.getPublicKey())
			pub2 = crypto.Key()
			pub2.setPublicKey(priv2.getPublicKey())

			self.assertTrue(pub1.verify(message, sig1))
			self.assertFalse(pub1.verify(message, sig2))


	def test_failures(self):
		"Test what happens in case of libssl failures"

		#Note: this is an incredibly white-box test.
		#Its main purpose is to get full code coverage, to make sure all
		#lines of the code "work" as intended.

		with DummyLibSSL() as libssl:
			libssl.returnValues = {'EC_KEY_new_by_curve_name': [1]}
			key = crypto.Key()

			libssl.returnValues = {'EC_KEY_generate_key': [0]}
			self.assertRaises(Exception, key.makeNewKey)

			libssl.returnValues = {'o2i_ECPublicKey': [0]}
			self.assertRaises(Exception, key.setPublicKey, '')

			libssl.returnValues = \
			{
			'EC_KEY_generate_key': [1],
			'EC_KEY_set_conv_form': [None]
			}
			key.makeNewKey()

			libssl.returnValues = {'i2o_ECPublicKey': [0]}
			self.assertRaises(Exception, key.getPublicKey)

			libssl.returnValues = {'i2o_ECPublicKey': [32, 33]}
			self.assertRaises(Exception, key.getPublicKey)

			libssl.returnValues = {'BN_init': [None], 'BN_bin2bn': [0]}
			self.assertRaises(Exception, key.setPrivateKey, '')

			libssl.returnValues = \
			{
			'EC_KEY_new_by_curve_name': [0],
			'BN_init': [None],
			'BN_bin2bn': [1]
			}
			key = crypto.Key()
			self.assertRaises(Exception, key.setPrivateKey, '')

			libssl.returnValues = {'EC_KEY_new_by_curve_name': [1]}
			key = crypto.Key()

			libssl.returnValues = \
			{
			'BN_init': [None],
			'BN_bin2bn': [1],
			'EC_KEY_get0_group': [None],
			'BN_CTX_new': [0]
			}
			self.assertRaises(Exception, key.setPrivateKey, '')

			libssl.returnValues = \
			{
			'BN_init': [None],
			'BN_bin2bn': [1],
			'EC_KEY_get0_group': [None],
			'BN_CTX_new': [1],
			'EC_POINT_new': [0]
			}
			self.assertRaises(Exception, key.setPrivateKey, '')

			libssl.returnValues = \
			{
			'BN_init': [None],
			'BN_bin2bn': [1],
			'EC_KEY_get0_group': [None],
			'BN_CTX_new': [1],
			'EC_POINT_new': [1],
			'EC_POINT_mul': [0]
			}
			self.assertRaises(Exception, key.setPrivateKey, '')

			libssl.returnValues = \
			{
			'EC_KEY_generate_key': [1],
			'EC_KEY_set_conv_form': [None]
			}
			key.makeNewKey()

			libssl.returnValues = {'EC_KEY_get0_private_key': [0]}
			self.assertRaises(Exception, key.getPrivateKey)

			libssl.returnValues = \
			{
			'EC_KEY_get0_private_key': [1],
			'BN_num_bits': [32*8],
			'BN_bn2bin': [33]
			}
			self.assertRaises(Exception, key.getPrivateKey)

			libssl.returnValues = \
			{
			'ECDSA_size': [71],
			'ECDSA_sign': [0]
			}
			self.assertRaises(Exception, key.sign, '')

			libssl.returnValues = {'ECDSA_verify': [-1]}
			self.assertRaises(Exception, key.verify, '', '')



if __name__ == "__main__":
	unittest.main(verbosity=2)

