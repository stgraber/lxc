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
import importlib
import logging
import os


def get_commands():
    """
        Returns a copy of the dict of command names and matching module.
    """

    commands = {}

    for command in os.listdir(os.path.dirname(__file__)):
        full_path = os.path.join(os.path.dirname(__file__), command)
        if not os.path.isdir(full_path):
            logging.debug("Ignoring %s: not a directory",
                          full_path)
            continue

        if not os.path.isfile(os.path.join(full_path, "__init__.py")):
            logging.debug("Ignoring %s: doesn't contain __init__.py",
                          full_path)
            continue

        try:
            commands[command] = importlib.import_module(
                "lxccmd.commands.%s" % command)
            logging.info("Successfully imported command: %s" % command)
        except Exception as e:
            logging.error("Failed to import command %s: %s" % (command, e))

    return commands
