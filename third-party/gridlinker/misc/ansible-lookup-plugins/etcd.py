from __future__ import absolute_import
from __future__ import unicode_literals

import importlib
import os

#from ansible import utils

from ansible.plugins.lookup import LookupBase

class LookupModule (LookupBase):

	def __init__ (self, * arguments, ** keyword_arguments):

		self.support = importlib.import_module (
			os.environ ["GRIDLINKER_SUPPORT"]).support

		self.context = self.support.get_context ()

		self.client = self.context.client

		LookupBase.__init__ (
			self,
			* arguments,
			** keyword_arguments)

	def run (self, terms, variables, ** keyword_arguments):

		ret = []

		for term in terms:

			key = term.split () [0]

			value = self.client.get_raw (key)

			ret.append (value)

		return ret

# ex: noet ts=4 filetype=python
