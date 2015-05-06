import etcd

import data
import yamlx

class DnodeClient:

	def __init__ (self,
		peers = None,
		ca_cert = None,
		client_cert = None,
		client_key = None,
	):

		if peers:

			self.etcd_client = etcd.Client (
				protocol = "https",
				host = peers,
				cert = (client_cert, client_key),
				ca_cert = ca_cert)

		else:

			self.etcd_client = etcd.client.Client (
				host = "localhost",
				port = 2379)

	def exists (self, key):

		try:
			self.etcd_client.get (key)
			return True

		except etcd.EtcdKeyNotFound:
			return False

	def get_raw (self, key):

		some_etcd = self.etcd_client.get (key)

		return some_etcd.value

	def set_raw (self, key, value):

		self.etcd_client.write (key, value)

	def rm_raw (self, key):

		self.etcd_client.delete (
			key = key)

	def rmdir_raw (self, key):

		self.etcd_client.delete (
			key = key,
			dir = True)

	def make_queue_dir (self, key):

		result = self.etcd_client.write (
			key = key,
			value = None,
			append = True,
			dir = True)

		return (
			str (result.key),
			str (result.createdIndex),
		)

	def get_yaml (self, key):

		some_yaml = self.get_raw (key)
		some_data = yamlx.parse (some_yaml)

		return some_data

	def set_yaml (self, schema_name, key, some_data):

		schema = data.schemas [schema_name]

		some_yaml = yamlx.encode (schema, some_data)

		self.set_raw (key, some_yaml)

	def get_host (self, host_name):

		key = "/host/%s" % host_name

		host_data = self.get_yaml (key)
		host_data ["host_name"] = host_name

		return host_data

	def set_host (self, host_name, host_data):

		key = "/host/%s" % host_name

		self.set_yaml (
			"host",
			key,
			host_data)

	def get_all_hosts (self):

		hosts_etcd = self.etcd_client.read ("host", recursive = True)

		ret = []

		for host_etcd in hosts_etcd.children:

			host_name = host_etcd.key.replace ("/host/", "")
			host_data = yamlx.parse (host_etcd.value)
			host_data ["host_name"] = host_name

			ret.append ((host_name, host_data))

		return ret

	def host_to_yaml (self, host_data):

		return yamlx.encode (data.schemas ["host"], host_data)
