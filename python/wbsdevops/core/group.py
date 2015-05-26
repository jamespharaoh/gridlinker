from __future__ import absolute_import

from wbsdevops.generic import *

group_command = GenericCommand (

	CommandHelper (

		name = "group",
		help = "manage group definitions",

		custom_args = [

			NameArgument (
				argument = "--name",
				key = "group_name"),

			SimpleArgument (
				argument = "--description",
				key = "group_description",
				value_name = "DESCRIPTION",
				help = "user-friendly description"),

			SetArgument (),
			GeneratePasswordArgument (),

		],

		custom_columns = [

			SimpleColumn (
				name = "group_name",
				label = "Name",
				default = True),

			SimpleColumn (
				name = "group_description",
				label = "Description",
				default = True),

		],

	)

)

def args (sub_parsers):

	group_command.args (sub_parsers)

# ex: noet ts=4 filetype=yaml
