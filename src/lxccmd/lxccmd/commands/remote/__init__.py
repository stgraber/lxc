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

    sp_list = subparsers.add_parser("list", help=_("List remote servers"))

    sp_remove = subparsers.add_parser("remove",
                                      help=_("Remove a remote server"))

    assert(sp_add)
    assert(sp_list)
    assert(sp_remove)


# REST functions
def rest_get_remotes():
    return {}


def rest_functions():
    return {("trusted", "GET", "/remote"): rest_get_remotes}
