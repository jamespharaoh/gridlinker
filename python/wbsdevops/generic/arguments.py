from __future__ import absolute_import

from wbsmisc import generate_password

class ArgumentGroup:

	def __init__ (self, label, arguments):

		self.label = label
		self.arguments = arguments

	def args_create (self, parser, helper):

		group = parser.add_argument_group (self.label)

		for argument in self.arguments:
			argument.args_create (group, helper)

	def args_update (self, parser, helper):

		group = parser.add_argument_group (self.label)

		for argument in self.arguments:
			argument.args_create (group, helper)

	def update_record (self, arg_vars, record_data, helper):

		for argument in self.arguments:
			argument.update_record (arg_vars, record_data, helper)

	def update_files (self, arg_vars, collection, helper):

		for argument in self.arguments:
			argument.update_files (arg_vars, collection, helper)

class SimpleArgument:

	def __init__ (self, argument, required, key, value_name, help):

		self.argument = argument
		self.key = key
		self.value_name = value_name
		self.help = help

		self.required = required

		self.argument_name = argument [2:].replace ("-", "_")

	def args_create (self, parser, helper):

		parser.add_argument (
			self.argument,
			metavar = self.value_name,
			help = self.help)

	def args_update (self, parser, helper):

		parser.add_argument (
			self.argument,
			metavar = self.value_name,
			help = self.help)

	def update_record (self, arg_vars, record_data, helper):

		value = arg_vars [self.argument_name]

		if value:
			record_data [self.key] = value

	def update_files (self, arg_vars, collection, helper):

		pass

class GroupArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--group",
			required = False,
			metavar = "GROUP",
			help = "group this %s belongs to" % helper.name)

	def args_update (self, parser, helper):

		pass

	def update_record (self, arg_vars, record_data, helper):

		value = arg_vars ["group"]

		if value:
			record_data ["%s_group" % helper.short_name] = value

	def update_files (self, arg_vars, collection, helper):

		pass

class AddListArgument:

	def __init__ (self, argument, key, help, value_name):

		self.argument = argument
		self.key = key
		self.help = help
		self.value_name = value_name

		self.argument_name = argument [2:].replace ("-", "_")

	def args_create (self, parser, helper):

		parser.add_argument (
			self.argument,
			action = "append",
			default = [],
			help = self.help,
			metavar = self.value_name)

	def args_update (self, parser, helper):

		parser.add_argument (
			self.argument,
			action = "append",
			default = [],
			help = self.help,
			metavar = self.value_name)

	def update_record (self, arg_vars, record_data, helper):

		for value in arg_vars [self.argument_name]:

			if not self.key in record_data:
				record_data [self.key] = []

			record_data [self.key].append (value)

	def update_files (self, arg_vars, collection, helper):

		pass

class AddDictionaryArgument:

	def __init__ (self, argument, key, help, key_name, value_name):

		self.argument = argument
		self.key = key
		self.help = help
		self.key_name = key_name
		self.value_name = value_name

		self.argument_name = argument [2:].replace ("-", "_")

	def args_create (self, parser, helper):

		parser.add_argument (
			self.argument,
			action = "append",
			default = [],
			nargs = 2,
			help = self.help,
			metavar = (self.key_name, self.value_name))

	def args_update (self, parser, helper):

		parser.add_argument (
			self.argument,
			action = "append",
			default = [],
			nargs = 2,
			help = self.help,
			metavar = (self.key_name, self.value_name))

	def update_record (self, arg_vars, record_data, helper):

		for key, value in arg_vars [self.argument_name]:

			if not self.key in record_data:
				record_data [self.key] = {}

			record_data [self.key] [key] = value

	def update_files (self, arg_vars, collection, helper):

		pass

class NameArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--name",
			required = True,
			help = "name of %s to create" % helper.name)

	def args_update (self, parser, helper):

		parser.add_argument (
			"--name",
			required = True,
			help = "name of %s to update" % helper.name)

	def update_record (self, arg_vars, record_data, helper):

		record_data ["%s_name" % helper.short_name] = arg_vars ["name"]

	def update_files (self, arg_vars, collection, helper):

		pass

