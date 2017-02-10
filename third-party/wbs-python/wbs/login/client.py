from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:

	import datetime
	import flask
	import httplib2
	import json

except ImportError:

	pass

class LoginClient (object):

	def __init__ (self, settings):

		self.token_cache = dict ()

		self.settings = settings

		self.http = (
			httplib2.Http ())

	def before_request (self):

		if "force_email" in self.settings:

			flask.g.user_email = (
				self.settings ["force_email"])

			flask.g.user_groups = (
				self.settings ["force_groups"])

			return

		if not self.settings ["cookie"] in flask.request.cookies:

			flask.g.user_email = None
			flask.g.user_groups = []

			return

		token = (
			flask.request.cookies [
				self.settings ["cookie"]])

		if token in self.token_cache:

			token_data = (
				self.token_cache [token])

			if token_data ["expires"] < datetime.datetime.now ():

				del (self.token_cache [token])

				token_data = None

		else:

			token_data = None

		if not token_data:

			response, content = (
				self.http.request (
					"%s/api/verify" % (
						self.settings ["login-url"]),
					"POST",
					body = json.dumps ({
						"token": token,
					}),
					headers = {
						"Content-Type": "application/json",
					}))

			token_data = (
				json.loads (
					content))

			token_data ["expires"] = (
				datetime.datetime.now ()
				+ datetime.timedelta (seconds = 10 * 60))

			self.token_cache [token] = (
				token_data)

		if token_data ["success"]:

			flask.g.user_email = (
				token_data ["email-address"])

			flask.g.user_groups = (
				token_data ["groups"])

		else:

			flask.g.user_email = None
			flask.g.user_groups = []

# ex: noet ts=4 filetype=python