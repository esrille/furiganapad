#!/usr/bin/env python3
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

import os
import signal
import sys
import time
import locale
import json
import cairo

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import GLib, Gio, Gtk, Gdk, GObject, Pango, PangoCairo


IAA = '\uFFF9'  # IAA (INTERLINEAR ANNOTATION ANCHOR)
IAS = '\uFFFA'  # IAS (INTERLINEAR ANNOTATION SEPARATOR)
IAT = '\uFFFB'  # IAT (INTERLINEAR ANNOTATION TERMINATOR)
HIRAGANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんゔがぎぐげござじずぜぞだぢづでどばびぶべぼぁぃぅぇぉゃゅょっぱぴぷぺぽゎゐゑ・ーゝゞ"
KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンヴガギグゲゴザジズゼゾダヂヅデドバビブベボァィゥェォャュョッパピプペポヮヰヱ・ーヽヾ"
NEWLINES = "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"

# A sentence with more than SENTENCE_SHORT characters is not short.
SENTENCE_SHORT = 50
# A sentence with more than SENTENCE_LONG characters is long.
SENTENCE_LONG = 60

DEFAULT_FONT = "Noto Sans Mono CJK JP 16px"


def to_hiragana(s):
    t = ''
    for c in s:
        i = KATAKANA.find(c)
        if i == -1:
            t += c
        else:
            t += HIRAGANA[i]
    return t


def is_kana(s):
    for c in s:
        if c not in HIRAGANA + KATAKANA:
            return False
    return True


def is_reading(s):
    for c in s:
        if c not in HIRAGANA + '―':
            return False
    return True


def has_newline(s):
    for c in s:
        if c in NEWLINES:
            return True
    return False


class Paragraph:

    PLAIN = 0
    BASE = 1
    RUBY = 2

    def __init__(self, text=''):
        self.text = text
        self.plain = ''
        self.rubies = list()

    def set_text(self, text):
        self.text = text
        self.plain = ''
        self.rubies.clear()

    def get_text(self):
        return self.text

    def get_length(self):
        # plus one as a newline at the end of the line
        return len(self.text) + 1

    def insert(self, offset, text):
        assert offset <= len(self.text)
        self.set_text(self.text[:offset] + text + self.text[offset:])

    def split(self, offset):
        assert offset <= len(self.text)
        next = Paragraph(self.text[offset:])
        self.set_text(self.text[:offset])
        return next

    def get_plain_text(self):
        if self.plain:
            return self.plain
        mode = self.PLAIN
        i = 0
        ruby = ''
        for c in self.text:
            if c == IAA:
                mode = self.BASE
                pos = i
            elif c == IAS:
                mode = self.RUBY
                len = i - pos
            elif c == IAT:
                mode = self.PLAIN
                self.rubies.append([pos, len, ruby])
                ruby = ''
            elif mode == self.RUBY:
                ruby += c
            else:
                self.plain += c
                i += 1
        return self.plain

    def get_plain_length(self):
        # plus one as a newline at the end of the line
        return len(self.get_plain_text()) + 1

    def _get_plain_offset(self, offset):
        mode = self.PLAIN
        i = 0
        len = 0
        for c in self.text:
            if i == offset:
                break
            if c == IAA:
                mode = self.BASE
            elif c == IAS:
                mode = self.RUBY
            elif c == IAT:
                mode = self.PLAIN
            elif mode == self.RUBY:
                pass
            else:
                len += 1
            i += 1
        return len

    def _expand_plain_offset(self, offset):
        mode = self.PLAIN
        i = 0
        length = 0
        for c in self.text:
            if length == offset:
                if i < len(self.text) and self.text[i] == IAS:
                    i = self.text.find(IAT, i + 1) + 1
                break
            if c == IAA:
                mode = self.BASE
            elif c == IAS:
                mode = self.RUBY
            elif c == IAT:
                mode = self.PLAIN
            elif mode == self.RUBY:
                pass
            else:
                length += 1
            i += 1
        return i

    def _forward_cursor_position(self, offset):
        if len(self.text) <= offset:
            return len(self.text) + 1
        mode = self.PLAIN
        if self.text[offset] == IAA:
            offset += 1
        offset += 1
        for c in self.text[offset:]:
            if c == IAA:
                return offset
            elif c == IAS:
                mode = self.RUBY
            elif c == IAT:
                mode = self.PLAIN
            elif mode == self.RUBY:
                pass
            else:
                return offset
            offset += 1
        return len(self.text)

    def _forward_search(self, offset, str, flags):
        plain = self.get_plain_text()
        offset = self._get_plain_offset(offset)
        offset = plain.find(str, offset)
        if offset < 0:
            return None
        end = self._expand_plain_offset(offset + len(str))
        offset = self._expand_plain_offset(offset)
        return (offset, end)

    def _backward_cursor_position(self, offset):
        if offset <= 0:
            return -1
        mode = self.PLAIN
        for c in reversed(self.text[:offset]):
            offset -= 1
            if c == IAA:
                mode = self.PLAIN
            elif c == IAS:
                mode = self.BASE
            elif c == IAT:
                mode = self.RUBY
            elif mode == self.RUBY:
                pass
            else:
                if 0 < offset and self.text[offset - 1] == IAA:
                    offset -= 1
                return offset
        return -1

    def _inside_ruby(self, offset):
        assert offset < self.get_length()
        for c in self.text[offset:]:
            if c == IAA:
                return False
            elif c == IAS:
                return True
            elif c == IAT:
                return True
        return False


class TextIter:

    def __init__(self, buffer, line=0, offset=0):
        self.buffer = buffer
        self.line = line
        self.offset = offset

    def __lt__(self, other):
        if self.line < other.line:
            return True
        if other.line < self.line:
            return False
        return self.offset < other.offset

    def __le__(self, other):
        if self.line < other.line:
            return True
        if other.line < self.line:
            return False
        return self.offset <= other.offset

    def __eq__(self, other):
        return self.line == other.line and self.offset == other.offset

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def assign(self, other):
        self.buffer = other.buffer
        self.line = other.line
        self.offset = other.offset

    def copy(self):
        return TextIter(self.buffer, self.line, self.offset)

    def backward_char(self):
        return self.forward_chars(-1)

    def backward_chars(self, count):
        return self.forward_chars(-count)

    def backward_cursor_position(self):
        return self.buffer._backward_cursor_position(self)

    def backward_cursor_positions(self, count):
        if count == 0:
            return False
        if count < 0:
            return self.forward_cursor_positions(-count)
        for i in range(count):
            if not self.backward_cursor_position():
                return False
        return True

    def forward_char(self):
        return self.forward_chars(1)

    def forward_chars(self, count):
        return self.buffer._forward_chars(self, count)

    def forward_cursor_position(self):
        return self.buffer._forward_cursor_position(self)

    def forward_cursor_positions(self, count):
        if count == 0:
            return False
        if count < 0:
            return self.backward_cursor_positions(-count)
        for i in range(count):
            if not self.forward_cursor_position():
                return False
        return True

    def forward_lines(self, count):
        if self.line + count < self.buffer.get_line_count():
            self.line += count
            self.offset = 0
            return True
        self.line = self.buffer.get_line_count() - 1
        self.offset = self.buffer.paragraphs[self.line].get_length() - 1
        return False

    def forward_search(self, str, flags, limit):
        if not str:
            return None
        if limit and limit <= str:
            return None
        return self.buffer._forward_search(self, str, flags, limit)

    def get_buffer(self):
        return self.buffer

    def get_line(self):
        return self.line

    def get_line_offset(self):
        return self.offset

    def get_plain_line_offset(self):
        return self.buffer._get_plain_line_offset(self)

    def inside_ruby(self):
        return self.buffer._inside_ruby(self)

    def set_line(self, line_number):
        self.line = line_number

    def set_line_offset(self, char_on_line):
        self.offset = char_on_line


