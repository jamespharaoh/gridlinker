# Based on local.py (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Maykel Moya <mmoya@speedyrails.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import distutils.spawn
import traceback
import os
import subprocess
from ansible import errors
from ansible.callbacks import vvv
import ansible.constants as C

class Connection (object):

	def __init__ (self, runner, host, port, * args, ** kwargs):

		self.chroot = host
		self.has_pipelining = False
		self.become_methods_supported = C.BECOME_METHODS

		self.sudo_cmd = distutils.spawn.find_executable ("sudo")

		if not self.sudo_cmd:
			raise errors.AnsibleError ("sudo command not found in PATH")

		self.chroot_cmd = distutils.spawn.find_executable ("chroot")

		if not self.chroot_cmd and os.path.isfile ("/usr/sbin/chroot"):
			self.chroot_cmd = "/usr/sbin/chroot"

		if not self.chroot_cmd:
			raise errors.AnsibleError ("chroot command not found in PATH")

		self.runner = runner
		self.host = host

	def connect (self, port = None):

		vvv ("THIS IS A LOCAL CHROOT DIR", host = self.chroot)

		return self

	def exec_command (self, cmd, tmp_path, become_user = None, sudoable = False, executable = "/bin/sh", in_data = None):

		if sudoable \
		and self.runner.become \
		and self.runner.become_method not in self.become_methods_supported:

			raise errors.AnsibleError (
				"Internal Error: this module does not support running commands via %s" % (
					self.runner.become_method))

		if in_data:

			raise errors.AnsibleError (" ".join ([
				"Internal Error: this module does not support optimized module",
				"pipelining",
			]))

		# We enter chroot as root so we ignore privlege escalation?

		if executable:

			local_cmd = [
				self.sudo_cmd,
				self.chroot_cmd,
				self.chroot,
				executable,
				"-c",
				cmd]

		else:

			local_cmd = "%s %s \"%s\" %s" % (
				self.sudo_cmd,
				self.chroot_cmd,
				self.chroot, cmd)

		vvv ("EXEC %s" % (local_cmd), host = self.chroot)

		p = subprocess.Popen (
			local_cmd,
			shell = isinstance (local_cmd, basestring),
			 cwd = self.runner.basedir,
			 stdin = subprocess.PIPE,
			 stdout = subprocess.PIPE,
			 stderr = subprocess.PIPE)

		stdout, stderr = p.communicate ()

		return (p.returncode, "", stdout, stderr)

	def put_file (self, in_path, out_path):

		if not out_path.startswith (os.path.sep):
			out_path = os.path.join (os.path.sep, out_path)

		normpath = os.path.normpath (out_path)

		out_path = os.path.join (self.chroot, normpath [1:])

		vvv ("PUT %s TO %s" % (in_path, out_path), host = self.chroot)

		if not os.path.exists (in_path):

			raise errors.AnsibleFileNotFound (
				"file or module does not exist: %s" % in_path)

		try:

			subprocess.check_call ([
				self.sudo_cmd,
				"cp",
				in_path,
				out_path,
			])

		except Exception:

			traceback.print_exc ()

			raise errors.AnsibleError (
				"failed to copy %s to %s" % (in_path, out_path))

	def fetch_file (self, in_path, out_path):

		if not in_path.startswith (os.path.sep):
			in_path = os.path.join (os.path.sep, in_path)

		normpath = os.path.normpath (in_path)

		in_path = os.path.join (self.chroot, normpath [1:])

		vvv ("FETCH %s TO %s" % (in_path, out_path), host = self.chroot)

		raise Exception ("TODO")

	def close (self):

		pass
