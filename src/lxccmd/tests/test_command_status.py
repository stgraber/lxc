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

import argparse
import socket
import unittest
import sys

from io import StringIO

from lxccmd.commands import status

try:
    from unittest import mock
except ImportError:
    import mock

if sys.version_info.major == 2:
    builtin_open = "__builtin__.open"
else:
    builtin_open = "builtins.open"


def fake_open(path, mode='r', buffering=-1, encoding=None,
              errors=None, newline=None, closefd=True, opener=None):
    if path == "/proc/1/environ":
        return StringIO(b"container=lxc\0".decode())

    if path == "/proc/sys/kernel/osrelease":
        return StringIO(b"1.2.3.4\n".decode())

    if path == "/run/container_type":
        return False

    if path == "/proc/self/uid_map":
        return StringIO(b"         0    1000000    1000000\n".decode())

    if path.endswith("certs/client.crt") or path.endswith("certs/server.crt"):
        return StringIO(b"""-----BEGIN CERTIFICATE-----
MIIFFTCCAv2gAwIBAgIJAMUQzS2WBWZXMA0GCSqGSIb3DQEBCwUAMCExHzAdBgNV
BAMMFkxYQyBzZXJ2ZXIgY2VydGlmaWNhdGUwHhcNMTQwNzA0MjIwNTM0WhcNMjQw
NzAxMjIwNTM0WjAhMR8wHQYDVQQDDBZMWEMgc2VydmVyIGNlcnRpZmljYXRlMIIC
IjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA2nop5cnNpu1e6aWzTLYQrjKT
r1XjUCUrEE3eLA7ldAnNpN4fRg4GkHAsiUOHT+JqFTsmeAgccRPwTpRbbq+Y3rpJ
sq8wrdGIzKlzQ2C9mjMeTXS//c8RCTn5G3TGBTfKMzzKtGjIRWoRf9L1vWHqaEDq
b3XyP+BFa8nWtqG48xixhtDP2OmQjCC3G8uviHjPq9aSNrumC+fT1VnrVLh5Xwux
Ov3akADYoRu9YiLNh2uQZLLgJeK18HsVIL/18q9ckfTg9CHGkvX9F/sJFcrGV8Tb
CR+2Zp4JLFBUoygLG+eGL5TtV1tagEhama60awvcIE8jt0WgfInRw20xjCzcV/y+
GqhOztLLLaArVuhPbx0HC1EzALMy45t/cTRyrSqTJhCrL8Ud/XE845knGMFZ1I+u
7d8FfkKovt2oCcltJ/y+Zv/yrpHh8SYNfd01PsUrIKsCQiq56moF1AxtFYKMUt/L
PUxWyrJNL2euyUxPLg6YEFuGqj+GG2pTBenQdmG3/+7fCD+QcB9Lbk7pVDcgWU+Y
2/wY/yJdQLf6cndRRUSKTlZ+IGk92kvRz2Lsivf/ig3FaPAUjlRjHOGx0wGp6B2+
9jMx4sylGZfoOvUh+E0fUgF+mAD9rv58gjQidqti5dCbchtoYfp3j81De8BqcUQ6
vpU8Ok1n3BT71u9EMkECAwEAAaNQME4wHQYDVR0OBBYEFATXqCMM51y4c2DrkVuK
jefcUCNGMB8GA1UdIwQYMBaAFATXqCMM51y4c2DrkVuKjefcUCNGMAwGA1UdEwQF
MAMBAf8wDQYJKoZIhvcNAQELBQADggIBAHnO+aYuaS/WfyDUHd93KBzOTCxFngZu
ePXPvxdAOtXdtjPWuaFx/oQbwIiwuNvwY1cJ15bCHeP6GYZ1pey4j/Nb4miH57Lj
wGIl0k89Cf0BfrUT7nAWhEIhVBhYXdwj1tuZ2OxNOHZgRByugCL0JH/ziRlXDNvG
jIBbtJXyoV34u9kivo5a4iblLc7S7+szBtIkz1WkJzAi3SqZ2e4h+Sk+EDSytJda
7QC7UBQK9BtJvPr0esoEAcN3jlr0wgzpkhDi1ezRh2CW4knqH52ND7nxGfKDknRW
c7iaGNwDOvvoRmHyxfNIWUtJrDaxVB+GPH4UQGoREjXX4jj1F6QyLQf4ItCs5Hpf
Mo7b/vb6IQmfKeoMXCAMpQlCsGGTxqPp7A+aQ15EoSTXRcPcCoziEHACXhjBiufl
qLzMPGg1/ho7FVmoSTsZeFzx6v9zamss+1oTJ1eVUD+FkG/SM+BmeG/q1SnJsJ+R
RZexbJEK6OaKKzHj/BsryjtXlWGe29O+ocno9uQ+6UZ+aKcIS3EFU1LEw19bkAom
k0xpjME+rrf45YvMd64orxfOixDxd2Jb9czL3V0D9WoFHx4c+x/s86OqmIVpU+0P
tIp/a9tvLl1U8Bag4/7voCRCmG6ZsecArl9sPitqP4UsZG1yAokYY72atZ0/kQoX
nSkHBBMese8H
-----END CERTIFICATE-----""".decode())

    if path.endswith(".mo"):
        raise IOError()

    return StringIO(b"Invalid\n".decode())


