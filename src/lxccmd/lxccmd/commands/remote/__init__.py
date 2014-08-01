# -*- coding: utf-8 -*-
#
# lxc: New LXC command line client
#
# Authors:
# Stephane Graber <stgraber@ubuntu.com> (Canonical Ltd. 2014)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# Import everything we need
import gettext

from lxccmd.certs import trust_cert_add
from lxccmd.config import config_has_section, config_list_sections, \
    config_remove_section, config_get, config_set
from lxccmd.exceptions import LXCError
from lxccmd.network import remote_get_certificate, remote_get_role, \
    remote_add_trusted

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

# Setup i18n
_ = gettext.gettext


# CLI functions
def cli_subparser(sp):
    parser = sp.add_parser("remote", help=_("Remote servers"))
    subparsers = parser.add_subparsers()

    ### Trick to have a consistent behavior for 2.x and 3.x
    if hasattr(subparsers, "required"):
        subparsers.required = True
        subparsers.dest = _("action")

    # Service control
    sp_add = subparsers.add_parser("add", help=_("Add a remote server"))
    sp_add.add_argument("name", metavar="NAME",
                        help=_("Local name for the remote server"))
    sp_add.add_argument("url", metavar="URL",
                        help=_("URL of the remote server"))
    sp_add.add_argument("--skip-fingerprint", action="store_true",
                        help=_("Don't ask for fingerprint confirmation"))
    sp_add.add_argument("--password", type=str, default=None,
                        help=_("Password to use to setup the trust"))
    sp_add.set_defaults(func=cli_add_remote)

    sp_list = subparsers.add_parser("list", help=_("List remote servers"))
    sp_list.set_defaults(func=cli_list_remote)

    sp_remove = subparsers.add_parser("remove",
                                      help=_("Remove a remote server"))
    sp_remove.add_argument("name", metavar="NAME",
                           help=_("Local name of the remote server"))
    sp_remove.set_defaults(func=cli_remove_remote)


def cli_add_remote(args):
    if config_has_section("remote/%s" % args.name):
        raise LXCError(_("Remote '%s' already exists." % args.name))

    parsed = urlparse(args.url)

    if parsed.scheme not in ("https"):
        raise LXCError(_("Invalid URL scheme '%s'.") % parsed.scheme)

    host = parsed.hostname
    port = parsed.port
    if not port:
        port = 8443

    certificate, fingerprint = remote_get_certificate(host, port)

    if not fingerprint:
        raise LXCError(_("Unable to reach remote server."))

    if not args.skip_fingerprint:
        print(_("Remote server certificate fingerprint is: %s" % fingerprint))
        if input(_("Is this correct? (yes/no): ")) != _("yes"):
            return

    role = remote_get_role(host, port)
    if role == "guest":
        if args.password:
            password = args.password
        else:
            if not args.skip_fingerprint:
                print("")
            password = input(_("Remote password: "))

        res = remote_add_trusted(host, port, password)
        if "success" not in res:
            raise LXCError(_("Invalid password."))

    config_set("remote/%s" % args.name, "url", args.url)
    config_set("remote/%s" % args.name, "fingerprint", fingerprint)
    config_set("remote/%s" % args.name, "type", "lxc-rest")

    trust_cert_add(certificate, "client")


def cli_list_remote(args):
    for entry in config_list_sections():
        if not entry.startswith("remote/"):
            continue

        remote_name = entry.split("remote/", 1)[-1]
        remote_url = config_get(entry, "url")
        remote_fingerprint = config_get(entry, "fingerprint")

        print(" - %s (%s, %s)" % (remote_name, remote_url, remote_fingerprint))


def cli_remove_remote(args):
    if not config_has_section("remote/%s" % args.name):
        raise LXCError(_("Remote '%s' doesn't exist." % args.name))

    config_remove_section("remote/%s" % args.name)


# REST functions
def rest_list_remote():
    return {}


def rest_functions():
    return {("trusted", "GET", "/remote"): rest_list_remote}
