# Datingnode Ansible


### setup

misc/create-resources jimmy
This creates the resource in etcd


Main website:

* https://bitbucket.org/jimmyff/datingnode-ansible

Developers:

* Jimmy Forrester-Fellows <jimmy@rocketware.co.uk>
* James Pharaoh <james@wellbehavedsoftware.com>

This project contains a self-contained automated system for setting up and
managing Datingnode's server infrastructure.

It is based on [gridlinker](https://github.com/wellbehavedsoftware/gridlinker),
which provides tools to manage data and a collection of general purpose
playbooks. It uses [etcd](https://github.com/coreos/etcd) to store runtime data,
and [ansible](https://github.com/ansible/ansible) to perform deployments.

This documentation is generated automatically, so please do not modify it
directly, or your changes will be overwritten.

## Requirements

This project depends on a recent version of python, currently 2.7.10. You can
download the [source code](https://www.python.org/downloads/) and compile this
yourself.

You will also need to download and install
[pip](https://pypi.python.org/pypi/pip), and a number of packages:

* `ipaddress`
* `jinja2`
* `netaddr`
* `paramiko`
* `pyopenssl`
* `pyyaml`

## Configuration

Most users will be provided with a copy of this software along with the relevant
configuration. If this is the case, you should be able to run commands directly,
and discover options via the built-in help.

```sh
cd datingnode-ansible
./datingnode-ansible --help
```

To set up a connection to an existing database, create `config/connections.yml`,
using the following template:

```yaml
---

datingnode-ansible:

  etcd_servers: [ "admin-1.vpn.datingnode.co.uk", "admin-2.vpn.datingnode.co.uk", "admin-3.vpn.datingnode.co.uk" ]
  etcd_secure: "yes"
  etcd_prefix: "/datingnode-ansible"

# ex: et ts=2 filetype=yaml
```

You also need to obtain a valid certificate, along with its private key, and the
ca certificate, from the administrator. These should be placed in the following
places:

* `config/datingnode-ansible-ca.cert`
* `config/datingnode-ansible.cert`
* `config/datingnode-ansible.key`

To use a local etcd server, for example during development or testing or when
you are working online, use the following configuration:

```yaml
---

datingnode-ansible:

  etcd_servers: [ "localhost" ]
  etcd_secure: "no"
  etcd_prefix: "/datingnode-ansible"

# ex: et ts=2 filetype=yaml
```

<p style="display:none">
<!-- ex: noet ts=4 filetype=markdown -->
</p>
