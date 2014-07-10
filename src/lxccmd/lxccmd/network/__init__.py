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
import json
import socket

from lxccmd.certs import get_cert_path

try:
    from http.client import HTTPSConnection
except:
    from httplib import HTTPSConnection


def server_is_running():
    """
        Attempts to bind the server address to check if it's running.
    """

    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("::", 8443))
        sock.close()

        return False
    except socket.error:
        return True


def secure_remote_call(target, method, path, **args):
    """
        Call a function using the authenticated REST API.
    """

    client_crt, client_key, client_capath = get_cert_path("client")

    conn = HTTPSConnection(target, 8443,
                           key_file=client_key,
                           cert_file=client_crt)
    conn.request(method, path)
    response = conn.getresponse()
    conn.close()

    if response.status != 200:
        return False

    return json.loads(response.read().decode())