class StatusTests(unittest.TestCase):
    @mock.patch(builtin_open)
    def test_get_status_kernel_good(self, mock_open):
        mock_open.side_effect = fake_open

        current_status = status.get_status()
        self.assertIn("kernel_version", current_status)
        self.assertEquals(current_status['kernel_version']['value_raw'],
                          "1.2.3.4")
        self.assertEquals(current_status['kernel_version']['value'],
                          "1.2.3.4")

    @mock.patch("os.path.exists")
    def test_get_status_kernel_bad(self, mock_exists):
        def fake_exists(path):
            if path == "/proc/sys/kernel/osrelease":
                return False
            return True
        mock_exists.side_effect = fake_exists

        current_status = status.get_status()
        self.assertIn("kernel_version", current_status)
        self.assertIsNone(current_status['kernel_version']['value_raw'])
        self.assertEquals(current_status['kernel_version']['value'],
                          "Unknown")

    def test_get_status_lxc_good(self):
        class FakeLXC:
            @property
            def version(self):
                return "1.2.3.4"

        sys.modules['lxc'] = FakeLXC()

        current_status = status.get_status()
        self.assertIn("lxc_version", current_status)
        self.assertEquals(current_status['lxc_version']['value_raw'],
                          "1.2.3.4")
        self.assertEquals(current_status['lxc_version']['value'],
                          "1.2.3.4")

    def test_get_status_lxc_bad(self):
        class FakeLXC:
            @property
            def version(self):
                raise ImportError("Module doesn't exist.")

        sys.modules['lxc'] = FakeLXC()

        current_status = status.get_status()
        self.assertIn("lxc_version", current_status)
        self.assertIsNone(current_status['lxc_version']['value_raw'])
        self.assertEquals(current_status['lxc_version']['value'],
                          "Unknown")

    @mock.patch("os.path.exists")
    def test_get_status_mode_host(self, mock_exists):
        def fake_exists(path):
            if path == "/run/container_type":
                return False
            return True
        mock_exists.side_effect = fake_exists

        current_status = status.get_status()
        self.assertIn("running_mode", current_status)
        self.assertFalse(current_status['running_mode']['value_raw'] & 1 == 1)

    @mock.patch("os.path.exists")
    def test_get_status_mode_container(self, mock_exists):
        def fake_exists(path):
            if path == "/run/container_type":
                return True
            return False
        mock_exists.side_effect = fake_exists

        current_status = status.get_status()
        self.assertIn("running_mode", current_status)
        self.assertTrue(current_status['running_mode']['value_raw'] & 1 == 1)

    @mock.patch(builtin_open)
    @mock.patch("os.path.exists")
    def test_get_status_mode_container_fallback(self, mock_exists, mock_open):
        def fake_exists(path):
            return True
        mock_exists.side_effect = fake_exists

        mock_open.side_effect = fake_open

        current_status = status.get_status()
        self.assertIn("running_mode", current_status)
        self.assertTrue(current_status['running_mode']['value_raw'] & 1 == 1)

    @mock.patch("os.path.exists")
    def test_get_status_mode_priv(self, mock_exists):
        def fake_exists(path):
            if path == "/proc/self/uid_map":
                return False
            return True
        mock_exists.side_effect = fake_exists

        current_status = status.get_status()
        self.assertIn("running_mode", current_status)
        self.assertFalse(current_status['running_mode']['value_raw'] & 2 == 2)

    @mock.patch(builtin_open)
    @mock.patch("os.path.exists")
    def test_get_status_mode_unpriv(self, mock_exists, mock_open):
        def fake_exists(path):
            if path == "/proc/self/uid_map":
                return True
            return False
        mock_exists.side_effect = fake_exists

        mock_open.side_effect = fake_open

        current_status = status.get_status()
        self.assertIn("running_mode", current_status)
        self.assertTrue(current_status['running_mode']['value_raw'] & 2 == 2)

    @mock.patch("os.geteuid")
    def test_get_status_mode_root(self, mock_geteuid):
        def fake_geteuid():
            return 0
        mock_geteuid.side_effect = fake_geteuid

        current_status = status.get_status()
        self.assertIn("running_mode", current_status)
        self.assertFalse(current_status['running_mode']['value_raw'] & 4 == 4)

    @mock.patch("os.geteuid")
    def test_get_status_mode_user(self, mock_geteuid):
        def fake_geteuid():
            return 1000
        mock_geteuid.side_effect = fake_geteuid

        current_status = status.get_status()
        self.assertIn("running_mode", current_status)
        self.assertTrue(current_status['running_mode']['value_raw'] & 4 == 4)

    @mock.patch("socket.socket.bind")
    @mock.patch("socket.socket.close")
    def test_get_status_server_stopped(self, mock_bind, mock_close):
        def fake_bind():
            return True
        mock_bind.side_effect = fake_bind

        def fake_close(self):
            return True
        mock_close.side_effect = fake_close

        current_status = status.get_status()
        self.assertIn("running_mode", current_status)
        self.assertFalse(current_status['server']['value_raw'])
        self.assertEquals(current_status['server']['value'], "Stopped")

    @mock.patch("socket.socket.bind")
    @mock.patch("socket.socket.close")
    def test_get_status_server_running(self, mock_bind, mock_close):
        def fake_bind():
            raise socket.error("Already bound.")
        mock_bind.side_effect = fake_bind

        def fake_close(self):
            return True
        mock_close.side_effect = fake_close

        current_status = status.get_status()
        self.assertIn("running_mode", current_status)
        self.assertTrue(current_status['server']['value_raw'])
        self.assertEquals(current_status['server']['value'], "Running")

    def test_cli_status(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--remote", default=None)
        subparsers = parser.add_subparsers()
        status.cli_subparser(subparsers)

        stdout = sys.stdout

        sys.stdout = StringIO()
        args = parser.parse_args(["status"])
        args.func(parser, args)

        self.assertEquals(len(sys.stdout.getvalue().strip().split("\n")), 7)

        sys.stdout = stdout
