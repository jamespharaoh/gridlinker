from __future__ import absolute_import

import os

import dnode.certificate
import dnode.client

cached_client = None

certificate_data = dict ({
	"country": "GB",
	"locality": "Leeds",
	"organization": "Rocketware Limited",
})

def get_client ():

	global cached_client

	if cached_client:
		return cached_client

	cached_client = dnode.client.DnodeClient ()

	return cached_client

cached_authorities = dict ()

def get_authority (name):

	global cached_authorities

	if name in cached_authorities:
		return cached_authorities [name]

	dnode_client = get_client ()

	cached_authorities [name] = dnode.certificate.Authority (
		dnode_client,
		"/authority/%s" % name,
		certificate_data)

	cached_authorities [name].load ()

	return cached_authorities [name]
