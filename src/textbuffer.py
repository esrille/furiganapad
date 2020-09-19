#
# Copyright (c) 2019, 2020  Esrille Inc.
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

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import GObject

import logging
import time


logger = logging.getLogger(__name__)

IAA = '\uFFF9'  # IAA (INTERLINEAR ANNOTATION ANCHOR)
IAS = '\uFFFA'  # IAS (INTERLINEAR ANNOTATION SEPARATOR)
IAT = '\uFFFB'  # IAT (INTERLINEAR ANNOTATION TERMINATOR)

NEWLINES = "\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029"

HIRAGANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんゔがぎぐげござじずぜぞだぢづでどばびぶべぼぁぃぅぇぉゃゅょっぱぴぷぺぽゎゐゑ・ーゝゞ"
KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンヴガギグゲゴザジズゼゾダヂヅデドバビブベボァィゥェォャュョッパピプペポヮヰヱ・ーヽヾ"

PLAIN = 0
BASE = 1
RUBY = 2


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


def get_plain_text(s):
    mode = PLAIN
    plain = ''
    for c in s:
        if c == IAA:
            mode = BASE
        elif c == IAS:
            mode = RUBY
        elif c == IAT:
            mode = PLAIN
        elif mode != RUBY:
            plain += c
    return plain


def has_newline(s):
    for c in s:
        if c in NEWLINES:
            return True
    return False


def remove_dangling_annotations(s):
    t = ''
    i = 0
    mode = PLAIN
    for c in s:
        if c == IAA:
            if mode != PLAIN:
                continue
            break
        elif c == IAS:
            mode = RUBY
        elif c == IAT:
            if mode != RUBY:
                t = ''
            i = i + 1
            break
        elif mode == PLAIN:
            t += c
        i += 1
    mode = PLAIN
    s = s[i:]
    a = ''
    for c in s:
        if c == IAA:
            if mode != PLAIN:
                continue
            mode = BASE
            a += c
        elif c == IAS:
            if mode != BASE:
                continue
            mode = RUBY
            a += c
        elif c == IAT:
            if mode != RUBY:
                continue
            mode = PLAIN
            a += c
            t += a
            a = ''
        elif mode == PLAIN:
            t += c
        else:
            a += c
    if mode != PLAIN:
        t += remove_dangling_annotations(a[1:])
    return t


class Paragraph:
    def __init__(self, text=''):
        self.text = text
        self.plain = ''
        self.rubies = list()

    def _backward_cursor_position(self, offset):
        if offset <= 0:
            return -1
        mode = PLAIN
        for c in reversed(self.text[:offset]):
            offset -= 1
            if c == IAA:
                mode = PLAIN
            elif c == IAS:
                mode = BASE
            elif c == IAT:
                mode = RUBY
            elif mode == RUBY:
                pass
            else:
                if 0 < offset and self.text[offset - 1] == IAA:
                    offset -= 1
                return offset
        return -1

    def _expand_plain_offset(self, offset):
        mode = PLAIN
        i = 0
        length = 0
        for c in self.text:
            if length == offset:
                if i < len(self.text) and self.text[i] == IAS:
                    i = self.text.find(IAT, i + 1) + 1
                break
            if c == IAA:
                mode = BASE
            elif c == IAS:
                mode = RUBY
            elif c == IAT:
                mode = PLAIN
            elif mode == RUBY:
                pass
            else:
                length += 1
            i += 1
        return i

    def _forward_cursor_position(self, offset):
        if len(self.text) <= offset:
            return len(self.text) + 1
        mode = PLAIN
        if self.text[offset] == IAA:
            offset += 1
        offset += 1
        for c in self.text[offset:]:
            if c == IAA:
                return offset
            elif c == IAS:
                mode = RUBY
            elif c == IAT:
                mode = PLAIN
            elif mode == RUBY:
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

    def _get_plain_offset(self, offset):
        mode = PLAIN
        i = 0
        len = 0
        for c in self.text:
            if i == offset:
                break
            if c == IAA:
                mode = BASE
            elif c == IAS:
                mode = RUBY
            elif c == IAT:
                mode = PLAIN
            elif mode == RUBY:
                pass
            else:
                len += 1
            i += 1
        return len

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

    def get_length(self):
        # plus one as a newline at the end of the line
        return len(self.text) + 1

    def get_plain_length(self):
        # plus one as a newline at the end of the line
        return len(self.get_plain_text()) + 1

    def get_plain_text(self):
        if self.plain:
            return self.plain
        mode = PLAIN
        i = pos = len = 0
        ruby = ''
        for c in self.text:
            if c == IAA:
                mode = BASE
                pos = i
            elif c == IAS:
                mode = RUBY
                len = i - pos
            elif c == IAT:
                mode = PLAIN
                self.rubies.append([pos, len, ruby])
                ruby = ''
            elif mode == RUBY:
                ruby += c
            else:
                self.plain += c
                i += 1
        return self.plain

    def get_text(self):
        return self.text

    def insert(self, offset, text):
        assert offset <= len(self.text)
        self.set_text(self.text[:offset] + text + self.text[offset:])

    def set_text(self, text):
        self.text = text
        self.plain = ''
        self.rubies.clear()

    def split(self, offset):
        assert offset <= len(self.text)
        next = Paragraph(self.text[offset:])
        self.set_text(self.text[:offset])
        return next


