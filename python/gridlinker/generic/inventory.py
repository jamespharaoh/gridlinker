from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import json
import sys

def main (context, args):

	inventory = Inventory (context)

	if args == []:

		raise Exception ()

	elif args [0] == "--list":

		inventory.do_list ()

	elif args [0] == "--host":

		inventory.do_host (args [1])

	else:

		raise Exception ()

class Inventory (object):

	def __init__ (self, context):

		self.context = context

		self.world = {}

		self.classes = {}
		self.groups = {}
		self.resources = {}

		self.children = collections.defaultdict (list)
		self.members = collections.defaultdict (list)

		self.virtual_groups = set ()

	def load_classes (self):

		class_list = self.context.local_data ["classes"].items ()

		for class_name, class_data in class_list:

			# check basics

			if not "identity" in class_data:

				raise Exception ()

			if class_data ["identity"] ["type"] != "class":

				raise Exception (
					"Class does not contain correct type: %s" % class_name)

			if class_name != class_data ["identity"] ["name"]:

				raise Exception (
					"Class does not contain correct name: %s" % class_name)

			# check for duplicates

			if class_name in self.world:

				raise Exception (
					"Class is duplicated: %s" % class_name)

			# create class

			self.world [class_name] = class_data
			self.classes [class_name] = class_data

			if "virtual_groups" in class_data ["class"]:

				for virtual_group_name \
				in class_data ["class"] ["virtual_groups"]:

					if not virtual_group_name in self.virtual_groups:

						if virtual_group_name in self.world:
							raise Exception ()

						self.world [virtual_group_name] = {}
						self.virtual_groups.add (virtual_group_name)

					self.children [virtual_group_name].append (class_name)

	def load_groups (self):

		group_list = self.context.groups.get_all_list_quick ()

		for group_name, group_data in group_list:

			# check basics

			if not "identity" in group_data:

				raise Exception (
					"Group does not have identity: %s" % group_name)

			if not "type" in group_data ["identity"]:

				raise Exception ()

			if group_data ["identity"] ["type"] != "group":

				raise Exception ()

			if group_name != group_data ["identity"] ["name"]:

				raise Exception (
					"Group does not contain correct name: %s" % class_group)

			# check for duplicates

			if group_name in self.world:

				raise Exception (
					"Group is duplicated: %s" % group_name)

			# create group

			class_name = group_data ["identity"] ["class"]

			self.world [group_name] = group_data
			self.groups [group_name] = group_data

			self.children [class_name].append (group_name)

	def load_resources (self):

		for resource_name, resource_data \
		in self.context.resources.get_all_list_quick ():

			# check basics

			if not "identity" in resource_data:
				raise Exception ()

			if resource_data ["identity"] ["type"] != "resource":
				raise Exception ()

			# work out class

			if "class" in resource_data ["identity"]:

				class_name = resource_data ["identity"] ["class"]

			elif "group" in resource_data ["identity"]:

				group_name = resource_data ["identity"] ["group"]

				group_data = self.context.groups.get_quick (group_name)

				class_name = group_data ["identity"] ["class"]

			else:

				raise Exception ()

			class_data = self.classes [class_name]

			# work out unique name

			if class_data ["class"] ["scope"] == "global":

				unique_name = resource_data ["identity"] ["name"]

			elif class_data ["class"] ["scope"] == "class":

				unique_name = "%s/%s" % (
					class_name,
					resource_data ["identity"] ["name"])

			elif class_data ["class"] ["scope"] == "group":

				unique_name = "%s/%s" % (
					group_name,
					resource_data ["identity"] ["name"])

			else:

				raise Exception ()

			if resource_name != unique_name:

				raise Exception (
					"Resource does not contain correct name: %s" % resource_name)

			# check for duplicates

			if resource_name in self.world:

				raise Exception (
					"Resource is duplicated: %s" % resource_name)

			# create resource

			self.world [resource_name] = resource_data
			self.resources [resource_name] = resource_data

			if "group" in resource_data ["identity"]:

				group_name = resource_data ["identity"] ["group"]

				self.members [group_name].append (resource_name)

			elif "class" in resource_data ["identity"]:

				class_name = resource_data ["identity"] ["class"]

				self.members [class_name].append (resource_name)

			else:

				print resource_data

				raise Exception ()

	def add_group_class_type (self,
			item_friendly_name,
			item_short_name,
			item_data):

		item_name = item_data [item_short_name + "_name"]

		if item_short_name + "_group" in item_data:

			# add to group

			item_group = item_data [item_short_name + "_group"]

			if not item_group in all_groups:

				raise Exception (
					"%s %s has invalid group: %s" % (
						item_friendly_name,
						item_name,
						item_group))

			group_data = all_groups [item_group]

			all_groups [item_group] ["hosts"].append (item_name)

			# add to class

			group_class = group_data ["vars"] ["group_class"]

			if not group_class in all_groups:

				raise Exception ()

			class_data = all_groups [group_class]

			all_groups [group_class] ["hosts"].append (item_name)

			# add to type

			group_type = class_data ["vars"] ["class_type"]

			if not group_type in all_groups:

				raise Exception ()

			type_data = all_groups [group_type]

			all_groups [group_type] ["hosts"].append (item_name)

		elif item_short_name + "_class" in item_data:

			item_class = item_data [item_short_name + "_class"]
			class_data = all_groups [item_class]
			all_groups [item_class] ["hosts"].append (item_name)

			group_type = class_data ["vars"] ["class_type"]
			type_data = all_groups [group_type]
			all_groups [group_type] ["hosts"].append (item_name)

	def resolve_group (self, group_name, group_data):

		group_vars = group_data.get ("global", {})

		for prefix, data in group_data.items ():

			if prefix == "identity":
				continue

			group_vars [prefix] = data

			for name, value in data.items ():
				group_vars [prefix + "_" + name] = value

		return group_vars

	def resolve_class (self, class_name, class_data):

		class_vars = class_data.get ("global", {})

		for prefix, data in class_data.items ():

			if prefix == "identity":
				continue

			class_vars [prefix] = data

			for name, value in data.items ():
				class_vars [prefix + "_" + name] = value

		return class_vars

	def resolve_resource (self, resource_name, resource_data):

		resource_vars = collections.OrderedDict ()

		for prefix, data in resource_data.items ():

			resource_vars [prefix] = data

			for name, value in data.items ():
				resource_vars [prefix + "_" + name] = value

		if "parent" in resource_data ["identity"]:

			resource_vars ["parent"] = "{{ hostvars ['%s'] }}" % (
				resource_data ["identity"] ["parent"])

		elif "group" in resource_data ["identity"]:

			group_data = self.groups [resource_data ["identity"] ["group"]]

			if "parent" in group_data ["identity"]:

				resource_vars ["parent"] = "{{ hostvars ['%s'] }}" % (
					group_data ["identity"] ["parent"])

		return resource_vars

	def load_world (self):

		world = {}

		self.all = {
			"HOME": self.context.home,
			"WORK": "%s/work" % self.context.home,
			"GRIDLINKER_HOME": self.context.gridlinker_home,
		}

		if "globals" in self.context.local_data:

			for prefix, data in self.context.local_data ["globals"].items ():
			
				self.all [prefix] = data

				for name, value in data.items ():
					self.all [prefix + "_" + name] = value

		self.load_classes ()
		self.load_groups ()
		self.load_resources ()

	def do_list (self):

		output = {
			"_meta": {
				"hostvars": {},
			},
		}

		self.load_world ()

		output ["all"] = {
			"vars": self.all,
		}

		for class_name, class_data in self.classes.items ():

			output [class_name] = {
				"children": self.children [class_name],
				"hosts": self.members [class_name],
				"vars": self.resolve_class (class_name, class_data),
			}

		for group_name, group_data in self.groups.items ():

			output [group_name] = group_data

		for resource_name, resource_data in self.resources.items ():

			output ["_meta"] ["hostvars"] [resource_name] = \
				self.resolve_resource (resource_name, resource_data)

		if "data" in self.context.project_metadata:

			for key, value in self.context.project_metadata ["data"].items ():
				output ["all"] ["vars"] [key] = self.context.local_data [value]

		for virtual_group_name in self.virtual_groups:

			output [virtual_group_name] = {
				"children": self.children [virtual_group_name],
			}

		print_json (output)

	def do_host (self, host_name):

		print_json (self.local_data ["hosts"] [host_name])

def print_json (data):

	print json.dumps (
		data,
		sort_keys = True,
		indent = 4,
		separators = (", ", ": "))

# ex: noet ts=4 filetype=yaml
