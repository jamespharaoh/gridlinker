from __future__ import absolute_import

import itertools
import os
import re
import struct
import sys

from OpenSSL import crypto, rand

from wbsdevops.certificate.certificate import Certificate

from wbsmisc import SchemaField, SchemaGroup

serial_pattern = re.compile (
	r"^[1-9]\d*$")

digest_pattern = re.compile (
	r"^\d{2}(:\d{2})*$")

class AlreadyExistsError (Exception):
	pass

class IllegalStateError (Exception):
	pass

class CertificateAuthority:

	def __init__ (self, context, path, certificate_data):

		self.state = "none"

		self.context = context
		self.client = context.client
		self.schemas = context.schemas

		self.path = path
		self.certificate_data = certificate_data

	def create (self, name):

		if self.state != "none":
			raise IllegalStateError ()

		# sanity check

		if self.client.exists (self.path):
			raise AlreadyExistsError ()

		# create key

		self.root_key = crypto.PKey ()
		self.root_key.generate_key (crypto.TYPE_RSA, 2048)

		# create certificate

		self.root_cert = crypto.X509 ()

		self.root_cert.set_pubkey (self.root_key)

		self.root_cert.set_version (2)

		self.root_cert.set_serial_number (
			struct.unpack ("Q", rand.bytes (8)) [0])

		self.root_cert.get_subject ().C = self.certificate_data ["country"]
		self.root_cert.get_subject ().L = self.certificate_data ["locality"]
		self.root_cert.get_subject ().O = self.certificate_data ["organization"]
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

		self.data = {

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

		self.client.set_yaml (
			self.path + "/data",
			self.data,
			self.schemas ["certificate-authority"])

		# write other data

		self.client.set_raw (
			self.path + "/certificate",
			self.root_cert_string)

		self.client.set_raw (
			self.path + "/key",
			self.root_key_string)

		self.client.set_raw (
			self.path + "/serial",
			"0")

		# write data in "active" state

		self.data ["authority_state"] = "active"

		self.client.set_yaml (
			self.path + "/data",
			self.data,
			self.schemas ["certificate-authority"])

	def load (self):

		self.data = self.client.get_yaml (
			self.path + "/data")

		self.root_cert_string = self.client.get_raw (
			self.path + "/certificate")

		self.root_key_string = self.client.get_raw (
			self.path + "/key")

		root_serial_string = self.client.get_raw (
			self.path + "/serial")

		self.root_cert = crypto.load_certificate (
			crypto.FILETYPE_PEM,
			self.root_cert_string)

		self.root_key = crypto.load_privatekey (
			crypto.FILETYPE_PEM,
			self.root_key_string)

		self.issue_serial = int (root_serial_string)

	def issue (self, type, name, alt_names):

		if self.client.exists (
			self.path + "/named/" + name):

			raise AlreadyExistsError ()

		else:

			return self.reissue (type, name, alt_names)

	def reissue (self, type, name, alt_names):

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

			raise IllegalArgumentError ()

		# increase serial

		issue_serial = self.issue_serial

		issue_path = "%s/issue/%s" % (self.path, issue_serial)

		self.issue_serial += 1

		self.client.set_raw (
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

		issue_cert.get_subject ().C = self.certificate_data ["country"]
		issue_cert.get_subject ().L = self.certificate_data ["locality"]
		issue_cert.get_subject ().O = self.certificate_data ["organization"]
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

		self.client.set_raw (
			issue_path + "/digest",
			issue_digest)

		self.client.set_raw (
			issue_path + "/certificate",
			issue_cert_string)

		self.client.set_raw (
			issue_path + "/key",
			issue_key_string)

		self.client.set_raw (
			self.path + "/index/" + issue_digest,
			str (issue_serial))

		self.client.set_raw (
			self.path + "/named/" + name,
			str (issue_serial))

		return Certificate (
			serial = issue_serial,
			digest = issue_digest,
			certificate = issue_cert_string,
			private_key = issue_key_string,
			certificate_path = issue_path + "/certificate",
			private_key_path = issue_path + "/key")

	def get (self, issue_ref):

		if serial_pattern.match (issue_ref):

			pass

		elif digest_pattern.match (issue_ref):

			issue_serial = self.client.get_raw (
				"%s/index/%s" % (self.path, issue_ref))

		else:

			issue_serial = self.client.get_raw (
				"%s/named/%s" % (self.path, issue_ref))

		issue_path = "%s/issue/%s" % (
			self.path,
			issue_serial,
		)

		issue_digest = self.client.get_raw (
			issue_path + "/digest")

		certificate_string = self.client.get_raw (
			issue_path + "/certificate")

		key_string = self.client.get_raw (
			issue_path + "/key")

		return Certificate (
			serial = issue_serial,
			digest = issue_digest,
			certificate = certificate_string,
			private_key = key_string,
			certificate_path = issue_path + "/certificate",
			private_key_path = issue_path + "/key")

	def root_certificate (self):

		return self.root_cert_string

def args (prev_sub_parsers):

	parser = prev_sub_parsers.add_parser (
		"authority",
		help = "manage a certificate authority",
		description = """
			This tool manages a certificate authority, along with a record of
			the certificates which have been issued and revoked, including the
			private key when appropriate. It is able to generate certificates
			along with private keys, or to sign requests (CSRs) which are
			generated elsewhere. It is also able to revoke certificates and to
			publish signed lists of revoked certificates (CRL).
		""")

	next_sub_parsers = parser.add_subparsers ()

	args_create (next_sub_parsers)
	args_issue (next_sub_parsers)
	args_export (next_sub_parsers)
	args_revoke (next_sub_parsers)
	args_crl (next_sub_parsers)
	args_sign (next_sub_parsers)

def args_create (sub_parsers):

	parser = sub_parsers.add_parser (
		"create",
		help = "create a new certificate authority",
		description = """
			This tool creates a new certificate authority. A private key and
			self-signed certificate will be generated and other metadata will be
			initialised.
		""")

	parser.set_defaults (
		func = do_create)

	parser.add_argument (
		"--authority",
		required = True,
		help = "name of the certificate authority to create")

	parser.add_argument (
		"--common-name",
		required = True,
		help = "common name to use in the subject of the certificate authority")

def do_create (context, args):

	authority = CertificateAuthority (
		context,
		"/authority/" + args.authority,
		context.certificate_data)

	authority.create (args.common_name)

	print "Created certificate authority %s" % args.authority

def args_issue (sub_parsers):

	parser = sub_parsers.add_parser (
		"issue",
		help = "issue a new certificate and key",
		description = """
			This tool issues a new certificate along with a private key which
			is generated locally. This is normally used when the certificate is
			to be used by a subordinate, such as an employee or a server
			belonging to the entity that controls the certificate authority.
		""")

	parser.set_defaults (
		func = do_issue)

	parser.add_argument (
		"--authority",
		required = True,
		help = "name of issuing certificate authority")

	parser.add_argument (
		"--common-name",
		required = True,
		help = "common name to use in subject")

	# type

	parser_type = parser.add_mutually_exclusive_group (
		required = True)

	parser_type.add_argument (
		"--server",
		help = "server usage only",
		action = "store_const",
		const = "server",
		dest = "type")

	parser_type.add_argument (
		"--client",
		help = "client usage only",
		action = "store_const",
		const = "client",
		dest = "type")

	parser_type.add_argument (
		"--mixed",
		help = "server or client usage",
		action = "store_const",
		const = "mixed",
		dest = "type")

	# store

	parser_store = parser.add_argument_group (
		"store")

	parser_store.add_argument (
		"--store-host",
		help = "TODO")

	parser_store.add_argument (
		"--store-certificate",
		help = "TODO")

	parser_store.add_argument (
		"--store-private-key",
		help = "TODO")

	# alt names

	parser_alt_names = parser.add_argument_group (
		"alt names")

	parser_alt_names.add_argument (
		"--alt-dns",
		help = "alternative dns hostname",
		default = [],
		action = "append")

	parser_alt_names.add_argument (
		"--alt-ip",
		help = "alternative ip address",
		default = [],
		action = "append")

	parser_alt_names.add_argument (
		"--alt-email",
		help = "alternative email address",
		default = [],
		action = "append")

def do_issue (context, args):

	authority = context.authorities [args.authority]

	alt_names = list (itertools.chain.from_iterable ([
		[ "DNS:" + alt_dns for alt_dns in args.alt_dns ],
		[ "IP:" + alt_ip for alt_ip in args.alt_ip ],
		[ "email:" + alt_email for alt_email in args.alt_email ],
	]))

	try:

		certificate = authority.issue (
			args.type,
			args.common_name,
			alt_names)

	except AlreadyExistsError:

		print "Certificate already exists for %s" % (
			args.common_name)

		sys.exit (1)

	print "Issued certificate %s %s %s" % (
		certificate.serial,
		certificate.digest,
		args.common_name)

	if args.store_host:

		host_data = context.hosts.get (args.store_host)

		if args.store_certificate:
			host_data [args.store_certificate] = certificate.certificate_path

		if args.store_private_key:
			host_data [args.store_private_key] = certificate.private_key_path

		context.hosts.set (args.store_host, host_data)

		print "Stored certificate in host %s" % (
			args.store_host)

def args_export (sub_parsers):

	parser = sub_parsers.add_parser (
		"export",
		help = "export a certificate, key, chain, etc",
		description = """
			This tool writes out the certificate and associated information for
			one of the certificates issued by this authority.
		""")

	parser.set_defaults (
		func = do_export)

	parser.add_argument (
		"--authority",
		required = True,
		help = "name of issuing certificate authority")

	parser.add_argument (
		"--common-name",
		required = True,
		help = "common name of certificate to export")

	parser.add_argument (
		"--certificate",
		required = False,
		help = "file to write the issued certificate only")

	parser.add_argument (
		"--certificate-and-chain",
		required = False,
		help = "file to write the issued certificate and chain")

	parser.add_argument (
		"--chain",
		required = False,
		help = "file to write the chain only")

	parser.add_argument (
		"--private-key",
		required = False,
		help = "filename to write the private key")

def do_export (context, args):

	authority = context.authorities [args.authority]

	try:

		certificate = authority.get (
			args.common_name)

	except KeyError:

		print "not found"
		sys.exit (1)

	if args.certificate:

		with open (args.certificate, "w") as file_handle:

			file_handle.write (certificate.certificate)

		print "Wrote certificate to %s" % (
			args.certificate)

	if args.chain:

		with open (args.chain, "w") as file_handle:

			file_handle.write (authority.root_certificate ())

		print "Wrote chain to %s" % (
			args.chain)

	if args.certificate_and_chain:

		with open (args.certificate_and_chain, "w") as file_handle:

			file_handle.write (certificate.certificate)
			file_handle.write (authority.root_certificate ())

		print "Wrote certificate and chain to %s" % (
			args.certificate_and_chain)

	if args.private_key:

		with open (args.private_key, "w") as file_handle:

			os.fchmod (file_handle.fileno (), 0600)

			file_handle.write (certificate.private_key)

		print "Wrote private key to %s" % (
			args.private_key)

def args_revoke (sub_parsers):

	parser = sub_parsers.add_parser (
		"revoke",
		help = "revoke a previously issued certificate",
		description = """
			This tool revokes a certificate which was previously issued by this
			certificate authority. For this to take effect, some method must be
			implemented to communicate the revocation list to the appropriate
			parties and to ensure that they actively verify certificates against
			it.
		""")

	parser.set_defaults (
		func = do_revoke)

	parser.add_argument (
		"--authority",
		required = True,
		help = "name of revoking certificate authority")

def do_revoke (context, args):

	raise Exception ("TODO")

def args_crl (sub_parsers):

	parser = sub_parsers.add_parser (
		"crl",
		help = "create a \"certificate revocation list\"",
		description = """
			This tool writes out a signed list of certificates which have been
			issued and then subsequently revoked by this certificate authority,
			commonly known as a "certificate revocation list\". This can be
			distributed to entities which need to verify certificates issued by
			this authority so that revoked certificates can be identified and
			their use prohibited.
		""")

	parser.set_defaults (
		func = do_crl)

	parser.add_argument (
		"--authority",
		required = True,
		help = "name of issuing certificate authority")

def do_crl (context, args):

	raise Exception ("TODO")

def args_sign (sub_parsers):

	parser = sub_parsers.add_parser (
		"sign",
		help = "sign a \"certificate signing request\"",
		description = """
			This tool is used to generated a signed certificate, corresponding
			to a certificate signing request generated by a third party. This
			should be used when the entity which controls the certificate
			authority and the entity to which the certificate is being issued
			are distinct, and it allows the private key to be generated by the
			entity to which the certificate is being issued without ever
			revealing it to the certificate authority.
		""")

	parser.set_defaults (
		func = do_sign)

	parser.add_argument (
		"--authority",
		required = True,
		help = "name of signing certificate authority")

def do_sign (context, args):

	raise Exception ("TODO")
