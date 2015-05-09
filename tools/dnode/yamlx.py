import sys
import yaml

def parse (string):

	return yaml.safe_load (string)

def encode (key_groups, data):

	yaml = "---\n\n"

	yaml += "%s\n" % encode_real (key_groups, data, "", True)

	return yaml

def encode_real (key_groups, data, indent, here):

	if isinstance (data, str):
		return encode_str (key_groups, data, indent, here)

	if isinstance (data, unicode):
		return encode_str (key_groups, data, indent, here)

	if isinstance (data, dict):
		return encode_dict (key_groups, data, indent, here)

	if isinstance (data, list):
		return encode_list (key_groups, data, indent, here)

	raise Exception ("Don't know how to handle %s" % type (data))

def encode_str (key_groups, data, indent, here):

	return "\"%s\"" % data

def encode_list (key_groups, data, indent, here):

	yaml = ""
	next_indent = indent + "  "

	for item in data:

		if not here:

			yaml += "\n"
			yaml += indent

		yaml += "- "
		yaml += encode_real (key_groups, item, next_indent, True)

		here = False

	return yaml

def encode_dict (schema, data, indent, here):

	yaml = ""
	next_indent = indent + "  "

	done_keys = {}

	for field_group in schema:

		new_group = True

		for field in field_group:

			if field ["name"] in data:
				value = data [field ["name"]]
			elif field ["default"] is not None:
				value = field ["default"]
			else:
				continue

			if not here:

				yaml += "\n"
				yaml += indent

				if new_group:

					yaml += "\n"
					yaml += indent

			yaml += field ["name"]
			yaml += ": "
			yaml += encode_real ([], value, next_indent, False)

			done_keys [field ["name"]] = True

			here = False
			new_group = False

	new_group = True

	for key in sorted (data.keys ()):

		if key in done_keys:
			continue;

		sys.stderr.write ("warning: unrecognised key: %s\n" % key)

		value = data [key]

		if not here:

			yaml += "\n"
			yaml += indent

			if new_group:

				yaml += "\n"
				yaml += indent

		yaml += key
		yaml += ": "
		yaml += encode_real ([], data [key], next_indent, False)

		here = False
		new_group = False

	return yaml