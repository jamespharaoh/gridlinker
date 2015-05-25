from __future__ import absolute_import

def args (sub_parsers):

	args_env (sub_parsers)

def args_env (sub_parsers):

	parser = sub_parsers.add_parser (
		"env",
		help = "print out environment variables",
		description = """
			This command writes a list of environment variables which correspond
			to the local configuration. This is intended to be used with the
			"eval" built-in command in sh or bash in order to correctly invoke
			various commands.
		""")

	parser.set_defaults (
		func = do_env)

def do_env (context, args):

	for key in sorted (context.env.keys ()):
		print "export %s=\"%s\"" % (key, context.env [key])

# ex: noet ts=4 filetype=yaml
