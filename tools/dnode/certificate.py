#!/usr/bin/env python

import os.path
import re
import struct
import sys
import tempfile

from OpenSSL import crypto, rand

import dnode
import dnode.data

serial_pattern = re.compile (
	r"^[1-9]\d*$")

digest_pattern = re.compile (
	r"^\d{2}(:\d{2})*$")

class Authority:

	def __init__ (self, dnode_client, path, data):

		self.state = "none"

		self.dnode_client = dnode_client
		self.path = path
		self.data = data

	def create (self, name):

		if (self.state != "none"):
			raise Exception ()

		# create key

		self.root_key = crypto.PKey ()
		self.root_key.generate_key (crypto.TYPE_RSA, 2048)

		# create certificate

		self.root_cert = crypto.X509 ()

		self.root_cert.set_pubkey (self.root_key)

		self.root_cert.set_version (2)

		self.root_cert.set_serial_number (
			struct.unpack ("Q", rand.bytes (8)) [0])

		self.root_cert.get_subject ().C = self.data ["country"]
		self.root_cert.get_subject ().L = self.data ["locality"]
		self.root_cert.get_subject ().O = self.data ["organization"]
		self.root_cert.get_subject ().CN = name

		self.root_cert.gmtime_adj_notBefore (0)
		self.root_cert.gmtime_adj_notAfter (315360000)

		self.root_cert.set_issuer (
			self.root_cert.get_subject ())

		self.root_cert.add_extensions ([

			crypto.X509Extension (
				"basicConstraints",
				True,
				"CA:TRUE, pathlen:0"),

			crypto.X509Extension (
				"keyUsage",
				True,
				"keyCertSign, cRLSign"),

			crypto.X509Extension (
				"subjectKeyIdentifier",
				False,
				"hash",
				subject = self.root_cert),

		])

		self.root_cert.add_extensions ([

			crypto.X509Extension (
				"authorityKeyIdentifier",
				False,
				"keyid,issuer:always",
				issuer = self.root_cert)

		])

		# sign certificate

		self.root_cert.sign (self.root_key, "sha256")

		# dump to pem

		self.root_cert_string = crypto.dump_certificate (
			crypto.FILETYPE_PEM,
			self.root_cert)

		self.root_key_string = crypto.dump_privatekey (
			crypto.FILETYPE_PEM,
			self.root_key)

		# write data in "creating" state

		self.root_data = {

			"authority_state":
				"creating",

			"subject_country":
				self.root_cert.get_subject ().C,

			"subject_locality":
				self.root_cert.get_subject ().L,

			"subject_organization":
				self.root_cert.get_subject ().O,

			"subject_common_name":
				self.root_cert.get_subject ().CN,

		}

		self.dnode_client.set_yaml (
			"certificate-authority",
			self.path + "/data",
			self.root_data)

		# write other data

		self.dnode_client.set_raw (
			self.path + "/certificate",
			self.root_cert_string)

		self.dnode_client.set_raw (
			self.path + "/key",
			self.root_key_string)

		self.dnode_client.set_raw (
			self.path + "/serial",
			"0")

		# write data in "active" state

		self.root_data ["authority_state"] = "active"

		self.dnode_client.set_yaml (
			"certificate-authority",
			self.path + "/data",
			self.root_data)

	def load (self):

		self.root_data = self.dnode_client.get_yaml (
			self.path + "/data")

		self.root_cert_string = self.dnode_client.get_raw (
			self.path + "/certificate")

		self.root_key_string = self.dnode_client.get_raw (
			self.path + "/key")

		root_serial_string = self.dnode_client.get_raw (
			self.path + "/serial")

		self.root_cert = crypto.load_certificate (
			crypto.FILETYPE_PEM,
			self.root_cert_string)

		self.root_key = crypto.load_privatekey (
			crypto.FILETYPE_PEM,
			self.root_key_string)

		self.issue_serial = int (root_serial_string)

	def issue (self, type, name, alt_names):

		# check if it exists

		if self.dnode_client.exists (
			self.path + "/named/" + name):

			return False, None, None

		# check type

		if type == "server":

			use_server = True
			use_client = False

			use_string = "serverAuth"

		elif type == "client":

			use_server = False
			use_client = True

			use_string = "clientAuth"

		elif type == "mixed":

			use_server = True
			use_client = True

			use_string = "serverAuth, clientAuth"

		else:

			raise Exception ("Invalid type: %s" % type)

		# increase serial

		issue_serial = self.issue_serial

		issue_path = "%s/issue/%s" % (self.path, issue_serial)

		self.issue_serial += 1

		self.dnode_client.set_raw (
			self.path + "/serial",
			str (self.issue_serial))

		# create key

		issue_key = crypto.PKey ()
		issue_key.generate_key (crypto.TYPE_RSA, 2048)

		# create certificate

		issue_cert = crypto.X509 ()

		issue_cert.set_pubkey (issue_key)

		issue_cert.set_version (2)
		issue_cert.set_serial_number (issue_serial)

		issue_cert.get_subject ().C = self.data ["country"]
		issue_cert.get_subject ().L = self.data ["locality"]
		issue_cert.get_subject ().O = self.data ["organization"]
		issue_cert.get_subject ().CN = name

		issue_cert.gmtime_adj_notBefore (0)
		issue_cert.gmtime_adj_notAfter (315360000)

		issue_cert.set_issuer (self.root_cert.get_subject ())

		issue_cert.add_extensions ([

			crypto.X509Extension (
				"basicConstraints",
				False,
				"CA:FALSE"),

			crypto.X509Extension (
				"keyUsage",
				False,
				"digitalSignature, keyEncipherment"),

			crypto.X509Extension (
				"extendedKeyUsage",
				False,
				use_string),

			crypto.X509Extension (
				"subjectKeyIdentifier",
				False,
				"hash",
				subject = issue_cert),

			crypto.X509Extension (
				"authorityKeyIdentifier",
				False,
				"keyid,issuer:always",
				issuer = self.root_cert),

		])

		if (alt_names):

			issue_cert.add_extensions ([

				crypto.X509Extension (
					"subjectAltName",
					False,
					",".join (alt_names)),

			])

		# sign certificate

		issue_cert.sign (self.root_key, "sha256")

		# dump to pem

		issue_cert_string = crypto.dump_certificate (
			crypto.FILETYPE_PEM,
			issue_cert)

		issue_key_string = crypto.dump_privatekey (
			crypto.FILETYPE_PEM,
			issue_key)

		issue_digest = issue_cert.digest ("sha1")

		# write to database

		self.dnode_client.set_raw (
			issue_path + "/certificate",
			issue_cert_string)

		self.dnode_client.set_raw (
			issue_path + "/key",
			issue_key_string)

		self.dnode_client.set_raw (
			self.path + "/index/" + issue_digest,
			str (issue_serial))

		self.dnode_client.set_raw (
			self.path + "/named/" + name,
			str (issue_serial))

		return True, issue_serial, issue_digest

	def get (self, issue_ref):

		if serial_pattern.match (issue_ref):

			pass

		elif digest_pattern.match (issue_ref):

			issue_serial = self.dnode_client.get_raw (
				"%s/index/%s" % (self.path, issue_ref))

		else:

			issue_serial = self.dnode_client.get_raw (
				"%s/named/%s" % (self.path, issue_ref))

		issue_path = "%s/issue/%s" % (
			self.path,
			issue_serial,
		)

		certificate_string = self.dnode_client.get_raw (
				issue_path + "/certificate")

		key_string = self.dnode_client.get_raw (
			issue_path + "/key")

		return (
			True,
			certificate_string,
			key_string,
		)

	def root_certificate (self):

		return self.root_cert_string

