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


IAA = '\uFFF9'  # IAA (INTERLINEAR ANNOTATION ANCHOR)
IAS = '\uFFFA'  # IAS (INTERLINEAR ANNOTATION SEPARATOR)
IAT = '\uFFFB'  # IAT (INTERLINEAR ANNOTATION TERMINATOR)


class Converter:

    def __init__(self):
        self.tr = str.maketrans({
            IAA: '<ruby>',
            IAS: '<rp>(</rp><rt>',
            IAT: '</rt><rp>)</rp></ruby>'
        })

    def convert_line(self, line):
        print(line.translate(self.tr), end='')

    def convert(self, filename):
        with open(filename, 'r') as file:
            for line in file:
                self.convert_line(line)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(0)

    converter = Converter()
    converter.convert(sys.argv[1])
