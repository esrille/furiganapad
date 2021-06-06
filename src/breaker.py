#
# Copyright (c) 2021  Esrille Inc.
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


import icu
import logging


logger = logging.getLogger(__name__)

IAA = '\uFFF9'  # IAA (INTERLINEAR ANNOTATION ANCHOR)
IAS = '\uFFFA'  # IAS (INTERLINEAR ANNOTATION SEPARATOR)
IAT = '\uFFFB'  # IAT (INTERLINEAR ANNOTATION TERMINATOR)

PLAIN = 0
BASE = 1
RUBY = 2

# Note 'を' is intentionally removed from HIRAGANA_BREAK.
HIRAGANA_BREAK = ("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん"
                  "ゔがぎぐげござじずぜぞだぢづでどばびぶべぼぁぃぅぇぉゃゅょっぱぴぷぺぽゎゐゑゝゞ")


def is_hiragana_break(s, offset):
    if offset <= 0 or len(s) <= offset:
        return False
    if s[offset - 1] in HIRAGANA_BREAK and s[offset] in (HIRAGANA_BREAK + 'を'):
        return True
    return False


class Breaker:
    def __init__(self, text=''):
        self.length = 0
        self.cursor_positions = []
        self.word_starts = []
        self.word_ends = []
        if text:
            self.set_text(text)

    def following(self, offset):
        assert 0 <= offset <= self.length
        while True:
            offset += 1
            if self.length < offset:
                return offset
            if self.cursor_positions[offset]:
                return offset

    def following_word_end(self, offset):
        assert 0 <= offset <= self.length
        while True:
            offset += 1
            if self.length < offset:
                return offset
            if self.word_ends[offset]:
                return offset

    def preceding(self, offset):
        assert 0 <= offset <= self.length
        while True:
            offset -= 1
            if offset < 0:
                return offset
            if self.cursor_positions[offset]:
                return offset

    def preceding_word_start(self, offset):
        assert 0 <= offset <= self.length
        while True:
            offset -= 1
            if offset < 0:
                return offset
            if self.word_starts[offset]:
                return offset

    def set_text(self, text):
        self.length = len(text)
        if not text:
            self.cursor_positions = []
            self.word_starts = []
            self.word_ends = []
            return

        self.cursor_positions = [0] * (self.length + 1)
        self.word_starts = [0] * (self.length + 1)
        self.word_ends = [0] * (self.length + 1)
        u16str = text.encode('utf_16_le')

        # Calculate cursor_positions
        boundary = icu.BreakIterator.createCharacterInstance(icu.Locale.getJapan())
        boundary.setText(text)
        u16offset = boundary.first()
        offset = len(u16str[:u16offset * 2].decode('utf_16_le', 'ignore'))
        self.cursor_positions[offset] = 1
        mode = PLAIN
        for u16offset in boundary:
            c = text[offset]    # previous character
            offset = len(u16str[:u16offset * 2].decode('utf_16_le', 'ignore'))
            d = text[offset] if offset < self.length else ''    # next character
            if c == IAA:
                mode = BASE
            elif d == IAS:
                mode = RUBY
            elif d == IAT:
                mode = PLAIN
            elif mode != RUBY:
                self.cursor_positions[offset] = 1
        self.cursor_positions[-1] = 1

        # Calculate word_starts and word_ends
        boundary = icu.BreakIterator.createWordInstance(icu.Locale.getJapan())
        boundary.setText(text)
        u16offset = boundary.first()
        offset = len(u16str[:u16offset * 2].decode('utf_16_le', 'ignore'))
        for u16offset in boundary:
            if self.cursor_positions[offset]:
                if not text[offset].isspace() and not is_hiragana_break(text, offset):
                    self.word_starts[offset] = 1
            elif 0 < offset and text[offset - 1] == IAA:
                self.word_starts[offset - 1] = 1
            offset = len(u16str[:u16offset * 2].decode('utf_16_le', 'ignore'))
            if self.cursor_positions[offset]:
                if 0 < offset and not text[offset - 1].isspace() and not is_hiragana_break(text, offset):
                    self.word_ends[offset] = 1
            elif 1 < offset and text[offset - 1] == IAA:
                self.word_ends[offset - 1] = 1
        self.word_starts[0] = 1
        self.word_ends[-1] = 1
