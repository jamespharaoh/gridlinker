from __future__ import absolute_import

import collections

Certificate = collections.namedtuple ("Certificate", [
	"serial",
	"digest",
	"certificate",
	"private_key",
	"certificate_path",
	"private_key_path",
])

def args (sub_parsers):

	pass

def schemas (schemas):

	pass
