from __future__ import absolute_import
from __future__ import unicode_literals

import importlib
import os

from ansible.plugins.action import ActionBase

class ActionModule (ActionBase):

	TRANSFERS_FILES = False

	def __init__ (self, * arguments, ** keyword_arguments):

		ActionBase.__init__ (
			self,
			* arguments,
			** keyword_arguments)

	def run (self, tmp = None, task_vars = dict ()):

		changed = False

		for key, value in self._task.args.items ():

			dynamic_path = (
				self._templar.template (
					key))

			if not "." in dynamic_path:

				raise Exception (
					"Invalid path for update_resource: %s" % dynamic_path)

			prefix, rest = (
				dynamic_path.split (".", 2))

			options [prefix] [rest] = value
			options [prefix + "_" + rest] = value

			changed = True

		return dict (
			ansible_facts = options,
			changed = changed)

# ex: noet ts=4 filetype=python
