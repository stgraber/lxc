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

import os
import subprocess
import unittest


class StaticTests(unittest.TestCase):
    def all_paths(self):
        paths = []
        for dirpath, dirnames, filenames in os.walk("."):
            for ignore in ".bzr", "__pycache__":
                if ignore in dirnames:
                    dirnames.remove(ignore)
            filenames = [
                n for n in filenames
                if not n.startswith(".") and not n.endswith("~")]
            if dirpath.split(os.sep)[-1] == "bin":
                for filename in filenames:
                    if filename in ("simg2img"):
                        continue

                    paths.append(os.path.join(dirpath, filename))
            else:
                for filename in filenames:
                    if filename.endswith(".py"):
                        paths.append(os.path.join(dirpath, filename))
        return paths

    @unittest.skipIf(not os.path.exists("/usr/bin/pep8"),
                     "Missing pep8, skipping test.")
    def test_pep8_clean(self):
        subp = subprocess.Popen(
            ["pep8"] + self.all_paths(),
            stdout=subprocess.PIPE, universal_newlines=True)
        output = subp.communicate()[0].splitlines()
        for line in output:
            print(line)
        self.assertEqual(0, len(output))

    @unittest.skipIf(not os.path.exists("/usr/bin/pyflakes"),
                     "Missing pyflakes, skipping test.")
    def test_pyflakes_clean(self):
        subp = subprocess.Popen(
            ["pyflakes"] + self.all_paths(),
            stdout=subprocess.PIPE, universal_newlines=True)
        output = subp.communicate()[0].splitlines()
        for line in output:
            print(line)
        self.assertEqual(0, len(output))

    @unittest.skipIf(not os.path.exists("/usr/bin/pyflakes3"),
                     "Missing pyflakes, skipping test.")
    def test_pyflakes3_clean(self):
        subp = subprocess.Popen(
            ["pyflakes3"] + self.all_paths(),
            stdout=subprocess.PIPE, universal_newlines=True)
        output = subp.communicate()[0].splitlines()
        for line in output:
            print(line)
        self.assertEqual(0, len(output))
