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
import json
import logging
import os
import socket
import ssl
import sys

from lxccmd.commands import get_commands
from lxccmd.certs import generate_cert, get_cert_path, \
    trust_cert_add, trust_cert_list, trust_cert_remove, trust_cert_verify
from lxccmd.config import get_run_path
from lxccmd.cli import render_table
from lxccmd.network import server_is_running

try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn
except ImportError:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from SocketServer import ThreadingMixIn

# Setup i18n
_ = gettext.gettext

# Global variables
exported_functions = {}


# Main functions
class ThreadingServer(ThreadingMixIn, HTTPServer):
    address_family = socket.AF_INET6


class RequestHandler(BaseHTTPRequestHandler):
    def handle_one_request(self):
        """
            Handle a single HTTP request.
            Mostly copy/paste from the original function.
        """

        # Validate the connection
        peer_cert = self.connection.getpeercert(binary_form=True)
        if not peer_cert:
            role = "guest"
        elif trust_cert_verify(ssl.DER_cert_to_PEM_cert(peer_cert), "server"):
            role = "trusted"
        else:
            role = "untrusted"

        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return

            # Actual processing happens here
            signature = (role, self.command, self.path)
            if signature not in self.server.exported_functions:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {'error': "No matching function"},
                        sort_keys=True, indent=4,
                        separators=(',', ': ')).encode())
                return

            self.send_response(200)
            self.send_header("Content-type:", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    self.server.exported_functions[signature](),
                    sort_keys=True, indent=4, separators=(',', ': ')).encode())

            self.wfile.flush()
        except socket.timeout as e:
            self.log_error("Request timed out: %r", e)
            self.close_connection = 1
            return


# CLI functions
def cli_subparser(sp):
    parser = sp.add_parser("server", help=_("Server control"))
    subparsers = parser.add_subparsers()

    ### Trick to have a consistent behavior for 2.x and 3.x
    if hasattr(subparsers, "required"):
        subparsers.required = True
        subparsers.dest = _("action")

    # Service control
    sp_start = subparsers.add_parser("status",
                                     help=_("Get status information"))
    sp_start.set_defaults(func=cli_status)

    sp_start = subparsers.add_parser("start", help=_("Start the server"))
    sp_start.add_argument("--foreground", "-f", action="store_true",
                          help=_("Start the server in the foreground."))
    sp_start.set_defaults(func=cli_start)

    sp_stop = subparsers.add_parser("stop", help=_("Stop the server"))
    sp_stop.set_defaults(func=cli_stop)

    # Trust control
    sp_trust = subparsers.add_parser(
        "trust", help=_("Allow trusted connections from a client"))
    sp_trust.add_argument("client_cert", metavar="CLIENT_CERT",
                          help=_("Certificate of the trusted client."))
    sp_trust.set_defaults(func=cli_trust)

    sp_forget = subparsers.add_parser(
        "forget", help=_("Cancel an existing trust relationship"))
    sp_forget.add_argument("clientid", metavar="CLIENT_ID",
                           help=_("ID (hash) of the trusted client."))
    sp_forget.set_defaults(func=cli_forget)

    # Configuration control
    sp_set = subparsers.add_parser(
        "set",
        help=_("Get/set a configuration property (empty string to unset)"))
    sp_set.add_argument("key", metavar="KEY", type=str, nargs=1,
                        help=_("Configuration key"))
    sp_set.add_argument("value", metavar="VALUE", type=str, nargs="?",
                        help=_("Configuration value"))
    sp_set.set_defaults(func=cli_set)


def cli_status(parser, args):
    render_table([[_("Running"), _("Trusted clients")],
                  [str(server_is_running()),
                   ", ".join(trust_cert_list("server"))]],
                 header=True, orientation="vertical")


def cli_start(parser, args):
    if server_is_running():
        parser.error(_("A server is already running!"))

    # Get or generate the server certificate
    generate_cert("server")
    server_crt, server_key, server_capath = get_cert_path("server")

    # Figure out what's to be exported
    commands = get_commands()
    exported_functions = {}
    for command_name, command_module in commands.items():
        if hasattr(command_module, "rest_functions"):
            exported_functions.update(command_module.rest_functions())

    httpd = ThreadingServer(('::', 8443), RequestHandler)
    httpd.exported_functions = exported_functions

    httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True,
                                   certfile=server_crt,
                                   keyfile=server_key,
                                   cert_reqs=ssl.CERT_OPTIONAL)
    httpd.socket._context.load_verify_locations(capath=server_capath)

    if not args.foreground:
        child = os.fork()

        if child:
            with open(os.path.join(get_run_path(), "server.pid"), "w+") as fd:
                fd.write(str(child))

            logging.info("Server started, pid: %s" % child)
            return

        sys.stdin.close()
        sys.stdout.close()
        sys.stderr.close()
        sys.stdin = open(os.devnull, "w")
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    httpd.serve_forever()


def cli_stop(parser, args):
    if not server_is_running():
        parser.error(_("The server isn't running at the moment!"))

    server_pid_path = os.path.join(get_run_path(), "server.pid")

    if not os.path.exists(server_pid_path):
        parser.error(_("No PID on record for running server!"))

    with open(server_pid_path, "r") as fd:
        server_pid = int(fd.read().strip())

    os.remove(server_pid_path)

    os.kill(server_pid, 9)


def cli_trust(parser, args):
    if not os.path.exists(args.client_cert):
        parser.error(_("The file doesn't exist."))

    with open(args.client_cert, "r") as fd:
        certificate = fd.read()

    if not trust_cert_add(certificate, "server"):
        parser.error(_("Failed to add the certificate to the trust store."))


def cli_forget(parser, args):
    if os.path.exists(args.clientid):
        with open(args.clientid, "r") as fd:
            certificate = fd.read()
    else:
        certificate = args.clientid

    if not trust_cert_remove(certificate, "server"):
        parser.error(
            _("Failed to remove the certificate from the trust store."))


def cli_set(parser, args):
    pass


# REST functions
def rest_functions():
    return {("guest", "GET", "/server/trust"): rest_trust}


def rest_trust():
    return {}
