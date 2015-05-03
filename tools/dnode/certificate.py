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

		root_cert_string = crypto.dump_certificate (
			crypto.FILETYPE_PEM,
			self.root_cert)

		root_key_string = crypto.dump_privatekey (
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
			root_cert_string)

		self.dnode_client.set_raw (
			self.path + "/key",
			root_key_string)

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

		root_cert_string = self.dnode_client.get_raw (
			self.path + "/certificate")

		root_key_string = self.dnode_client.get_raw (
			self.path + "/key")

		root_serial_string = self.dnode_client.get_raw (
			self.path + "/serial")

		self.root_cert = crypto.load_certificate (
			crypto.FILETYPE_PEM,
			root_cert_string)

		self.root_key = crypto.load_privatekey (
			crypto.FILETYPE_PEM,
			root_key_string)

		self.issue_serial = int (root_serial_string)

	def issue (self, type, name, alt_names):

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

		return issue_serial, issue_digest

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

		issue_certificate_text = self.dnode_client.get_raw (
			issue_path + "/certificate")

		issue_key_text = self.dnode_client.get_raw (
			issue_path + "/key")

		return (
			issue_certificate_text,
			issue_key_text,
		)

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

	def request (self, name, alt_names):

		# create key

		request_key = crypto.PKey ()
		request_key.generate_key (crypto.TYPE_RSA, 2048)

		# create certificate

		request_csr = crypto.X509Req ()

		request_csr.set_pubkey (request_key)

		request_csr.set_version (2)

		request_csr.get_subject ().C = self.data ["country"]
		request_csr.get_subject ().L = self.data ["locality"]
		request_csr.get_subject ().O = self.data ["organization"]
		request_csr.get_subject ().CN = name

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
