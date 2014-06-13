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

import logging
import unittest

from lxccmd import commands

try:
    from unittest import mock
except ImportError:
    import mock


class CommandsTests(unittest.TestCase):
    def test_get_commands(self):
        self.assertIn("status", commands.get_commands())

    @mock.patch("importlib.import_module")
    def test_get_commands_fail(self, mock_import_module):
        def fake_import_module(path):
            raise ImportError("Failed to import")
        mock_import_module.side_effect = fake_import_module

        old_level = logging.root.level
        logging.root.setLevel(100)
        self.assertNotIn("status", commands.get_commands())
        logging.root.setLevel(old_level)
