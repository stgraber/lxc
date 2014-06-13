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
import os


def config_get_string(section, key, default=None):
    return None


def get_config_path():
    """
        Returns the path to the configuration directory.
    """

    if "HOME" in os.environ:
        return os.path.join(os.environ["HOME"], ".config", "lxc")

    return os.path.join(os.getcwd(), ".config", "lxc")


def get_run_path():
    """
        Returns the path to the runtime directory.
    """

    run_path = config_get_string("global", "run_path")
    if run_path:
        return run_path

    if "XDG_RUNTIME_DIR" in os.environ:
        return os.path.join(os.environ["XDG_RUNTIME_DIR"], "lxc")

    return os.path.join("/tmp", "lxc-%s" % os.geteuid())
