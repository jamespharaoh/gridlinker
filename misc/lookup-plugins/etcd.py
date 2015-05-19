import etcd
import os
import sys

from ansible import utils

HOME = os.path.abspath (os.path.dirname (__file__) + "/../..")

sys.path.append (HOME + "/tools")

import dnode.client

class LookupModule (object):

	def __init__ (self, basedir = None, ** kwargs):

		self.basedir = basedir

		self.etcd_client = dnode.client.DnodeClient ()

	def run (self, terms, inject = None, ** kwargs):

		terms = utils.listify_lookup_plugin_terms (
			terms,
			self.basedir,
			inject)

		if isinstance (terms, basestring):
			terms = [ terms ]

		ret = []

		for term in terms:

			key = term.split () [0]

			value = self.etcd_client.get_raw (key)

			ret.append (value)

		return ret

# ex: noet ts=4 filetype=python