class TextIter:

    def __init__(self, buffer, line=0, offset=0):
        self.buffer = buffer
        self.line = line
        self.offset = offset

    def __eq__(self, other):
        return self.line == other.line and self.offset == other.offset

    def __ge__(self, other):
        return not self.__lt__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __le__(self, other):
        if self.line < other.line:
            return True
        if other.line < self.line:
            return False
        return self.offset <= other.offset

    def __lt__(self, other):
        if self.line < other.line:
            return True
        if other.line < self.line:
            return False
        return self.offset < other.offset

    def __ne__(self, other):
        return not self.__eq__(other)

    def assign(self, other):
        self.buffer = other.buffer
        self.line = other.line
        self.offset = other.offset

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

    def copy(self):
        return TextIter(self.buffer, self.line, self.offset)

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


class TextBuffer(GObject.Object):

    __gsignals__ = {
        'begin_user_action': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'delete_range': (GObject.SIGNAL_RUN_LAST, None, (object, object, )),
        'end_user_action': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'insert_text': (GObject.SIGNAL_RUN_LAST, None, (object, str, )),
        'modified-changed': (GObject.SIGNAL_RUN_LAST, None, ()),
        'redo': (GObject.SIGNAL_RUN_LAST, None, ()),
        'undo': (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self):
        super().__init__()
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

    def _annotate(self, s, r):
        if is_kana(s):
            return s
        pos = r.find('―')
        if 0 <= pos:
            r = r[:pos] + r[pos + 1:]
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
            if i < len(r) and to_hiragana(s[-1 - i]) == r[-1 - i]:
                after = s[-1 - i] + after
            else:
                break
        if after:
            s = s[:-len(after)]
            r = r[:-len(after)]
        if s and r:
            s = IAA + s + IAS + r + IAT
        return before + s + after

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

    def empty(self):
        if 1 < self.get_line_count():
            return False
        return self.paragraphs[0].get_length() == 1

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
        text = remove_dangling_annotations(text)
        clipboard.set_text(text, -1)

    def create_mark(self, mark_name, where):
        self.marks[mark_name] = TextMark(where)

    def cut_clipboard(self, clipboard, default_editable):
        start, end = self.get_selection_bounds()
        if start == end:
            return
        text = self.get_text(start, end, True)
        text = remove_dangling_annotations(text)
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
            self.annotated = text[offset + 1:pos]
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
            logger.info('よみ: %s', self.reading)
        self.surround_deleted = True
        self.delete(start, end)

    def do_delete_range(self, start, end):
        if start.get_line() == end.get_line():
            text = self.paragraphs[start.get_line()].get_text()
            text = text[:start.get_line_offset()] + text[end.get_line_offset():]
            self.paragraphs[start.get_line()].set_text(text)
            end.set_line_offset(start.get_line_offset())
        else:
            lineno = end.get_line()
            if start.get_line() + 1 < lineno:
                del self.paragraphs[start.get_line() + 1:lineno]
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

    def do_insert_text(self, iter, text):
        assert 0 < len(text)
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

    def do_redo(self):
        if not self.redo:
            return
        was_modified = self.get_modified()
        logger.info("do_redo")
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
                    logger.info("do_redo: %s", action)
                    start = self.get_iter_at_line_offset(action[1], action[2])
                    self.insert(start, action[5])
        self.place_cursor(start)
        self.undo.append(action)
        if not was_modified:
            self.emit('modified-changed')

    def do_undo(self):
        if not self.get_modified():
            return
        logger.info("do_undo")
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
                    logger.info("do_undo: %s", action)
                    start = self.get_iter_at_line_offset(action[1], action[2])
                    self.insert(start, action[5])
        elif action[0] == "delete_range":
            start = self.get_iter_at_line_offset(action[1], action[2])
            self.insert(start, action[5])
        self.place_cursor(start)
        self.redo.append(action)
        if not self.get_modified():
            self.emit('modified-changed')

    def end_user_action(self):
        self.emit('end_user_action')
        self.user_action = False

    def get_anchor(self):
        return self.get_selection_bound().iter.copy()

    def get_bounds(self):
        start = self.get_start_iter()
        end = self.get_end_iter()
        return start, end

    def get_cursor(self):
        return self.get_insert().iter.copy()

    def get_end_iter(self):
        lineno = self.get_line_count() - 1
        return TextIter(self, lineno, self.paragraphs[lineno].get_length() - 1)

    def get_has_selection(self):
        return self.get_selection_bound().iter != self.get_insert().iter

    def get_insert(self):
        return self.marks["insert"]

    def get_iter_at_line_offset(self, line_number, char_offset):
        assert line_number < self.get_line_count()
        assert char_offset < self.paragraphs[line_number].get_length()
        return TextIter(self, line_number, char_offset)

    def get_iter_at_mark(self, mark):
        return mark.iter.copy()

    def get_line_count(self):
        return len(self.paragraphs)

    def get_modified(self):
        return 0 < len(self.undo)

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

    def get_surrounding(self):
        cursor = self.get_cursor()
        return self.paragraphs[cursor.get_line()].get_text(), cursor.get_line_offset()

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

    def insert(self, iter, text):
        if not text:
            self.surround_deleted = False
            return
        if self.empty():
            if text.endswith('\r\n'):
                text = text[:-2]
            elif text[-1] in NEWLINES:
                text = text[:-1]
        if self.surround_deleted and self.ruby_mode and not iter.inside_ruby():
            text = self._annotate(text, self.reading)
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

    def on_delete(self, textbuffer, start, end):
        if self.user_action:
            was_modified = self.get_modified()
            text = self.get_text(start, end, True)
            action = ["delete_range",
                      start.get_line(), start.get_line_offset(),
                      end.get_line(), end.get_line_offset(),
                      text,
                      time.perf_counter()]
            logger.info("on_delete: %s", action)
            self.undo.append(action)
            self.redo.clear()
            if not was_modified:
                self.emit('modified-changed')

    def on_insert(self, textbuffer, iter, text):
        if self.user_action:
            self.inserting = iter.copy()

    def on_inserted(self, textbuffer, iter, text):
        if self.user_action:
            was_modified = self.get_modified()
            action = ["insert_text",
                      self.inserting.get_line(), self.inserting.get_line_offset(),
                      iter.get_line(), iter.get_line_offset(),
                      text,
                      time.perf_counter()]
            logger.info("on_inserted: %s", action)
            self.undo.append(action)
            self.redo.clear()
            self.inserting = None
            if not was_modified:
                self.emit('modified-changed')

    def place_cursor(self, where):
        self.select_range(where, where)

    def select_all(self):
        start, end = self.get_bounds()
        self.select_range(start, end)

    def select_range(self, ins, bound):
        self.move_mark(self.get_insert(), ins)
        self.move_mark(self.get_selection_bound(), bound)

    def set_modified(self, modified):
        current = self.get_modified()
        if current and not modified:
            self.undo = []
            self.redo = []
        if current != self.get_modified():
            self.emit('modified-changed')
        return self.get_modified()

    def set_ruby_mode(self, ruby):
        self.ruby_mode = ruby

    def set_text(self, text):
        start, end = self.get_bounds()
        self.delete(start, end)
        self.insert(start, text)
        iter = self.get_start_iter()
        self.place_cursor(iter)

    def unconvert(self, iter):
        text = self.paragraphs[iter.get_line()].get_text()
        pos = iter.get_line_offset()
        if pos < 5 or text[pos - 1] != IAT:
            return False
        mode = IAT
        ruby = ''
        size = 1
        for c in reversed(text[:pos - 1]):
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