class Database:

	def __init__ (self, dnode_client, path, data):

		self.state = "none"

		self.dnode_client = dnode_client
		self.path = path
		self.data = data

	def exists (self):

		return self.dnode_client.exists (self.path + "/data")

	def create (self):

		if (self.state != "none"):
			raise Exception ()

		if self.dnode_client.exists (self.path + "/data"):
			raise Exception ()

		self.root_data = dict ({})

		self.root_data ["database_state"] = "active"

		self.dnode_client.set_yaml (
			"certificate-database",
			self.path + "/data",
			self.root_data)

	def load (self):

		# nothing much to do at the moment

		pass

	def request (self, name):

		# create key

		request_key = crypto.PKey ()
		request_key.generate_key (crypto.TYPE_RSA, 2048)

		# create certificate

		request_csr = crypto.X509Req ()

		request_csr.set_pubkey (request_key)

		request_csr.set_version (2)

		request_csr.get_subject ().C = self.data ["country"]
		request_csr.get_subject ().ST = "NA"
		request_csr.get_subject ().L = self.data ["locality"]
		request_csr.get_subject ().O = self.data ["organization"]
		request_csr.get_subject ().CN = name

		request_csr.sign (request_key, "sha256")

		# dump to pem

		request_csr_string = crypto.dump_certificate_request (
			crypto.FILETYPE_PEM,
			request_csr)

		request_key_string = crypto.dump_privatekey (
			crypto.FILETYPE_PEM,
			request_key)

		# write to database

		request_path = self.path + "/" + name

		if self.dnode_client.exists (request_path + "/pending"):

			return (False, None, None)

		self.dnode_client.set_raw (
			request_path + "/pending/request",
			request_csr_string)

		self.dnode_client.set_raw (
			request_path + "/pending/key",
			request_key_string)

		return (
			True,
			request_csr_string,
			request_key_string,
		)

	def cancel (self, name):

		request_path = self.path + "/" + name

		# sanity check

		if not self.dnode_client.exists (request_path + "/pending"):

			return False

		# read pending

		request_csr_string = self.dnode_client.get_raw (
			request_path + "/pending/request")

		request_key_string = self.dnode_client.get_raw (
			request_path + "/pending/key")

		# create cancelled

		cancelled_path, cancelled_index = self.dnode_client.make_queue_dir (
			request_path + "/cancelled")

		self.dnode_client.set_raw (
			cancelled_path + "/request",
			request_csr_string)

		self.dnode_client.set_raw (
			cancelled_path + "/key",
			request_key_string)

		# remove pending

		self.dnode_client.rm_raw (
			request_path + "/pending/request")

		self.dnode_client.rm_raw (
			request_path + "/pending/key")

		self.dnode_client.rmdir_raw (
			request_path + "/pending")

		return True

	def signed (self,
			name,
			certificate_strings,
			verify_subject,
			verify_common_name):

		request_path = self.path + "/" + name

		# sanity check

		if not self.dnode_client.exists (request_path + "/pending"):

			raise Error ("No request pending")

		# read pending

		request_csr_string = self.dnode_client.get_raw (
			request_path + "/pending/request")

		request_key_string = self.dnode_client.get_raw (
			request_path + "/pending/key")

		request_csr = crypto.load_certificate_request (
			crypto.FILETYPE_PEM,
			request_csr_string)

		request_key = crypto.load_privatekey (
			crypto.FILETYPE_PEM,
			request_key_string)

		# read chain

		certificates = [

			crypto.load_certificate (
				crypto.FILETYPE_PEM,
				certificate_string)

			for certificate_string
				in certificate_strings

		]

		# verify chain

		if not request_csr.verify (certificates [0].get_pubkey ()):

			raise Exception (
				"Public key of certificate does not match request")

		if verify_subject \
		and request_csr.get_subject () \
			!= certificates [0].get_subject ():

			raise Exception (
				"Subject of certificate does not match request")

		if verify_common_name \
		and request_csr.get_subject ().CN \
			!= certificates [0].get_subject ().CN:

			raise Exception (
				"Common name of certificate does not match request")

		for child, parent in zip (
			certificates [:-1],
			certificates [1:]):

			if not child.get_issuer () == parent.get_subject ():

				raise Exception (
					"Certificate chain subjects and issues do not match")

		if certificates [-1].get_issuer () != certificates [-1].get_subject ():

			raise Exception (
				"Root certificate is not self-signed")

		# TODO verify the actual signatures of the chain

		# archive existing certificate

		if self.dnode_client.exists (request_path + "/current"):

			raise Exception ("TODO need to move chain somehow")

			# read current

			archive_csr_string = self.dnode_client.get_raw (
				request_path + "/current/request")

			archive_certificate_string = self.dnode_client.get_raw (
				request_path + "/current/certificate")

			archive_key_string = self.dnode_client.get_raw (
				request_path + "/current/key")

			# write to archive

			archive_path, archive_index = self.dnode_client.make_queue_dir (
				request_path + "/archive")

			self.dnode_client.set_raw (
				archive_path + "/request",
				archive_csr_string)

			self.dnode_client.set_raw (
				archive_path + "/certificate",
				archive_certificate_string)

			self.dnode_client.set_raw (
				archive_path + "/key",
				archive_key_string)

			# remove current

			self.dnode_client.rm_raw (
				request_path + "/current/request")

			self.dnode_client.rm_raw (
				request_path + "/current/certificate")

			self.dnode_client.rm_raw (
				request_path + "/current/key")

			self.dnode_client.rmdir_raw (
				request_path + "/current")

		# store new certificate

		self.dnode_client.set_raw (
			request_path + "/current/request",
			request_csr_string)

		self.dnode_client.set_raw (
			request_path + "/current/key",
			request_key_string)

		self.dnode_client.set_raw (
			request_path + "/current/certificate",
			certificate_strings [0])

		for chain_index, chain_string \
			in enumerate (certificate_strings [1:]):

			self.dnode_client.set_raw (
				request_path + "/current/chain/" + str (chain_index),
				chain_string)

		# remove pending

		self.dnode_client.rm_raw (
			request_path + "/pending/request")

		self.dnode_client.rm_raw (
			request_path + "/pending/key")

		self.dnode_client.rmdir_raw (
			request_path + "/pending")
