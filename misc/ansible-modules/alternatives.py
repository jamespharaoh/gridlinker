#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to manage symbolic link alternatives.
(c) 2014, Gabe Mulley <gabe.mulley@gmail.com>
(c) 2015, David Wittman <dwittman@gmail.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: alternatives
short_description: Manages alternative programs for common commands
description:
    - Manages symbolic links using the 'update-alternatives' tool
    - Useful when multiple programs are installed but provide similar functionality (e.g. different editors).
version_added: "1.6"
author:
    - '"David Wittman (@DavidWittman)" <dwittman@gmail.com>'
    - '"Gabe Mulley (@mulby)" <gabe.mulley@gmail.com>'
    - '"James Pharaoh" <james@pharaoh.uk>'
options:
  name:
    description:
      - The generic name of the link.
    required: true
  path:
    description:
      - The path to the real executable that the link should point to.
    required: true
  link:
    description:
      - The path to the symbolic link that should point to the real executable.
      - This option is required on RHEL-based distributions
    required: false
  force:
    description:
      - Replace or drop any real file that is installed where an alternative
        link has to be installed or removed.
    choices: [ "yes", "no" ]
    required: false
    default: "yes"
requirements: [ update-alternatives ]
'''

EXAMPLES = '''
- name: correct java version selected
  alternatives: name=java path=/usr/lib/jvm/java-7-openjdk-amd64/jre/bin/java

- name: alternatives link created
  alternatives: name=hadoop-conf link=/etc/hadoop/conf path=/etc/hadoop/conf.ansible
'''

DEFAULT_LINK_PRIORITY = 50

import re

def main():

    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            path = dict(required=True),
            link = dict(required=False),
            force = dict(default=False, type='bool'),
        ),
        supports_check_mode=True,
    )

    params = module.params
    name = params['name']
    path = params['path']
    link = params['link']
    force = params['force']

    UPDATE_ALTERNATIVES = module.get_bin_path('update-alternatives',True)

    current_path = None
    all_alternatives = []

    # Run `update-alternatives --display <name>` to find existing alternatives
    (rc, display_output, _) = module.run_command(
        [UPDATE_ALTERNATIVES, '--display', name]
    )

    if rc == 0:
        # Alternatives already exist for this link group
        # Parse the output to determine the current path of the symlink and
        # available alternatives
        current_path_regex = re.compile(r'^\s*link currently points to (.*)$',
                                        re.MULTILINE)
        alternative_regex = re.compile(r'^(\/.*)\s-\spriority', re.MULTILINE)

        current_path = current_path_regex.search(display_output).group(1)
        all_alternatives = alternative_regex.findall(display_output)

        if not link:
            # Read the current symlink target from `update-alternatives --query`
            # in case we need to install the new alternative before setting it.
            #
            # This is only compatible on Debian-based systems, as the other
            # alternatives don't have --query available
            rc, query_output, _ = module.run_command(
                [UPDATE_ALTERNATIVES, '--query', name]
            )
            if rc == 0:
                for line in query_output.splitlines():
                    if line.startswith('Link:'):
                        link = line.split()[1]
                        break

    if not force:
        need_to_force = False
    elif not os.path.islink(link):
        need_to_force = True
    elif os.readlink(link) != '/etc/alternatives/' + name:
        need_to_force = True
    else:
        need_to_force = False

    if current_path != path or need_to_force:
        if module.check_mode:
            module.exit_json(changed=True, current_path=current_path)
        try:
            # install the requested path if necessary
            if path not in all_alternatives:
                if not link:
                    module.fail_json(msg="Needed to install the alternative, but unable to do so as we are missing the link")

                if need_to_force:
                    module.run_command(
                        [UPDATE_ALTERNATIVES, '--force', '--install', link, name, path, str(DEFAULT_LINK_PRIORITY)],
                        check_rc=True
                    )

                else:
                    module.run_command(
                        [UPDATE_ALTERNATIVES, '--install', link, name, path, str(DEFAULT_LINK_PRIORITY)],
                        check_rc=True
                    )

            # select the requested path
            module.run_command(
                [UPDATE_ALTERNATIVES, '--set', name, path],
                check_rc=True
            )

            module.exit_json(changed=True)
        except subprocess.CalledProcessError, cpe:
            module.fail_json(msg=str(dir(cpe)))

    else:
        module.exit_json(changed=False)


# import module snippets
from ansible.module_utils.basic import *
main()