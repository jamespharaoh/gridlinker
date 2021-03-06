from __future__ import absolute_import
from __future__ import unicode_literals

import json

from collections import OrderedDict

from wbs import generate_password

class ArgumentGroup:

	def __init__ (self, label, arguments):

		self.label = label
		self.arguments = arguments

	def args_create (self, parser, helper):

		group = parser.add_argument_group (
			self.label)

		for argument in self.arguments:
			if hasattr (argument, "args_create"):
				argument.args_create (group, helper)

	def args_edit (self, parser, helper):

		group = parser.add_argument_group (
			self.label)

		for argument in self.arguments:
			if hasattr (argument, "args_edit"):
				argument.args_edit (group, helper)

	def args_list (self, parser, helper):

		group = parser.add_argument_group (
			self.label)

		for argument in self.arguments:
			if hasattr (argument, "args_list"):
				argument.args_list (group, helper)

	def args_remove (self, parser, helper):

		group = parser.add_argument_group (
			self.label)

		for argument in self.arguments:
			if hasattr (argument, "args_remove"):
				argument.args_remove (group, helper)

	def args_show (self, parser, helper):

		group = parser.add_argument_group (
			self.label)

		for argument in self.arguments:
			if hasattr (argument, "args_show"):
				argument.args_show (group, helper)

	def args_update (self, parser, helper):

		group = parser.add_argument_group (
			self.label)

		for argument in self.arguments:
			if hasattr (argument, "args_update"):
				argument.args_update (group, helper)

	def update_record (self, arg_vars, record_data, context, helper):

		for argument in self.arguments:
			if hasattr (argument, "update_record"):
				argument.update_record (arg_vars, record_data, context, helper)

	def update_files (self, arg_vars, unique_name, context, helper):

		for argument in self.arguments:
			if hasattr (argument, "update_files"):
				argument.update_files (arg_vars, unique_name, context, helper)

	def filter_record (self, arg_vars, record_name, record_data, context, helper):

		for argument in self.arguments:

			if hasattr (argument, "filter_record"):

				if not argument.filter_record (
						arg_vars,
						record_name,
						record_data,
						context,
						helper):

					return False

		return True

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

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("self.argument_name") == None:
			return

		if arg_vars.get ("self.argument_name") == None:
			return

		value = arg_vars [self.argument_name]

		if value:
			record_data [self.key] = value

class ClassArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--class",
			required = False,
			metavar = "CLASS",
			help = "class this {0} belongs to".format (helper.name))

	def args_edit (self, parser, helper):

		parser.add_argument (
			"--class",
			required = False,
			metavar = "CLASS",
			help = "class to edit {0}s belonging to".format (helper.name))

	def args_list (self, parser, helper):

		parser.add_argument (
			"--class",
			required = False,
			metavar = "CLASS",
			help = "Class to list {0}s belong to".format (helper.name))

	def args_update (self, parser, helper):

		parser.add_argument (
			"--class",
			required = False,
			metavar = "CLASS",
			help = "class of {0} to update".format (helper.name))

	def args_show (self, parser, helper):

		parser.add_argument (
			"--class",
			required = False,
			metavar = "CLASS",
			help = "class of {0} to show".format (helper.name))

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("class") == None:
			return

		value = arg_vars ["class"]

		if value:
			record_data ["identity"] ["class"] = value

	def filter_record (self, arg_vars, record_name, record_data, context, helper):

		if arg_vars.get ("class") == None:
			return True

		return record_data ["identity"] ["class"] == arg_vars ["class"]

class NamespaceArgument:

	def args_list (self, parser, helper):

		parser.add_argument (
			"--namespace",
			required = False,
			metavar = "NAMESPACE",
			help = "Namsepace to list {0}s belong to".format (helper.name))

	def args_update (self, parser, helper):

		parser.add_argument (
			"--namespace",
			required = False,
			metavar = "NAMESPACE",
			help = "Namespace of {0}s to update".format (helper.name))

	def filter_record (self, arg_vars, record_name, record_data, context, helper):

		if arg_vars.get ("namespace") == None:
			return True

		class_name = record_data ["identity"] ["class"]
		class_data = context.local_data ["classes"] [class_name]

		return class_data ["class"] ["namespace"] == arg_vars ["namespace"]

class ParentArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--set-parent",
			required = False,
			metavar = "PARENT",
			help = "set parent in newly created {0}".format (helper.name))

	def args_list (self, parser, helper):

		parser.add_argument (
			"--parent",
			required = False,
			metavar = "PARENT",
			help = "list {0}s with this parent".format (helper.name))

	def args_update (self, parser, helper):

		parser.add_argument (
			"--parent",
			required = False,
			metavar = "PARENT",
			help = "update {0}s with this parent".format (helper.name))

		parser.add_argument (
			"--set-parent",
			required = False,
			metavar = "PARENT",
			help = "set parent in updated {0}".format (helper.name))

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("set_parent") == None:
			return

		value = arg_vars ["set_parent"]

		if value:
			record_data ["identity"] ["parent"] = value

	def filter_record (self, arg_vars, record_name, record_data, context, helper):

		if arg_vars.get ("parent") == None:
			return True

		if not "parent" in record_data ["identity"]:
			return False

		class_name = record_data ["identity"] ["class"]
		class_data = context.local_data ["classes"] [class_name]

		if not "parent_namespace" in class_data ["class"]:
			return False

		parent_name = "/".join ([
			class_data ["class"] ["parent_namespace"],
			record_data ["identity"] ["parent"],
		])

		return parent_name == arg_vars ["parent"]

class IndexArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--index",
			required = False,
			metavar = "INDEX",
			help = "index of this %s" % helper.name)

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("index") == None:
			return

		value = arg_vars ["index"]

		if value:
			record_data ["identity"] ["index"] = value

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

	def update_record (self, arg_vars, record_data, context, helper):

		for value in arg_vars [self.argument_name]:

			if not self.key in record_data:
				record_data [self.key] = []

			record_data [self.key].append (value)

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

	def update_record (self, arg_vars, record_data, context, helper):

		for key, value in arg_vars [self.argument_name]:

			if not self.key in record_data:
				record_data [self.key] = {}

			record_data [self.key] [key] = value

class NameArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--name",
			required = True,
			dest = "name",
			metavar = "NAME",
			help = "name of %s to create" % helper.name)

	def args_edit (self, parser, helper):

		parser.add_argument (
			"--name",
			required = True,
			metavar = "NAME",
			help = "name of %s to edit" % helper.name)

	def args_remove (self, parser, helper):

		parser.add_argument (
			"--name",
			required = False,
			metavar = "NAME",
			help = "name of %s to remove" % helper.name)

	def args_show (self, parser, helper):

		parser.add_argument (
			"--name",
			required = False,
			metavar = "NAME",
			help = "name of %s to show" % helper.name)

	def args_update (self, parser, helper):

		parser.add_argument (
			"--name",
			required = False,
			metavar = "NAME",
			help = "name of %s to update" % helper.name)

	def filter_record (self, arg_vars, record_name, record_data, context, helper):

		if arg_vars.get ("name") == None:
			return True

		return record_name == arg_vars ["name"]

class MiscSetFileArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--set-file",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("NAME", "SOURCE"),
			help = "miscellaneous file to store")

	def args_update (self, parser, helper):

		parser.add_argument (
			"--set-file",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("NAME", "SOURCE"),
			help = "miscellaneous file to store")

	def update_files (self, arg_vars, unique_name, context, helper):

		collection = helper.get_collection (context)

		value = arg_vars ["set_file"]

		if not value:
			return

		for name, source in value:

			with open (source) as file_handle:
				file_contents = file_handle.read ()

			collection.set_file (unique_name, name, file_contents)

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

	def update_files (self, arg_vars, unique_name, context, helper):

		collection = helper.get_collection ()

		value = arg_vars [self.argument_name]

		if not value:
			return

		with open (value) as file_handle:
			file_contents = file_handle.read ()

		collection.set_file (unique_name, self.path, file_contents)

class MiscSetArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--set",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("GROUP.KEY", "VALUE"),
			help = "miscellaneous value to store")

	def args_update (self, parser, helper):

		parser.add_argument (
			"--set",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("GROUP.KEY", "VALUE"),
			help = "miscellaneous value to store")

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("set") == None:
			return

		if arg_vars.get ("set") == None:
			return

		for section_key, value in arg_vars ["set"]:

			section, key = section_key.split (".")

			if not section in record_data:
				record_data [section] = {}

			record_data [section] [key] = value

