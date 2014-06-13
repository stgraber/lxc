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

import sys
import unittest

from io import StringIO

from lxccmd import cli


class CLITests(unittest.TestCase):
    def test_render_table_empty(self):
        self.assertIsNone(cli.render_table([]))

    def test_render_table_horizontal(self):
        stdout = sys.stdout
        sys.stdout = StringIO()

        cli.render_table([["abc", "def", "ghi"], ["jkl", "lmn", "opq"]],
                         orientation="horizontal")

        self.assertEquals(sys.stdout.getvalue(), """abc  def  ghi
jkl  lmn  opq
""")

        sys.stdout = stdout

    def test_render_table_horizontal_header(self):
        stdout = sys.stdout
        sys.stdout = StringIO()

        cli.render_table([["abc", "def", "ghi"], ["jkl", "lmn", "opq"]],
                         orientation="horizontal", header=True)

        self.assertEquals(sys.stdout.getvalue(), """abc  def  ghi
-------------
jkl  lmn  opq
""")

        sys.stdout = stdout

    def test_render_table_horizontal_header_only(self):
        stdout = sys.stdout
        sys.stdout = StringIO()

        cli.render_table([["abc", "def", "ghi"]],
                         orientation="horizontal", header=True)

        self.assertEquals(sys.stdout.getvalue(), """abc  def  ghi
-------------
""")

        sys.stdout = stdout

    def test_render_table_vertical(self):
        stdout = sys.stdout
        sys.stdout = StringIO()

        cli.render_table([["abc", "def", "ghi"], ["jkl", "lmn", "opq"]],
                         orientation="vertical")

        self.assertEquals(sys.stdout.getvalue(), """abc  jkl
def  lmn
ghi  opq
""")

        sys.stdout = stdout

    def test_render_table_vertical_header(self):
        stdout = sys.stdout
        sys.stdout = StringIO()

        cli.render_table([["abc", "def", "ghi"], ["jkl", "lmn", "opq"]],
                         orientation="vertical", header=True)

        self.assertEquals(sys.stdout.getvalue(), """abc  |  jkl
def  |  lmn
ghi  |  opq
""")

        sys.stdout = stdout
