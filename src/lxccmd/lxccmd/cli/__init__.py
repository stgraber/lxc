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
from __future__ import print_function
import sys


def render_table(data, header=False, orientation="horizontal"):
    """
        Render a simple table on screen.
        data is a list of list.
        header is a boolean indicating whether the first line is a header.
        orientation can be horizontal or vertical.

        It's assumed every list in data is of the same length.
    """

    if not data:
        return

    if orientation == "vertical":
        # Shift the array
        old_data = data
        data = []
        index = 0
        for i in range(len(old_data)):
            for j in range(len(old_data[i])):
                if len(data) <= j:
                    data.append([])

                data[j].append(old_data[i][j])

    # Get the maximum size for each field
    max_length = {}
    for line in data:
        for i in range(len(line)):
            if not i in max_length:
                max_length[i] = len(line[i])
                continue

            if max_length[i] < len(line[i]):
                max_length[i] = len(line[i])

    # Generate the line format string based on the maximum length and
    # a 2 character padding
    line_format = ""
    index = 0
    for field in range(len(data[0])):
        if orientation == "vertical" and header and field == 0:
            line_format += "{fields[%s]:%s}|  " % (index,
                                                   max_length[field] + 2)
        else:
            line_format += "{fields[%s]:%s}" % (index, max_length[field] + 2)
        index += 1

    # Figure out the max line length
    line_length = -2
    for field, length in max_length.items():
        line_length += length + 2

    if orientation == "horizontal":
        if header:
            if sys.version_info.major == 2:  # pragma: no cover
                print(line_format.format(fields=data[0]).strip().decode())
            else:  # pragma: no cover
                print(line_format.format(fields=data[0]).strip())
            print(b"-".decode() * line_length)

            if len(data) > 1:
                data = data[1:]
            else:
                data = []

    for line in data:
        if sys.version_info.major == 2:  # pragma: no cover
            print(line_format.format(fields=line).strip().decode())
        else:  # pragma: no cover
            print(line_format.format(fields=line).strip())