class TextMark():

    def __init__(self, iter):
        self.iter = TextIter(iter.get_buffer())
        self.iter.assign(iter)

    # The cursor has moved from start to end.
    def on_insert(self, start, end):
        if self.iter < start:
            return
        if self.iter == start:
            self.iter.assign(end)
            return
        d = self.iter.get_line() - start.get_line()
        self.iter.set_line(end.get_line() + d)
        if 0 < d:
            return
        d = self.iter.get_line_offset() - start.get_line_offset()
        self.iter.set_line_offset(end.get_line_offset() + d)

    def on_delete(self, start, end):
        if self.iter <= start:
            return
        if self.iter <= end:
            self.iter.assign(start)
            return
        d = self.iter.get_line() - end.get_line()
        self.iter.set_line(start.get_line() + d)
        if 0 < d:
            return
        d = self.iter.get_line_offset() - end.get_line_offset()
        self.iter.set_line_offset(start.get_line_offset() + d)


class TextBuffer(GObject.Object):

    __gsignals__ = {
        'insert_text': (GObject.SIGNAL_RUN_LAST, None, (object, str, )),
        'delete_range': (GObject.SIGNAL_RUN_LAST, None, (object, object, )),
        'begin_user_action': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'end_user_action': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'undo': (GObject.SIGNAL_RUN_LAST, None, ()),
        'redo': (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self.modified = False
        self.marks = {}
        self.paragraphs = list()
        self.reading = ''
        self.surround_deleted = False
        self.annotated = ''
        self.ruby_mode = True

        # Undo buffers
        self.user_action = False
        self.undo = []  # undo buffer
        self.redo = []  # redo buffer
        self.inserting = None

        # TextBuffer always contains at least one line
        paragraph = Paragraph()
        self.paragraphs.append(paragraph)

        # Create the default textmarks
        iter = self.get_start_iter()
        self.create_mark("insert", iter)
        self.create_mark("selection_bound", iter)

        # Connect operations for undo and redo
        self.connect("insert_text", self.on_insert)
        self.connect_after("insert_text", self.on_inserted)
        self.connect("delete_range", self.on_delete)

    def _empty(self):
        if 1 < self.get_line_count():
            return False
        return self.paragraphs[0].get_length() == 1

    def __annotate(self, s, r):
        if is_kana(s):
            return s
        pos = r.find('―')
        if 0 <= pos:
            r = r[:pos] + r[pos+1:]
        before = ''
        for i in range(len(s)):
            if i < len(r) and to_hiragana(s[i]) == r[i]:
                before += s[i]
            else:
                break
        if before:
            s = s[len(before):]
            r = r[len(before):]
        after = ''
        for i in range(len(s)):
            if i < len(r) and to_hiragana(s[-1-i]) == r[-1-i]:
                after = s[-1-i] + after
            else:
                break
        if after:
            s = s[:-len(after)]
            r = r[:-len(after)]
        if s and r:
            s = IAA + s + IAS + r + IAT
        return before + s + after

    def _forward_chars(self, iter, count):
        if count == 0:
            return False
        lineno = iter.get_line()
        offset = iter.get_line_offset() + count
        while True:
            length = self.paragraphs[lineno].get_length()
            if 0 <= offset and offset < length:
                iter.set_line(lineno)
                iter.set_line_offset(offset)
                return True
            if length <= offset:
                lineno += 1
                if len(self.paragraphs) <= lineno:
                    lineno = 0
                offset -= length
            else:
                lineno -= 1
                if lineno < 0:
                    lineno = len(self.paragraphs) - 1
                offset += self.paragraphs[lineno].get_length()

    def _backward_cursor_position(self, iter):
        lineno = iter.get_line()
        offset = iter.get_line_offset()
        offset = self.paragraphs[lineno]._backward_cursor_position(offset)
        if 0 <= offset:
            iter.set_line_offset(offset)
            return True
        lineno -= 1
        if 0 <= lineno:
            iter.set_line(lineno)
            iter.set_line_offset(self.paragraphs[lineno].get_length() - 1)
            return True
        return False

    def _forward_cursor_position(self, iter):
        lineno = iter.get_line()
        offset = iter.get_line_offset()
        offset = self.paragraphs[lineno]._forward_cursor_position(offset)
        if offset < self.paragraphs[lineno].get_length():
            iter.set_line_offset(offset)
            return True
        lineno += 1
        if lineno < len(self.paragraphs):
            iter.set_line(lineno)
            iter.set_line_offset(0)
            return True
        return False

    def _forward_search(self, iter, str, flags, limit):
        while True:
            lineno = iter.get_line()
            offset = iter.get_line_offset()
            bounds = self.paragraphs[lineno]._forward_search(offset, str, flags)
            if bounds:
                iter.set_line_offset(bounds[0])
                end = iter.copy()
                end.set_line_offset(bounds[1])
                if not limit or end <= limit:
                    return (iter, end)
                else:
                    return None
            if not iter.forward_lines(1):
                return None
            if limit and limit <= iter:
                return None

    def _get_plain_line_offset(self, iter):
        return self.paragraphs[iter.get_line()]._get_plain_offset(iter.get_line_offset())

    def _inside_ruby(self, iter):
        return self.paragraphs[iter.get_line()]._inside_ruby(iter.get_line_offset())

    def begin_user_action(self):
        self.user_action = True
        self.emit('begin_user_action')

    def copy_clipboard(self, clipboard):
        start, end = self.get_selection_bounds()
        if start == end:
            return
        text = self.get_text(start, end, True)
        clipboard.set_text(text, -1)

    def create_mark(self, mark_name, where):
        self.marks[mark_name] = TextMark(where)

    def cut_clipboard(self, clipboard, default_editable):
        start, end = self.get_selection_bounds()
        if start == end:
            return
        text = self.get_text(start, end, True)
        self.delete_selection(True, default_editable)
        clipboard.set_text(text, -1)

    def delete(self, start, end):
        if start == end:
            return
        if end < start:
            start, end = end, start

        # Check annotation before 'start'
        self.annotated = ''
        cursor = start.copy()
        text = self.paragraphs[start.get_line()].get_text()
        offset = pos = start.get_line_offset()
        d = ''
        i = 0
        for c in text[pos:]:
            if c == IAA:
                break
            elif c == IAS:
                d = IAA
                break
            elif c == IAT:
                d = IAS
                break
            i += 1
            cursor.set_line_offset(pos + i)
            if end <= cursor:
                break
        if d == IAS:
            pos = text.rfind(IAS, 0, pos)
            d = IAA
        if d == IAA:
            offset = text.rfind(IAA, 0, pos)
            self.annotated = text[offset+1:pos]
        start.set_line_offset(offset)

        # Check annotation after 'end'
        cursor = end.copy()
        text = self.paragraphs[end.get_line()].get_text()
        offset = pos = end.get_line_offset()
        d = ''
        i = 0
        for c in reversed(text[:pos]):
            if c == IAA:
                d = IAS
                break
            elif c == IAS:
                d = IAT
                break
            elif c == IAT:
                break
            i -= 1
            cursor.set_line_offset(pos + i)
            if cursor <= start:
                break
        if d == IAS:
            offset = text.find(IAS, pos)
            self.annotated += text[pos:offset]
            pos = offset
            d = IAT
        if d == IAT:
            offset = text.find(IAT, pos) + 1
        end.set_line_offset(offset)

        for mark in self.marks.values():
            mark.on_delete(start, end)
        self.emit('delete_range', start, end)

    def do_delete_range(self, start, end):
        self.set_modified(True)

        if start.get_line() == end.get_line():
            text = self.paragraphs[start.get_line()].get_text()
            text = text[:start.get_line_offset()] + text[end.get_line_offset():]
            self.paragraphs[start.get_line()].set_text(text)
            end.set_line_offset(start.get_line_offset())
        else:
            lineno = end.get_line()
            if start.get_line() + 1 < lineno:
                del self.paragraphs[start.get_line()+1:lineno]
                lineno = start.get_line() + 1

            text = self.paragraphs[lineno].get_text()[end.get_line_offset():]
            del self.paragraphs[lineno]
            lineno -= 1
            text = self.paragraphs[lineno].get_text()[:start.get_line_offset()] + text
            self.paragraphs[lineno].set_text(text)
            end.set_line(lineno)
            end.set_line_offset(start.get_line_offset())

        # Insert annotated text again without the annotation
        if self.annotated:
            self.insert(start, self.annotated)
            self.annotated = ''

    def delete_selection(self, interactive, default_editable):
        if not self.get_has_selection():
            return False
        if interactive:
            self.begin_user_action()
            self.delete(self.get_anchor(), self.get_cursor())
            self.end_user_action()
        else:
            self.delete(self.get_anchor(), self.get_cursor())
        return True

    def end_user_action(self):
        self.emit('end_user_action')
        self.user_action = False

    def get_bounds(self):
        start = self.get_start_iter()
        end = self.get_end_iter()
        return start, end

    def get_anchor(self):
        return self.get_selection_bound().iter.copy()

    def get_cursor(self):
        return self.get_insert().iter.copy()

    def get_end_iter(self):
        lineno = self.get_line_count() - 1
        return TextIter(self, lineno, self.paragraphs[lineno].get_length() - 1)

    def get_has_selection(self):
        return self.get_selection_bound().iter != self.get_insert().iter

    def get_insert(self):
        return self.marks["insert"]

    def get_iter_at_offset(self, offset):
        pass

    def get_iter_at_line_offset(self, line_number, char_offset):
        assert line_number < self.get_line_count()
        assert char_offset < self.paragraphs[line_number].get_length()
        return TextIter(self, line_number, char_offset)

    def get_iter_at_mark(self, mark):
        return mark.iter.copy()

    def get_line_count(self):
        return len(self.paragraphs)

    def get_modified(self):
        return self.modified

    def get_selection_bound(self):
        return self.marks["selection_bound"]

    def get_selection_bounds(self):
        start = self.get_anchor()
        end = self.get_cursor()
        if end < start:
            start, end = end, start
        return (start, end)

    def get_start_iter(self):
        return TextIter(self, 0, 0)

    def get_text(self, start, end, include_hidden_chars):
        if start == end:
            return ''
        if end < start:
            start, end = end, start
        line = start.get_line()
        if line == end.get_line():
            if include_hidden_chars:
                return self.paragraphs[line].get_text()[start.get_line_offset():end.get_line_offset()]
            else:
                s = self._get_plain_line_offset(start)
                e = self._get_plain_line_offset(end)
                return self.paragraphs[line].get_plain_text()[s:e]
        assert start < end
        text = ''
        if include_hidden_chars:
            text += self.paragraphs[line].get_text()[start.get_line_offset():] + '\n'
        else:
            offset = self._get_plain_line_offset(start)
            text += self.paragraphs[line].get_plain_text()[offset:] + '\n'
        line += 1
        while line < end.get_line():
            if include_hidden_chars:
                text += self.paragraphs[line].get_text() + '\n'
            else:
                text += self.paragraphs[line].get_plain_text() + '\n'
            line += 1
        assert line == end.get_line()
        if line < self.get_line_count():
            if include_hidden_chars:
                text += self.paragraphs[line].get_text()[:end.get_line_offset()]
            else:
                offset = self._get_plain_line_offset(end)
                text += self.paragraphs[line].get_plain_text()[:offset]
        return text

    def do_insert_text(self, iter, text):
        assert 0 < len(text)
        self.set_modified(True)

        lines = text.splitlines(keepends=True)
        lineno = iter.get_line()
        if 1 == len(lines) and lines[0][-1] not in NEWLINES:
            self.paragraphs[lineno].insert(iter.get_line_offset(), text)
            iter.set_line_offset(iter.get_line_offset() + len(text))
            return

        next = self.paragraphs[lineno].split(iter.get_line_offset())
        if lineno == self.get_line_count() - 1:
            self.paragraphs.append(next)
        else:
            self.paragraphs.insert(lineno + 1, next)

        text = lines[0].rstrip(NEWLINES)
        self.paragraphs[lineno].insert(iter.get_line_offset(), text)
        lines.pop(0)
        if not lines:
            iter.set_line(lineno + 1)
            iter.set_line_offset(0)
            return

        for s in lines:
            lineno += 1
            if s[-1] not in NEWLINES:
                self.paragraphs[lineno].insert(0, s)
                iter.set_line(lineno)
                iter.set_line_offset(len(s))
                return
            p = Paragraph(s.rstrip(NEWLINES))
            self.paragraphs.insert(lineno, p)
        iter.set_line(lineno + 1)
        iter.set_line_offset(0)

    def insert(self, iter, text):
        if not text:
            self.surround_deleted = False
            return
        if self._empty():
            if text.endswith('\r\n'):
                text = text[:-2]
            elif text[-1] in NEWLINES:
                text = text[:-1]
        if self.surround_deleted and self.ruby_mode and not iter.inside_ruby():
            text = self.__annotate(text, self.reading)
        self.surround_deleted = False
        start = TextIter(self)
        start.assign(iter)
        self.emit('insert_text', iter, text)
        for mark in self.marks.values():
            mark.on_insert(start, iter)

    def insert_at_cursor(self, text):
        self.delete_selection(False, True)
        self.insert(self.get_cursor(), text)

    def move_cursor(self, cursor, is_selection):
        if is_selection:
            self.move_mark(self.get_insert(), cursor)
        else:
            self.place_cursor(cursor)

    def move_mark(self, mark, where):
        mark.iter.assign(where)

    def place_cursor(self, where):
        self.select_range(where, where)

    def select_range(self, ins, bound):
        self.move_mark(self.get_insert(), ins)
        self.move_mark(self.get_selection_bound(), bound)

    def select_all(self):
        start, end = self.get_bounds()
        self.select_range(start, end)

    def set_modified(self, setting):
        if self.modified == setting:
            return
        self.modified = setting
        if not self.modified:
            self.undo = []
            self.redo = []

    def set_ruby_mode(self, ruby):
        self.ruby_mode = ruby

    def set_text(self, text):
        start, end = self.get_bounds()
        self.delete(start, end)
        self.insert(start, text)
        iter = self.get_start_iter()
        self.place_cursor(iter)

    def get_surrounding(self):
        cursor = self.get_cursor()
        return self.paragraphs[cursor.get_line()].get_text(), cursor.get_line_offset()

    def delete_surrounding(self, offset, len):
        if len == 0:
            return
        start = self.get_cursor()
        start.forward_cursor_positions(offset)
        end = start.copy()
        end.forward_cursor_positions(len)
        if end < start:
            start, end = end, start
            if len < 0:
                len = -len

        assert start.get_line() == end.get_line()
        reading = self.paragraphs[start.get_line()].get_text()[start.get_line_offset():end.get_line_offset()]
        if is_reading(reading):
            self.reading = reading
            print('よみ:', self.reading)
        self.surround_deleted = True
        self.delete(start, end)

    def unconvert(self, iter):
        text = self.paragraphs[iter.get_line()].get_text()
        pos = iter.get_line_offset()
        if pos < 5 or text[pos-1] != IAT:
            return False
        mode = IAT
        ruby = ''
        size = 1
        for c in reversed(text[:pos-1]):
            size += 1
            if c == IAA:
                start = iter.copy()
                start.set_line_offset(pos - size)
                self.delete(start, iter)
                self.insert(iter, ruby)
                return True
            elif c == IAS:
                mode = IAS
            elif mode == IAT:
                ruby = c + ruby
        return False

    def on_delete(self, textbuffer, start, end):
        if self.user_action:
            text = self.get_text(start, end, True)
            action = ["delete_range",
                      start.get_line(), start.get_line_offset(),
                      end.get_line(), end.get_line_offset(),
                      text,
                      time.perf_counter()]
            print("on_delete", action)
            self.undo.append(action)
            self.redo.clear()

    def on_insert(self, textbuffer, iter, text):
        if self.user_action:
            self.inserting = iter.copy()

    def on_inserted(self, textbuffer, iter, text):
        if self.user_action:
            action = ["insert_text",
                      self.inserting.get_line(), self.inserting.get_line_offset(),
                      iter.get_line(), iter.get_line_offset(),
                      text,
                      time.perf_counter()]
            print("on_inserted", action)
            self.undo.append(action)
            self.redo.clear()
            self.inserting = None

    def do_undo(self):
        if not self.undo:
            return
        print("do_undo")
        action = self.undo.pop()
        if action[0] == "insert_text":
            start = self.get_iter_at_line_offset(action[1], action[2])
            end = self.get_iter_at_line_offset(action[3], action[4])
            self.delete(start, end)
            # Undo previous delete_range that issued within 5 msec
            # to cope with ibus-replace-with-kanji smoothly
            if self.undo:
                prev = self.undo[-1]
                if prev[0] == "delete_range" and action[6] - prev[6] < 0.005:
                    self.redo.append(action)
                    action = self.undo.pop()
                    print("do_undo", action)
                    start = self.get_iter_at_line_offset(action[1], action[2])
                    self.insert(start, action[5])
        elif action[0] == "delete_range":
            start = self.get_iter_at_line_offset(action[1], action[2])
            self.insert(start, action[5])
        self.place_cursor(start)
        self.redo.append(action)

    def do_redo(self):
        if not self.redo:
            return
        print("do_redo")
        action = self.redo.pop()
        if action[0] == "insert_text":
            start = self.get_iter_at_line_offset(action[1], action[2])
            self.insert(start, action[5])
        elif action[0] == "delete_range":
            start = self.get_iter_at_line_offset(action[1], action[2])
            end = self.get_iter_at_line_offset(action[3], action[4])
            self.delete(start, end)
            # Redo previous insert_text that issued within 5 msec
            # to cope with ibus-replace-with-kanji smoothly
            if self.redo:
                prev = self.redo[-1]
                if prev[0] == "insert_text" and action[6] - prev[6] < 0.005:
                    self.undo.append(action)
                    action = self.redo.pop()
                    print("do_redo", action)
                    start = self.get_iter_at_line_offset(action[1], action[2])
                    self.insert(start, action[5])
        self.place_cursor(start)
        self.undo.append(action)


class TextView(Gtk.DrawingArea, Gtk.Scrollable):

    __gsignals__ = {
        'cut-clipboard': (GObject.SIGNAL_RUN_LAST, None, ()),
        'copy-clipboard': (GObject.SIGNAL_RUN_LAST, None, ()),
        'paste-clipboard': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'select-all': (GObject.SIGNAL_RUN_FIRST, None, (bool,))
    }

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self._init_scrollable()
        self._init_immultiontext()

        self.buffer = TextBuffer()
        self.spacing = 12
        self.width = 0
        self.height = 0
        self.allocated_height = 0
        self.caret = Gdk.Rectangle()
        self.heights = list()
        self.highlight_sentences = True
        self.reflow_line = -1   # line number to reflow after "delete_range"; -1 to reflow every line

        self.buffer.connect_after("insert_text", self.on_inserted)
        self.buffer.connect("delete_range", self.on_delete)
        self.buffer.connect_after("delete_range", self.on_deleted)

        self.connect("draw", self.on_draw)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)
        self.connect("focus-in-event", self.on_focus_in)
        self.connect("focus-out-event", self.on_focus_out)

        self.connect('motion-notify-event', self.on_mouse_move)
        self.connect('button-press-event', self.on_mouse_press)
        self.connect('button-release-event', self.on_mouse_release)

        self.set_can_focus(True)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_MOTION_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.SCROLL_MASK)

        desc = Pango.font_description_from_string(DEFAULT_FONT)
        # desc = self.get_style().font_desc
        self.set_font(desc)

        self.tr = str.maketrans({
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;'
        })

    def _init_scrollable(self):
        self._hadjustment = self._vadjustment = None
        self._hadjust_signal = self._vadjust_signal = None

    def _init_immultiontext(self):
        self.im = Gtk.IMMulticontext()
        self.im.connect("commit", self.on_commit)
        self.im.connect("delete-surrounding", self.on_delete_surrounding)
        self.im.connect("retrieve-surrounding", self.on_retrieve_surrounding)
        self.im.connect("preedit-changed", self.on_preedit_changed)
        self.im.connect("preedit-end", self.on_preedit_end)
        self.im.connect("preedit-start", self.on_preedit_start)
        self.preedit = ('', None, 0)

    def _escape(self, str):
        return str.translate(self.tr)

    def _get_offset(self):
        offset = 0
        if self._vadjustment:
            offset = self._vadjustment.get_value()
        return offset

    def _has_preedit(self):
        return self.preedit[0]

    def get_buffer(self):
        return self.buffer

    def get_paragraph(self, line):
        if 0 <= line and line < self.get_buffer().get_line_count():
            return self.get_buffer().paragraphs[line]
        return None

    def get_editable(self):
        return True

    def get_iter_at_location(self, x, y):
        cursor = self.buffer.get_cursor()
        width = self.get_allocated_width()
        height = 0
        i = 0
        for h in self.heights:
            if y < h + height:
                context = self.create_pango_context()
                layout = Pango.Layout(context)
                desc = self.get_font()
                layout.set_font_description(desc)
                layout.set_width(width * Pango.SCALE)
                layout.set_spacing(self.spacing * Pango.SCALE)
                paragraph = self.get_paragraph(i)
                text = paragraph.get_plain_text()
                cursor_offset = len(text)
                if i == cursor.get_line() and self._has_preedit():
                    cursor_offset = cursor.get_plain_line_offset()
                    text = text[:cursor_offset] + self.preedit[0] + text[cursor_offset:]
                layout.set_text(text, -1)
                inside, index, trailing = layout.xy_to_index(x * Pango.SCALE, (y - height) * Pango.SCALE)
                offset = len(text.encode()[:index].decode())
                if cursor_offset <= offset:
                    offset -= len(self.preedit[0])
                offset = paragraph._expand_plain_offset(offset)
                if trailing:
                    offset = paragraph._forward_cursor_position(offset)
                iter = TextIter(self.buffer, i, offset)
                return inside, iter
            height += h
            i += 1
        return False, self.buffer.get_end_iter()

    def get_font(self):
        return self.font_desc

    def set_font(self, font_desc):
        self.font_desc = font_desc
        if font_desc.get_size_is_absolute():
            self.spacing = font_desc.get_size() / Pango.SCALE * 7 / 8
        else:
            context = self.create_pango_context()
            dpi = PangoCairo.context_get_resolution(context)
            self.spacing = font_desc.get_size() / Pango.SCALE * dpi / 72 * 7 / 8
        self.reflow()

    def get_check_sentences(self):
        return self.highlight_sentences

    def set_check_sentences(self, value):
        if value != self.highlight_sentences:
            self.highlight_sentences = value
            self.queue_draw()

    def place_cursor_onscreen(self):
        self.scroll_mark_onscreen(self.buffer.get_insert())

    def scroll_mark_onscreen(self, mark):
        if not self._vadjustment:
            return

        width = self.get_allocated_width()
        height = self.get_allocated_height()
        offset = self._get_offset()

        y = 0
        line = mark.iter.get_line()
        for i in range(line):
            y += self.heights[i]

        context = self.create_pango_context()
        layout = Pango.Layout(context)
        desc = self.get_font()
        layout.set_font_description(desc)
        layout.set_width(width * Pango.SCALE)
        layout.set_spacing(self.spacing * Pango.SCALE)
        text = self.buffer.paragraphs[line].get_plain_text()
        layout.set_text(text, -1)

        current = text[:mark.iter.get_plain_line_offset()]
        st, we = layout.get_cursor_pos(len(current.encode()))
        st.x, st.y, st.width, st.height = \
            st.x / Pango.SCALE - 1, st.y / Pango.SCALE, st.width / Pango.SCALE + 2, st.height / Pango.SCALE
        y += st.y
        h = self.spacing + self.caret.height

        if y < offset:
            self._vadjustment.set_value(y)
        elif offset + height <= y + h:
            y += h
            lines = height // h
            y = (y + h - 1) // h
            self._vadjustment.set_value(h * (y - lines))

        self.queue_draw()

    def _draw_rubies(self, cr, layout, paragraph, plain, height, cursor_offset):
        lt = PangoCairo.create_layout(cr)
        desc = self.get_font().copy_static()
        size = desc.get_size()
        desc.set_size(size // 2)
        lt.set_font_description(desc)
        for pos, length, ruby in paragraph.rubies:
            if self._has_preedit() and cursor_offset <= pos:
                pos += len(self.preedit[0])
            text = plain[:pos]
            left = layout.index_to_pos(len(text.encode()))
            text = plain[:pos+length-1]
            right = layout.index_to_pos(len(text.encode()))
            left.x /= Pango.SCALE
            left.y /= Pango.SCALE
            right.x += right.width
            right.x /= Pango.SCALE
            right.y /= Pango.SCALE
            if left.y == right.y:
                cr.save()
                lt.set_text(ruby, -1)
                PangoCairo.update_layout(cr, lt)
                w, h = lt.get_pixel_size()
                x = (left.x + right.x - w) / 2
                if x < 0:
                    x = 0
                elif self.width < x + w:
                    x = self.width - w
                y = height + left.y - h
                cr.move_to(x, y)
                PangoCairo.show_layout(cr, lt)
                cr.restore()
            else:
                ruby_width = right.x + self.width - left.x
                left_length = round(len(ruby) * (self.width - left.x) / ruby_width)
                if 0 < left_length:
                    text = ruby[:left_length]
                    cr.save()
                    lt.set_text(text, -1)
                    PangoCairo.update_layout(cr, lt)
                    w, h = lt.get_pixel_size()
                    x = self.width - w
                    y = height + left.y - h
                    cr.move_to(x, y)
                    PangoCairo.show_layout(cr, lt)
                    cr.restore()
                if left_length < len(ruby):
                    text = ruby[left_length:]
                    cr.save()
                    lt.set_text(text, -1)
                    PangoCairo.update_layout(cr, lt)
                    w, h = lt.get_pixel_size()
                    x = 0
                    y = height + right.y - h
                    cr.move_to(x, y)
                    PangoCairo.show_layout(cr, lt)
                    cr.restore()

    def _draw_caret(self, cr, layout, current, y, offset):
        cr.save()
        st, we = layout.get_cursor_pos(len(current[:offset].encode()))
        self.caret.x, self.caret.y, self.caret.width, self.caret.height = \
            st.x / Pango.SCALE - 1, y + st.y / Pango.SCALE, st.width / Pango.SCALE + 2, st.height / Pango.SCALE
        cr.set_operator(cairo.Operator.DIFFERENCE)
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(self.caret.x, self.caret.y, self.caret.width, self.caret.height)
        cr.fill()
        self.im.set_cursor_location(self.caret)
        cr.restore()

    def reflow(self, line=-1, redraw=True):
        self.width = self.get_allocated_width()

        cursor = self.buffer.get_cursor()

        context = self.create_pango_context()
        layout = Pango.Layout(context)
        desc = self.get_font()
        layout.set_font_description(desc)
        layout.set_width(self.width * Pango.SCALE)
        layout.set_spacing(self.spacing * Pango.SCALE)

        paragraph = self.get_paragraph(line)
        if paragraph and self.heights:
            self.height -= self.heights[line]
            text = paragraph.get_plain_text()
            if line == cursor.get_line() and self._has_preedit():
                cursor_offset = cursor.get_plain_line_offset()
                text = text[:cursor_offset] + self.preedit[0] + text[cursor_offset:]
            layout.set_text(text, -1)
            w, h = layout.get_pixel_size()
            h += self.spacing
            self.heights[line] = h
            self.height += h
        else:
            self.heights.clear()
            self.height = self.spacing
            for paragraph in self.get_buffer().paragraphs:
                text = paragraph.get_plain_text()
                if line == cursor.get_line() and self._has_preedit():
                    cursor_offset = cursor.get_plain_line_offset()
                    text = text[:cursor_offset] + self.preedit[0] + text[cursor_offset:]
                layout.set_text(text, -1)
                w, h = layout.get_pixel_size()
                h += self.spacing
                self.heights.append(h)
                self.height += h

        if self._vadjustment:
            # TODO: Adjust _vadjustment value as well
            self._vadjustment.set_properties(
                lower=0,
                upper=self.height,
                page_size=self.get_allocated_height()
            )

        if redraw:
            self.queue_draw()

    def _check_sentences(self, text):
        if not self.highlight_sentences:
            return text
        markup = ''
        sentence = ''
        start = end = 0
        text_length = len(text)
        for i in range(text_length):
            c = text[i]
            if start == end:
                if c in "\t 　":
                    markup += c
                    start += 1
                    end = start
                    continue
            end = i + 1
            if c in "　 。．？！" or text_length <= end:
                if c in "　 ":
                    end -= 1
                else:
                    sentence += c
                count = end - start
                if SENTENCE_LONG < count:
                    markup += '<span background="light pink">' + sentence + '</span>'
                elif SENTENCE_SHORT < count:
                    markup += '<span background="light yellow">' + sentence + '</span>'
                else:
                    markup += sentence
                if c in "　 ":
                    markup += c
                start = end = i + 1
                sentence = ''
            else:
                sentence += self._escape(c)
        return markup

    def on_draw(self, wid, cr):
        if wid.get_allocated_width() != self.width:
            self.reflow(redraw=False)
        height = wid.get_allocated_height()

        cr.set_source_rgb(255, 255, 255)
        cr.rectangle(0, 0, self.width, height)
        cr.fill()
        cr.move_to(0, 0)
        cr.set_source_rgb(0, 0, 0)

        cursor = self.buffer.get_cursor()
        start, end = self.buffer.get_selection_bounds()

        layout = PangoCairo.create_layout(cr)
        desc = self.get_font()
        layout.set_font_description(desc)
        layout.set_width(self.width * Pango.SCALE)
        layout.set_spacing(self.spacing * Pango.SCALE)

        lineno = 0
        offset = self._get_offset()
        y = self.spacing - offset
        for paragraph in self.buffer.paragraphs:
            h = self.heights[lineno]
            if y < height and 0 <= y + h:
                text = paragraph.get_plain_text()
                cursor_offset = len(text)
                if lineno == cursor.get_line():
                    cursor_offset = cursor.get_plain_line_offset()
                    if self._has_preedit():
                        text = text[:cursor_offset] + self.preedit[0] + text[cursor_offset:]
                if start == end or lineno < start.get_line() or end.get_line() < lineno:
                    # Note set_text() does not reset the existing markups.
                    markup = self._check_sentences(text)
                    layout.set_markup(markup, -1)
                elif start.get_line() < lineno and lineno < end.get_line():
                    markup = self._escape(text)
                    markup = '<span background="#ACCEF7">' + markup + '</span>'
                    layout.set_markup(markup, -1)
                elif start.get_line() == end.get_line():
                    assert lineno == end.get_line()
                    so = start.get_plain_line_offset()
                    eo = end.get_plain_line_offset()
                    markup = self._escape(text[:so]) + \
                        '<span background="#ACCEF7">' + self._escape(text[so:eo]) + '</span>' + \
                        self._escape(text[eo:])
                    layout.set_markup(markup, -1)
                elif start.get_line() == lineno:
                    o = start.get_plain_line_offset()
                    markup = self._escape(text[:o]) + '<span background="#ACCEF7">' + self._escape(text[o:]) + '</span>'
                    layout.set_markup(markup, -1)
                elif lineno == end.get_line():
                    o = end.get_plain_line_offset()
                    markup = '<span background="#ACCEF7">' + self._escape(text[:o]) + '</span>' + self._escape(text[o:])
                    layout.set_markup(markup, -1)
                PangoCairo.update_layout(cr, layout)
                cr.move_to(0, y)
                PangoCairo.show_layout(cr, layout)
                self._draw_rubies(cr, layout, paragraph, text, y, cursor_offset)
                if lineno == cursor.get_line():
                    self._draw_caret(cr, layout, text, y, cursor_offset + self.preedit[2])
            y += h
            lineno += 1

        self.caret.y += offset

        if height != self.allocated_height:
            self.allocated_height = height
            if self._vadjustment:
                # TODO: Adjust _vadjustment value as well
                self._vadjustment.set_properties(
                    lower=0,
                    upper=self.height,
                    page_size=height
                )

    def on_focus_in(self, wid, event):
        print("on_focus_in")
        self.im.set_client_window(wid.get_window())
        self.im.focus_in()
        return True

    def on_focus_out(self, wid, event):
        print("on_focus_out")
        self.im.focus_out()
        return True

    def on_key_press(self, wid, event):
        is_selection = (event.state & Gdk.ModifierType.SHIFT_MASK)
        is_control = (event.state & Gdk.ModifierType.CONTROL_MASK)
        print("on_key_press:", Gdk.keyval_name(event.keyval), event.state)
        if self.im.filter_keypress(event):
            return True
        # Process shortcut keys firstly
        if is_control:
            if event.keyval == Gdk.KEY_A or event.keyval == Gdk.KEY_a:
                self.emit('select-all', True)
                return True
            elif event.keyval == Gdk.KEY_X or event.keyval == Gdk.KEY_x:
                self.emit('cut-clipboard')
                return True
            elif event.keyval == Gdk.KEY_C or event.keyval == Gdk.KEY_c:
                self.emit('copy-clipboard')
                return True
            elif event.keyval == Gdk.KEY_V or event.keyval == Gdk.KEY_v:
                self.emit('paste-clipboard')
                return True
        if event.keyval == Gdk.KEY_BackSpace:
            if self.buffer.delete_selection(True, True):
                return True
            end = self.buffer.get_cursor()
            start = end.copy()
            if start.backward_cursor_position():
                self.buffer.begin_user_action()
                self.buffer.delete(start, end)
                self.buffer.end_user_action()
                self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_Delete:
            if self.buffer.delete_selection(True, True):
                return True
            start = self.buffer.get_cursor()
            end = start.copy()
            if start.forward_cursor_position():
                self.buffer.begin_user_action()
                self.buffer.delete(start, end)
                self.buffer.end_user_action()
                self.buffer.place_cursor(start)
                self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_Return:
            self.buffer.begin_user_action()
            self.buffer.insert_at_cursor('\n')
            self.buffer.end_user_action()
            self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_Escape:
            cursor = self.buffer.get_cursor()
            self.buffer.place_cursor(cursor)
            self.queue_draw()
            return True
        elif event.keyval == Gdk.KEY_Left:
            cursor = self.buffer.get_cursor()
            if cursor.backward_cursor_position():
                self.buffer.move_cursor(cursor, is_selection)
                self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_Right:
            cursor = self.buffer.get_cursor()
            if cursor.forward_cursor_position():
                self.buffer.move_cursor(cursor, is_selection)
                self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_Up:
            y = self.caret.y - self.caret.height - self.spacing
            if 0 <= y:
                inside, cursor = self.get_iter_at_location(self.caret.x + 1, y)
                self.buffer.move_cursor(cursor, is_selection)
                self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_Down:
            y = self.caret.y + self.caret.height + self.spacing
            if y < self.height:
                inside, cursor = self.get_iter_at_location(self.caret.x + 1, y)
                self.buffer.move_cursor(cursor, is_selection)
                self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_Home:
            if is_control:
                cursor = self.buffer.get_start_iter()
            else:
                inside, cursor = self.get_iter_at_location(0, self.caret.y)
            if cursor != self.buffer.get_cursor():
                self.buffer.move_cursor(cursor, is_selection)
                self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_End:
            if is_control:
                cursor = self.buffer.get_end_iter()
            else:
                width = wid.get_allocated_width()
                inside, cursor = self.get_iter_at_location(width, self.caret.y)
            if cursor != self.buffer.get_cursor():
                self.buffer.move_cursor(cursor, is_selection)
                self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_Page_Up:
            y = self.caret.y - wid.get_allocated_height()
            inside, cursor = self.get_iter_at_location(self.caret.x + 1, y)
            self.buffer.move_cursor(cursor, is_selection)
            self.place_cursor_onscreen()
            return True
        elif event.keyval == Gdk.KEY_Page_Down:
            y = self.caret.y + wid.get_allocated_height()
            inside, cursor = self.get_iter_at_location(self.caret.x + 1, y)
            self.buffer.move_cursor(cursor, is_selection)
            self.place_cursor_onscreen()
            return True
        return False

    def on_key_release(self, wid, event):
        # print("on_key_release: '", Gdk.keyval_name(event.keyval), "', ", event.state, sep='')
        if self.im.filter_keypress(event):
            return True
        return False

    def on_commit(self, wid, str):
        self.buffer.begin_user_action()
        self.buffer.insert_at_cursor(str)
        self.buffer.end_user_action()
        self.place_cursor_onscreen()
        return True

    def on_retrieve_surrounding(self, wid):
        text, offset = self.buffer.get_surrounding()
        self.im.set_surrounding(text, len(text.encode()), len(text[:offset].encode()))
        return True

    def on_delete_surrounding(self, wid, offset, n_chars):
        self.buffer.begin_user_action()
        self.buffer.delete_surrounding(offset, n_chars)
        self.buffer.end_user_action()
        self.place_cursor_onscreen()
        return True

    def on_preedit_changed(self, wid):
        self.preedit = self.im.get_preedit_string()
        cursor = self.buffer.get_cursor()
        self.buffer.delete_selection(True, True)
        self.reflow(cursor.get_line())
        print('on_preedit_changed', self.preedit)

    def on_preedit_end(self, wid):
        self.preedit = self.im.get_preedit_string()
        self.buffer.delete_selection(True, True)
        print('on_preedit_end', self.preedit)

    def on_preedit_start(self, wid):
        self.preedit = self.im.get_preedit_string()
        self.buffer.delete_selection(True, True)
        print('on_preedit_start', self.preedit)

    def on_value_changed(self, *whatever):
        self.queue_draw()

    def on_inserted(self, textbuffer, iter, text):
        if has_newline(text):
            self.reflow()
        else:
            self.reflow(iter.get_line())
        self.queue_draw()

    def on_delete(self, textbuffer, start, end):
        if start.get_line() == end.get_line():
            self.reflow_line = start.get_line()
        else:
            self.reflow_line = -1

    def on_deleted(self, textbuffer, start, end):
        self.reflow(self.reflow_line)
        self.queue_draw()

    def on_mouse_move(self, wid, event):
        if (event.state & Gdk.ModifierType.BUTTON1_MASK):
            inside, cursor = self.get_iter_at_location(event.x, self._get_offset() + event.y)
            self.buffer.move_cursor(cursor, True)
            self.place_cursor_onscreen()
        return True

    def on_mouse_press(self, wid, event):
        if event.button == Gdk.BUTTON_PRIMARY:
            is_selection = (event.state & Gdk.ModifierType.SHIFT_MASK)
            inside, cursor = self.get_iter_at_location(event.x, self._get_offset() + event.y)
            self.buffer.move_cursor(cursor, is_selection)
            self.place_cursor_onscreen()
        return True

    def on_mouse_release(self, wid, event):
        return True

    def get_hadjustment(self):
        return self._hadjustment

    def get_vadjustment(self):
        return self._vadjustment

    def set_hadjustment(self, adjustment):
        if self._hadjustment:
            self._hadjustment.disconnect(self._hadjust_signal)
            self._hadjust_signal = None

        self._hadjustment = adjustment
        if adjustment:
            adjustment.set_properties(
                lower=0,
                upper=self.get_allocated_width(),
                page_size=self.get_allocated_width()
            )
            self._hadjust_signal = adjustment.connect(
                    "value-changed", self.on_value_changed
            )

    def set_vadjustment(self, adjustment):
        if self._vadjustment:
            self._vadjustment.disconnect(self._vadjust_signal)
            self._vadjust_signal = None

        self._vadjustment = adjustment
        if adjustment:
            adjustment.set_properties(
                lower=0,
                upper=self.height,
                page_size=self.get_allocated_height()
            )
            self._vadjust_signal = adjustment.connect(
                "value-changed", self.on_value_changed
            )

    def do_cut_clipboard(self):
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        self.buffer.cut_clipboard(clipboard, self.get_editable())
        self.place_cursor_onscreen()

    def do_copy_clipboard(self):
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        self.buffer.copy_clipboard(clipboard)

    def do_paste_clipboard(self):
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        text = clipboard.wait_for_text()
        if text is not None:
            self.buffer.begin_user_action()
            self.buffer.insert_at_cursor(text)
            self.buffer.end_user_action()

    def do_select_all(self, select):
        self.buffer.select_all()
        self.queue_draw()

    hadjustment = GObject.property(
        get_hadjustment, set_hadjustment, type=Gtk.Adjustment
    )
    vadjustment = GObject.property(
        get_vadjustment, set_vadjustment, type=Gtk.Adjustment
    )
    hscroll_policy = GObject.property(
        default=Gtk.ScrollablePolicy.NATURAL, type=Gtk.ScrollablePolicy
    )
    vscroll_policy = GObject.property(
        default=Gtk.ScrollablePolicy.NATURAL, type=Gtk.ScrollablePolicy
    )


class EditorWindow(Gtk.ApplicationWindow):

    def __init__(self, app, file=None):
        content = ""

        self.title = _("FuriganaPad")

        if file:
            try:
                [success, content, etags] = file.load_contents(None)
                content = content.decode("utf-8", "ignore")
            except GObject.GError as e:
                file = None
                print("Error: " + e.message)
        super().__init__(application=app)
        self.set_default_size(720, 400)

        grid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(grid)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.textview = TextView()

        scrolled_window.add(self.textview)
        grid.pack_start(scrolled_window, True, True, 0)

        self.searchbar = Gtk.SearchBar()
        # We use Gtk.Entry since Gtk.SearchEntry does not support IME
        # at this point.
        self.search_entry = Gtk.Entry()
        self.searchbar.add(self.search_entry)
        self.searchbar.connect_entry(self.search_entry)
        grid.pack_start(self.searchbar, False, False, 0)
        self.searchbar.set_search_mode(False)
        self.search_entry.connect("activate", self.on_find)

        self.replacebar = Gtk.SearchBar()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.replacebar.add(box)
        self.replace_from = Gtk.Entry()
        box.pack_start(self.replace_from, False, False, 1)
        self.replace_to = Gtk.Entry()
        box.pack_start(self.replace_to, False, False, 1)
        self.replacebar.connect_entry(self.replace_from)
        grid.pack_start(self.replacebar, False, False, 0)
        self.replacebar.set_search_mode(False)
        self.replace_from.connect("activate", self.on_find)
        self.replace_to.connect("activate", self.on_replace)

        self.rubybar = Gtk.SearchBar()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.rubybar.add(box)
        label = Gtk.Label(_("Ruby") + ": ")
        box.pack_start(label, False, False, 1)
        self.ruby_entry = Gtk.Entry()
        box.pack_start(self.ruby_entry, False, False, 1)
        self.rubybar.connect_entry(self.ruby_entry)
        grid.pack_start(self.rubybar, False, False, 0)
        self.rubybar.set_search_mode(False)
        self.ruby_entry.connect("activate", self.on_ruby)

        self.connect("key-press-event", self.on_key_press_event)

        self.buffer = self.textview.get_buffer()
        if content:
            self.buffer.set_text(content)
            self.buffer.set_modified(False)
            self.buffer.place_cursor(self.buffer.get_start_iter())

        actions = {
            "new": self.new_callback,
            "open": self.open_callback,
            "save": self.save_callback,
            "saveas": self.save_as_callback,
            "close": self.close_callback,
            "closeall": self.close_all_callback,
            "undo": self.undo_callback,
            "redo": self.redo_callback,
            "cut": self.cut_callback,
            "copy": self.copy_callback,
            "paste": self.paste_callback,
            "find": self.find_callback,
            "replace": self.replace_callback,
            "annotate": self.annotate_callback,
            "unconvert": self.unconvert_callback,
            "selectall": self.select_all_callback,
            "font": self.font_callback,
            "about": self.about_callback,
        }
        for name, method in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", method)
            self.add_action(action)
        self.connect("delete-event", self.on_delete_event)

        action = Gio.SimpleAction.new_stateful(
            "ruby", None, GLib.Variant.new_boolean(True))
        action.connect("activate", self.ruby_callback)
        self.add_action(action)

        self.highlightlongsentences_action = Gio.SimpleAction.new_stateful(
            "highlightlongsentences", None, GLib.Variant.new_boolean(True))
        self.highlightlongsentences_action.connect(
            "activate", self.highlightlongsentences_callback)
        self.add_action(self.highlightlongsentences_action)

        self.set_file(file)

    def on_key_press_event(self, wid, event):
        # Control focus around search bars by checking keys typed into the
        # main window
        if self.search_entry.is_focus():
            if event.keyval == Gdk.KEY_Escape:
                self.searchbar.set_search_mode(False)
                self.textview.grab_focus()
                return True
        elif self.replace_to.is_focus() or self.replace_from.is_focus():
            if event.keyval == Gdk.KEY_Tab or event.keyval == Gdk.KEY_ISO_Left_Tab:
                if self.replace_to.is_focus():
                    self.replacebar.connect_entry(self.replace_from)
                    self.replace_from.grab_focus()
                elif self.replace_from.is_focus():
                    self.replacebar.connect_entry(self.replace_to)
                    self.replace_to.grab_focus()
                return True
            if event.keyval == Gdk.KEY_Escape:
                self.replacebar.set_search_mode(False)
                self.textview.grab_focus()
                return True
        elif self.ruby_entry.is_focus():
            if event.keyval == Gdk.KEY_Escape:
                self.rubybar.set_search_mode(False)
                self.textview.grab_focus()
                return True
        return False

    def set_file(self, file):
        self.file = file
        if self.file:
            self.buffer.set_modified(False)
            self.set_title(file.get_basename() + " ― " + self.title)
            return False
        else:
            self.set_title(self.title)
            return True

    def is_opened(self, file):
        windows = self.get_application().get_windows()
        for window in windows:
            if window.file and window.file.equal(file):
                return window
        return None

    def new_callback(self, action, parameter):
        win = EditorWindow(self.get_application())
        win.show_all()

    def open_callback(self, action, parameter):
        open_dialog = Gtk.FileChooserDialog(
            _("Open File"), self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
        self.add_filters(open_dialog)
        open_dialog.set_local_only(False)
        open_dialog.set_modal(True)
        open_dialog.connect("response", self.open_response_cb)
        open_dialog.show()

    def open_response_cb(self, dialog, response):
        file = None
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
        dialog.destroy()
        # Open new window after closing dialog to raise the new window
        # in the stacking order.
        if file:
            win = self.is_opened(file)
            if win:
                win.present()
                return
            win = EditorWindow(self.get_application(), file=file)
            win.show_all()

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name(_("Text files"))
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        filter_py = Gtk.FileFilter()
        filter_py.set_name(_("Python files"))
        filter_py.add_mime_type("text/x-python")
        dialog.add_filter(filter_py)

        filter_any = Gtk.FileFilter()
        filter_any.set_name(_("Any files"))
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def save(self):
        [start, end] = self.buffer.get_bounds()
        current_contents = self.buffer.get_text(start, end, True)
        if current_contents:
            current_contents += '\n'
            try:
                current_contents = current_contents.encode()
                self.file.replace_contents(current_contents,
                                           None,
                                           False,
                                           Gio.FileCreateFlags.NONE,
                                           None)
            except GObject.GError as e:
                self.file = None
        else:
            try:
                self.file.replace_readwrite(None,
                                            False,
                                            Gio.FileCreateFlags.NONE,
                                            None)
            except GObject.GError as e:
                self.file = None
        return self.set_file(self.file)

    def save_as(self):
        dialog = Gtk.FileChooserDialog(
            _("Save File"), self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT))
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_modal(True)
        if self.file is not None:
            try:
                dialog.set_file(self.file)
            except GObject.GError as e:
                print("Error: " + e.message)
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.file = dialog.get_file()
            dialog.destroy()
            return self.save()
        dialog.destroy()
        return self.set_file(None)

    def confirm_save_changes(self):
        if not self.buffer.get_modified():
            return False
        dialog = Gtk.MessageDialog(
            self, 0, Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.NONE, _("Save changes to this document?"))
        dialog.format_secondary_text(
            _("If you don't, changes will be lost."))
        dialog.add_button(_("Close _Without Saving"), Gtk.ResponseType.NO)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.YES)
        dialog.set_default_response(Gtk.ResponseType.YES)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.NO:
            return False
        elif response == Gtk.ResponseType.YES:
            # Close the window after saving changes
            self.close_after_save = True
            if self.file is not None:
                return self.save()
            else:
                return self.save_as()
        else:
            return True

    def save_callback(self, action, parameter):
        if self.file is not None:
            self.save()
        else:
            self.save_as()

    def save_as_callback(self, action, parameter):
        self.save_as()

    def close_callback(self, action, parameter):
        if not self.confirm_save_changes():
            self.destroy()

    def close_all_callback(self, action, parameter):
        windows = self.get_application().get_windows()
        for window in windows:
            window.lookup_action("close").activate()

    def on_delete_event(self, wid, event):
        return self.confirm_save_changes()

    def undo_callback(self, action, parameter):
        self.buffer.emit('undo')

    def redo_callback(self, action, parameter):
        self.buffer.emit('redo')

    def cut_callback(self, action, parameter):
        self.textview.emit('cut-clipboard')

    def copy_callback(self, action, parameter):
        self.textview.emit('copy-clipboard')

    def paste_callback(self, action, parameter):
        self.textview.emit('paste-clipboard')

    def find_callback(self, action, parameter):
        self.searchbar.set_search_mode(True)

    def select_text(self, text):
        cursor_mark = self.buffer.get_insert()
        start = self.buffer.get_iter_at_mark(cursor_mark)
        selecton_mark = self.buffer.get_selection_bound()
        selected = self.buffer.get_iter_at_mark(selecton_mark)
        if start < selected:
            start = selected
        match = start.forward_search(text, 0, None)
        if match is None:
            start = self.buffer.get_start_iter()
            match = start.forward_search(text, 0, None)
        if match is not None:
            match_start, match_end = match
            self.buffer.select_range(match_start, match_end)
            self.textview.scroll_mark_onscreen(self.buffer.get_insert())
        return match

    def on_find(self, entry):
        self.select_text(entry.get_text())

    def replace_callback(self, action, parameter):
        self.replacebar.set_search_mode(True)

    def on_replace(self, entry):
        match = self.select_text(self.replace_from.get_text())
        if match is None:
            return
        self.buffer.begin_user_action()
        self.buffer.delete(match[0], match[1])
        text = self.replace_to.get_text()
        if text is not None:
            self.buffer.insert_at_cursor(text)
            cursor_mark = self.buffer.get_insert()
            end = self.buffer.get_iter_at_mark(cursor_mark)
            start = end.copy()
            start.backward_chars(len(text))
            self.textview.scroll_mark_onscreen(cursor_mark)
            self.buffer.select_range(start, end)
        self.buffer.end_user_action()

    def annotate_callback(self, action, parameter):
        if self.buffer.get_has_selection():
            self.rubybar.set_search_mode(True)

    def unconvert_callback(self, action, parameter):
        self.buffer.begin_user_action()
        self.buffer.unconvert(self.buffer.get_cursor())
        self.buffer.end_user_action()

    def on_ruby(self, entry):
        start, end = self.buffer.get_selection_bounds()
        if start == end:
            return
        if start.get_line() != end.get_line():
            return
        text = self.buffer.get_text(start, end, False)
        ruby = entry.get_text()
        # TODO: remove IAA, IAS, IAT from ruby
        self.buffer.begin_user_action()
        self.buffer.delete(start, end)
        if ruby:
            text = IAA + text + IAS + ruby + IAT
        self.buffer.insert_at_cursor(text)
        self.buffer.end_user_action()

    def select_all_callback(self, action, parameter):
        self.textview.emit('select-all', True)

    def font_callback(self, action, parameter):
        dialog = Gtk.FontChooserDialog(_("Font"), self)
        dialog.props.preview_text = _("The quick brown fox jumps over the lazy dog.")
        font_desc = self.textview.get_font()
        dialog.set_font_desc(font_desc)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            font = dialog.get_font()
            if font:
                desc = Pango.font_description_from_string(font)
                self.textview.set_font(desc)
        dialog.destroy()

    def ruby_callback(self, action, parameter):
        ruby = not action.get_state()
        action.set_state(GLib.Variant.new_boolean(ruby))
        self.buffer.set_ruby_mode(ruby)

    def highlightlongsentences_callback(self, action, parameter):
        highlight = not action.get_state()
        action.set_state(GLib.Variant.new_boolean(highlight))
        self.textview.set_check_sentences(highlight)

    def about_callback(self, action, parameter):
        dialog = Gtk.AboutDialog()
        dialog.set_transient_for(self)

        authors = ["Esrille Inc."]
        documenters = ["Esrille Inc."]

        dialog.set_program_name(self.title)
        dialog.set_copyright("Copyright 2019 Esrille Inc.")
        dialog.set_authors(authors)
        dialog.set_documenters(documenters)
        dialog.set_website("http://www.esrille.com/")
        dialog.set_website_label("Esrille Inc.")
        dialog.set_logo_icon_name("furiganapad")

        # To close the dialog when "close" is clicked, e.g. on RPi,
        # we connect the "response" signal to about_response_callback
        dialog.connect("response", self.about_response_callback)
        dialog.show()

    def about_response_callback(self, dialog, response):
        dialog.destroy()


