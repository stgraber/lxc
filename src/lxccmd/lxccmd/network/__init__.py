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
import hashlib
import json
import os
import socket
import ssl

from lxccmd.certs import get_cert_path
from lxccmd.config import config_get, config_has_section, get_config_path
from lxccmd.exceptions import LXCError

try:
    from http.client import HTTPSConnection
except:
    from httplib import HTTPSConnection

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

# Setup i18n
_ = gettext.gettext


def remote_add_trusted(host, port, password, cert="client"):
    """
        Setup a trust relationship with a remote server using a password.
    """

    client_crt, client_key, client_capath = get_cert_path(cert)
    with open(client_crt, "r") as fd:
        cert = fd.read()

    return remote_call(host, port, "POST", "/server/trust", None,
                       data={'password': password,
                             'cert': cert})


def remote_get_certificate(host, port):
    """
        Connect to the target and retrieve the fingerprint.
    """

    try:
        certificate = ssl.get_server_certificate((host, port))

        return certificate, hashlib.sha256(
            ssl.PEM_cert_to_DER_cert(certificate)).hexdigest()
    except:
        return False, False


def remote_get_role(host, port):
    """
        Return the role (trusted or guest) as seen from the remote server.
    """

    try:
        ret = remote_call(host, port, "GET", "/server/whoami")
    except:
        try:
            ret = remote_call(host, port, "GET", "/server/whoami", None)
        except:
            raise LXCError(_("Unable to get current role."))

    return ret['role']


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


def secure_remote_call(remote, method, path, data=None):
    """
        Call a remote function using the authenticated REST API.
    """

    if not config_has_section("remote/%s" % remote):
        raise LXCError(_("Invalid remote server: %s" % remote))

    remote_url = config_get("remote/%s" % remote, "url")
    parsed_url = urlparse(remote_url)
    remote_fingerprint = config_get("remote/%s" % remote, "fingerprint")

    host = parsed_url.hostname
    port = parsed_url.port
    if not port:
        port = 8443

    return remote_call(host, port, method, path,
                       fingerprint=remote_fingerprint,
                       data=data)


def remote_call(host, port, method, path, cert="client",
                fingerprint=None, data=None):
    """
        Call a function using the REST API.
    """

    client_crt = None
    client_key = None
    client_capath = None

    if cert:
        client_crt, client_key, client_capath = get_cert_path(cert)

    try:
        context = ssl._create_stdlib_context()

        if fingerprint:
            cert_path = os.path.join(get_config_path(), "certs")
            ca_file = os.path.join(cert_path, "client-ca",
                                   "%s.crt" % fingerprint)

            if not os.path.exists(ca_file):
                raise LXCError(_("Invalid certificate fingerprint."))

            context.load_verify_locations(cafile=ca_file)

        conn = HTTPSConnection(host, port,
                               key_file=client_key,
                               cert_file=client_crt,
                               context=context)
        if data:
            params = json.dumps(data)
            headers = {'Content-Type': "application/json"}
            conn.request(method, path, params, headers)
        else:
            conn.request(method, path)
        response = conn.getresponse()
        conn.close()
    except:
        raise LXCError(_("Remote function isn't available."))

    if response.status == 404:
        raise LXCError(_("Remote function isn't available."))

    value = response.read().decode()
    return json.loads(value)
