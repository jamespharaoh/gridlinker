schemas = dict ()

def define_schema (name, groups):

	schemas [name] = groups

def schema_group (items):

	return items

def schema_field (name, required = False, default = None):

	return dict ({
		"name": name,
		"required": required,
		"default": default,
	})

define_schema ("certificate-authority", [

	schema_group ([

		schema_field (
			name = "authority_state",
			required = True),

		schema_field (
			name = "authority_serial",
			required = True),

	]),

	schema_group ([

		schema_field (
			name = "subject_country",
			required = True),

		schema_field (
			name = "subject_locality",
			required = True),

		schema_field (
			name = "subject_organization",
			required = True),

		schema_field (
			name = "subject_common_name",
			required = True),

	]),

])

define_schema ("certificate-database", [

	schema_group ([

		schema_field (
			name = "database_state",
			required = True),

	]),

])