class EditorApplication(Gtk.Application):

    uitexts = {}

    def __init__(self, resourcedir='', *args, **kwargs):
        super().__init__(*args,
                         flags=Gio.ApplicationFlags.HANDLES_OPEN,
                         **kwargs)

        if resourcedir:
            self.resourcedir = resourcedir
        else:
            self.resourcedir = os.path.join(os.path.dirname(sys.argv[0]), "../data")
        print(self.resourcedir)

        self.lang = locale.getdefaultlocale()[0]
        filename = os.path.join(self.resourcedir, "furiganapad." + self.lang + ".json")
        try:
            with open(filename, 'r') as file:
                EditorApplication.uitexts = json.load(file)
        except OSError as e:
            EditorApplication.uitexts = {}

    def do_activate(self):
        win = EditorWindow(self)
        win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        builder = Gtk.Builder()
        filename = os.path.join(self.resourcedir, "furiganapad.menu." + self.lang + ".ui")
        try:
            builder.add_from_file(filename)
        except GObject.GError as e:
            try:
                filename = os.path.join(self.resourcedir, "furiganapad.menu.ui")
                builder.add_from_file(filename)
            except GObject.GError as e:
                print("Error: " + e.message)
                sys.exit()
        self.set_menubar(builder.get_object("menubar"))

    def do_open(self, files, *hint):
        for file in files:
            win = EditorWindow(self, file=file)
            win.show_all()


# i18n
def _(string):
    if string in EditorApplication.uitexts:
        return EditorApplication.uitexts[string]
    return string


if __name__ == '__main__':
    app = EditorApplication()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
