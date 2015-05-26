from __future__ import absolute_import

import os

support = __import__ (os.environ ["WBS_DEVOPS_TOOLS_SUPPORT"]).support

class CallbackModule (object):

	def runner_on_ok (self, record_name, result):

		if result ["invocation"] ["module_name"] != "set_fact":
			return

		self.store_facts (record_name, result ["ansible_facts"])

	def store_facts (self, record_name, facts):

		found_records = []

		for collection in support.context.collections:

			if not collection.exists (record_name):
				continue

			found_records.append ((
				collection,
				collection.get (record_name),
			))

		if not found_records:
			raise Exception ("Not found: " + record_name)

		if len (found_records) > 1:
			raise Exception ("Found multiple")

		collection, record_data = found_records [0]

		for key, value in facts.items ():
			record_data [key] = value

		collection.set (record_name, record_data)