class FileArgument:

	def __init__ (self, argument, path, help):

		self.argument = argument
		self.path = path
		self.help = help

		self.argument_name = argument [2:].replace ("-", "_")

	def args_create (self, parser, helper):

		parser.add_argument (
			self.argument,
			metavar = "FILE",
			help = self.help)

	def args_update (self, parser, helper):

		parser.add_argument (
			self.argument,
			metavar = "FILE",
			help = self.help)

	def update_record (self, arg_vars, record_data, helper):

		pass

	def update_files (self, arg_vars, collection, helper):

		value = arg_vars [self.argument_name]

		if not value:
			return

		with open (value) as file_handle:
			file_contents = file_handle.read ()

		collection.set_file (arg_vars ["name"], self.path, file_contents)

class MiscSetArgument:

	def __init__ (self):

		pass

	def args_create (self, parser, helper):

		parser.add_argument (
			"--set",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("KEY", "VALUE"),
			help = "miscellaneous value to store")

	def args_update (self, parser, helper):

		parser.add_argument (
			"--set",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("KEY", "VALUE"),
			help = "miscellaneous value to store")

	def update_record (self, arg_vars, record_data, helper):

		for key, value in arg_vars ["set"]:
			record_data [key] = value

	def update_files (self, arg_vars, collection, helper):

		pass

class MiscUnsetArgument:

	def __init__ (self):

		pass

	def args_create (self, parser, helper):

		parser.add_argument (
			"--unset",
			action = "append",
			default = [],
			metavar = "KEY",
			help = "miscellaneous value to unset")

	def args_update (self, parser, helper):

		parser.add_argument (
			"--set",
			action = "append",
			default = [],
			metavar = "KEY",
			help = "miscellaneous value to unset")

	def update_record (self, arg_vars, record_data, helper):

		for key in arg_vars ["unset"]:
			if key in record_data:
				del record_data [key]

	def update_files (self, arg_vars, collection, helper):

		pass

class MiscRemoveArgument:

	def __init__ (self):

		pass

	def args_create (self, parser, helper):

		parser.set_defaults (
			remove = [])

	def args_update (self, parser, helper):

		parser.add_argument (
			"--remove",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("KEY", "VALUE"),
			help = "miscellaneous value to remove from list")

	def update_record (self, arg_vars, record_data, helper):

		for key, value in arg_vars ["remove"]:

			if not key in record_data:
				return

			record_data [key].remove (value)

	def update_files (self, arg_vars, collection, helper):

		pass

class MiscAddArgument:

	def __init__ (self):

		pass

	def args_create (self, parser, helper):

		parser.add_argument (
			"--add",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("KEY", "VALUE"),
			help = "miscellaneous value to add to list")

	def args_update (self, parser, helper):

		parser.add_argument (
			"--add",
			action = "append",
			nargs = 2,
			default = [],
			help = "miscellaneous value to add to list")

	def update_record (self, arg_vars, record_data, helper):

		for key, value in arg_vars ["add"]:

			if not key in record_data:
				record_data [key] = []

			record_data [key].append (value)

	def update_files (self, arg_vars, collection, helper):

		pass

class GeneratePasswordArgument:

	def __init__ (self):

		pass

	def args_create (self, parser, helper):

		parser.add_argument (
			"--generate-password",
			action = "append",
			default = [],
			metavar = "KEY",
			help = "generate random password to store")

	def args_update (self, parser, helper):

		parser.add_argument (
			"--generate-password",
			action = "append",
			default = [],
			metavar = "KEY",
			help = "generate random password to store")

	def update_record (self, arg_vars, record_data, helper):

		for key in arg_vars ["generate_password"]:
			record_data [key] = generate_password ()

	def update_files (self, arg_vars, collection, helper):

		pass
