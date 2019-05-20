#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019  Esrille Inc.
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
# License along with this library; if not, see <http://www.gnu.org/licenses/>.

import sys


class GetText:

    def __init__(self):
        self.strings = set()

    def scanline(self, line):
        while line:
            pos = line.find("_(")
            if pos < 0:
                return
            line = line[pos + 2:].strip()
            if line[0] not in "'\"":
                return
            d = line[0]
            line = line[1:]
            s = d
            escape = False
            for c in line:
                if escape:
                    s += '\\' + c
                    escape = False
                elif c == '\\':
                    escape = True
                elif c == d:
                    s += d
                    d = ''
                    break
                else:
                    s += c
            if d:
                return
            line = line[len(s) - 1:].strip()
            if not line or line[0] != ')':
                return
            line = line[1:]
            self.strings.add(s)

    def scan(self, filename):
        with open(filename, 'r') as file:
            for line in file:
                self.scanline(line)

    def emit(self, filename):
        with open(filename, 'w') as f:
            f.write("{\n")
            sep = ''
            for string in sorted(self.strings):
                f.write(sep + "    " + string + ": " + string)
                sep = ",\n"
            f.write("\n}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(0)
    output = 'output.json'
    gettext = GetText()
    for filename in sys.argv[1:]:
        if filename == '-o':
            output = ''
            continue
        if not output:
            output = filename
            continue
        gettext.scan(filename)
    if output:
        gettext.emit(output)
