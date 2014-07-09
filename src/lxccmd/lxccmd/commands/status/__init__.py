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
import logging
import os
import socket

from lxccmd.certs import get_fingerprint
from lxccmd.cli import render_table
from lxccmd.network import server_is_running, secure_remote_call

# Setup i18n
_ = gettext.gettext


# Main functions
def get_status():
    status = {}

    # Kernel version
    if os.path.exists("/proc/sys/kernel/osrelease"):
        with open("/proc/sys/kernel/osrelease", "r") as fd:
            kernel_version = fd.read().strip()
            kernel_version_raw = kernel_version
    else:
        logging.info("Unable to get kernel version, "
                     "/proc/sys/kernel/osrelease is missing.")
        kernel_version = _("Unknown")
        kernel_version_raw = None
    status['kernel_version'] = {'description': _("Kernel version"),
                                'value': kernel_version,
                                'value_raw': kernel_version_raw}

    # LXC version
    try:
        import lxc
        lxc_version = lxc.version
        lxc_version_raw = lxc.version
    except ImportError:
        lxc_version = _("Unknown")
        lxc_version_raw = None
    status['lxc_version'] = {'description': _("LXC version"),
                             'value': lxc_version,
                             'value_raw': lxc_version_raw}

    # Running mode
    # Bitmask:
    # - 1 => running inside a container
    # - 2 => running under userns
    # - 4 => running as a user

    running_mode = 0

    ## Detect running inside a container or on host
    if os.path.exists("/run/container_type"):
        running_mode += 1
    else:
        try:
            with open("/proc/1/environ", "r") as fd:
                for entry in fd.read().split("\x00"):
                    if entry.startswith("container="):
                        running_mode += 1
                        break
        except:
            pass

    ## Detect running inside a userns
    if os.path.exists("/proc/self/uid_map"):
        with open("/proc/self/uid_map", "r") as fd:
            if fd.read().strip() != "0          0 4294967295":
                running_mode += 2

    ## Detect running as a user or root
    if os.geteuid() > 0:
        running_mode += 4

    running_mode_descriptions = \
        {0: _("Running as root on the host"),
         1: _("Running as root inside a container"),
         2: _("Running as root on the host inside a user namespace"),
         3: _("Running as root inside an unprivileged container"),
         4: _("Running as user on the host"),
         5: _("Running as a user inside a container"),
         6: _("Running as a user on the host inside a user namespace"),
         7: _("Running as a user inside an unprivileged container")}

    status['running_mode'] = {'description': _("Running mode"),
                              'value': running_mode_descriptions[running_mode],
                              'value_raw': running_mode}

    # Server is running
    if server_is_running():
        server_state = _("Running")
        server_state_raw = True
    else:
        server_state = _("Stopped")
        server_state_raw = False

    status['server'] = {'description': _("Server state"),
                        'value': server_state,
                        'value_raw': server_state_raw}

    client_id_raw = get_fingerprint("client")
    status['hash_client'] = {'description': _("Client ID"),
                             'value': client_id_raw if client_id_raw
                             else _("Not generated"),
                             'value_raw': client_id_raw}

    server_id_raw = get_fingerprint("server")
    status['hash_server'] = {'description': _("Server ID"),
                             'value': server_id_raw if server_id_raw
                             else _("Not generated"),
                             'value_raw': server_id_raw}

    status['hostname'] = {'description': _("Hostname"),
                          'value': socket.gethostname(),
                          'value_raw': socket.gethostname()}

    return status


# CLI functions
def cli_subparser(sp):
    parser = sp.add_parser("status", help=_("System status"))
    parser.set_defaults(func=cli_status)


def cli_status(args):
    keys = []
    values = []

    if not args.remote:
        status = get_status()
    else:
        status = secure_remote_call(args.remote, "GET", "/status")

    for entry, entry_dict in sorted(status.items()):
        keys.append(entry_dict['description'])
        values.append(entry_dict['value'])

    render_table([keys, values], header=True, orientation="vertical")


# REST functions
def rest_functions():
    return {("trusted", "GET", "/status"): get_status}
