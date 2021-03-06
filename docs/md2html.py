#!/usr/bin/env python3
#
# Copyright (c) 2017-2020 Esrille Inc.
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

import html
import markdown
import re
import sys
import textwrap

from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension


IAA = '\uFFF9'  # IAA (INTERLINEAR ANNOTATION ANCHOR)
IAS = '\uFFFA'  # IAS (INTERLINEAR ANNOTATION SEPARATOR)
IAT = '\uFFFB'  # IAT (INTERLINEAR ANNOTATION TERMINATOR)

title = ''


class MyPreprocessor(Preprocessor):

    def strip_ruby(self, line):
        br = line.find('<br>')
        if 0 <= br:
            line = line[:br]
        iaa = line.find(IAA)
        while 0 <= iaa:
            line = line[:iaa] + line[iaa + 1:]
            ias = line.find(IAS)
            iat = line.find(IAT)
            line = line[:ias] + line[iat + 1:]
            iaa = line.find(IAA)
        return line

    def run(self, lines):
        global title
        tr = str.maketrans({
            IAA: '<ruby>',
            IAS: '<rp>(</rp><rt>',
            IAT: '</rt><rp>)</rp></ruby>'
        })
        pre = False
        new_lines = []
        for line in lines:
            if line:
                if line.startswith("# "):
                    title = line[2:].strip(' \n\r')
                    title = self.strip_ruby(title)
                line = line.translate(tr)
                if line.startswith("```"):
                    pre = pre ^ True
                elif not pre:
                    if line.startswith('　'):
                        line = '\n' + line
                    line = line.replace('　', '&#x3000;')
                else:
                    line += '↲'
                    if not new_lines[-1].startswith("```"):
                        new_lines[-1] = new_lines[-1] + line
                        continue
            new_lines.append(line)
        return new_lines


class MyExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        # Insert code here to change markdown's behavior.
        md.preprocessors.add('my', MyPreprocessor(md), '_begin')


def main():
    global title

    if len(sys.argv) < 2:
        print('Usage: md2html path/to/file prev next [template]',
              file=sys.stderr)
        sys.exit(1)

    prev_url = next_url = ''
    if 4 <= len(sys.argv):
        prev_url = sys.argv[2][:-2] + 'html'
        next_url = sys.argv[3][:-2] + 'html'

    path = 'template.html'
    if 5 <= len(sys.argv):
        path = sys.argv[4]
    template = ''
    with open(path) as file:
        for line in file:
            template += line

    path = sys.argv[1]
    source = ''
    with open(path) as file:
        for line in file:
            source += line

    md = markdown.Markdown(extensions=[MyExtension(),
                                       'markdown.extensions.meta',
                                       'markdown.extensions.sane_lists',
                                       'markdown.extensions.tables',
                                       'markdown.extensions.extra',
                                       'markdown.extensions.attr_list'],
                           output_format='html5')

    body = md.convert(source)
    description = title
    og_image = 'https://esrille.github.io/ibus-hiragana/screenshot.png'
    if 'summary' in md.Meta:
        description = ' '.join(md.Meta['summary'])
    if 'language' in md.Meta:
        template = template.replace(
            "<html lang='ja'>",
            "<html lang='" + md.Meta['language'][0] + "'>",
            1)
    if 'og_image' in md.Meta:
        og_image = md.Meta['og_image'][0]

    path = path[:-2] + 'html'
    content = textwrap.dedent(
        template.format(body=body,
                        title=html.escape(title),
                        prev_url=prev_url,
                        next_url=next_url,
                        description=html.escape(description),
                        og_image=html.escape(og_image),
                        path=path))

    content = content.replace("。\n", "。")
    content = content.replace("↲", "\n")
    content = content.replace("\n</code></pre>", "</code></pre>")

    with open(path, 'w') as file:
        file.write(content)


if __name__ == '__main__':
    main()