class MiscUnsetArgument:

	def args_update (self, parser, helper):

		parser.add_argument (
			"--unset",
			action = "append",
			default = [],
			metavar = "GROUP.KEY",
			help = "miscellaneous value to unset")

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("unset") == None:
			return

		for section_key in arg_vars ["unset"]:

			section, key = section_key.split (".")

			if not section in record_data:
				continue

			if not key in record_data [section]:
				continue

			del record_data [section] [key]

			if not record_data [section]:
				del record_data [section]

class MiscSetJsonArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--set-json",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("GROUP.KEY", "VALUE"),
			help = "miscellaneous JSON value to store")

	def args_update (self, parser, helper):

		parser.add_argument (
			"--set-json",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("GROUP.KEY", "VALUE"),
			help = "miscellaneous JSON value to store")

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("set_json") == None:
			return

		if arg_vars.get ("set_json") == None:
			return

		for section_key, json_value in arg_vars ["set_json"]:

			section, key = (
				section_key.split ("."))

			if not section in record_data:
				record_data [section] = {}

			print (json_value)

			value = (
				json.loads (
					json_value))

			record_data [section] [key] = (
				value)

class MiscRemoveArgument:

	def args_update (self, parser, helper):

		parser.add_argument (
			"--remove",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("KEY", "VALUE"),
			help = "miscellaneous value to remove from list")

	def args_create (self, parser, helper):

		parser.add_argument (
			"--remove",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("KEY", "VALUE"),
			help = "miscellaneous value to remove from list")

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("remove") == None:
			return

		for section_key, value in arg_vars ["remove"]:

			section, key = section_key.split (".")

			if not section in record_data:
				continue

			if not key in record_data [section]:
				continue

			if not value in record_data [section] [key]:
				continue

			record_data [section] [key].remove (value)

class MiscAddArgument:

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

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("add") == None:
			return

		if arg_vars.get ("add") == None:
			return

		for section_key, value in arg_vars ["add"]:

			section, key = section_key.split (".")

			if not section in record_data:
				record_data [section] = {}

			if not key in record_data [section]:
				record_data [section] [key] = []

			if value in record_data [section] [key]:
				continue

			record_data [section] [key].append (value)

class MiscSetDictArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--set-dict",
			action = "append",
			nargs = 3,
			default = [],
			metavar = ("SECTION.KEY", "KEY", "VALUE"),
			help = "miscellaneous value to store in dictionary")

	def args_update (self, parser, helper):

		parser.add_argument (
			"--set-dict",
			action = "append",
			nargs = 3,
			default = [],
			metavar = ("SECTION.KEY", "KEY", "VALUE"),
			help = "miscellaneous value to store in dictionary")

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("set_dict") == None:
			return

		if arg_vars.get ("set_dict") == None:
			return

		for section_key, dict_key, value in arg_vars ["set_dict"]:

			section, key = section_key.split (".")

			if not section in record_data:
				record_data [section] = {}

			if not key in record_data [section]:
				record_data [section] [key] = OrderedDict ()

			record_data [section] [key] [dict_key] = value

class MiscUnsetDictArgument:

	def args_create (self, parser, helper):

		parser.add_argument (
			"--unset-dict",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("SECTION.KEY", "KEY"),
			help = "miscellaneous value to unset in dictionary")

	def args_update (self, parser, helper):

		parser.add_argument (
			"--unset-dict",
			action = "append",
			nargs = 2,
			default = [],
			metavar = ("SECTION.KEY", "KEY"),
			help = "miscellaneous value to unset in dictionary")

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("unset_dict") == None:
			return

		if arg_vars.get ("unset_dict") == None:
			return

		for section_key, dict_key in arg_vars ["unset_dict"]:

			section, key = section_key.split (".")

			if not section in record_data:
				return

			if not key in record_data [section]:
				return

			del (record_data [section] [key] [dict_key])

class GeneratePasswordArgument:

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

	def update_record (self, arg_vars, record_data, context, helper):

		if arg_vars.get ("generate_password") == None:
			return

		if arg_vars.get ("generate_password") == None:
			return

		for section_key in arg_vars ["generate_password"]:

			section, key = section_key.split (".")

			if not section in record_data:
				record_data [section] = {}

			record_data [section] [key] = generate_password ()

# ex: noet ts=4 filetype=python
