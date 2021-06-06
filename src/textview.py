#
# Copyright (c) 2019-2021  Esrille Inc.
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
from gi.repository import Gtk, Gdk, GObject, Pango, PangoCairo

from textbuffer import FuriganaBuffer, has_newline, remove_dangling_annotations

import cairo
import logging
import math

logger = logging.getLogger(__name__)

# A sentence with more than SENTENCE_SHORT characters is not short.
SENTENCE_SHORT = 50
# A sentence with more than SENTENCE_LONG characters is long.
SENTENCE_LONG = 60

DEFAULT_FONT = "Noto Sans Mono CJK JP 18px"
RUBY_DIV = 2.75

ESCAPE = str.maketrans({
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;'
})


class FuriganaView(Gtk.DrawingArea, Gtk.Scrollable):
    __gsignals__ = {
        'backspace': (GObject.SIGNAL_ACTION | GObject.SIGNAL_RUN_LAST, None, ()),
        'cut-clipboard': (GObject.SIGNAL_ACTION | GObject.SIGNAL_RUN_LAST, None, ()),
        'copy-clipboard': (GObject.SIGNAL_ACTION | GObject.SIGNAL_RUN_LAST, None, ()),
        'delete-from-cursor': (GObject.SIGNAL_ACTION | GObject.SIGNAL_RUN_LAST, None, (Gtk.DeleteType, int,)),
        'move-cursor': (GObject.SIGNAL_ACTION | GObject.SIGNAL_RUN_LAST, None, (Gtk.MovementStep, int, bool,)),
        'paste-clipboard': (GObject.SIGNAL_ACTION | GObject.SIGNAL_RUN_FIRST, None, ()),
        'redo': (GObject.SIGNAL_ACTION | GObject.SIGNAL_RUN_LAST, None, ()),
        'select-all': (GObject.SIGNAL_ACTION | GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'undo': (GObject.SIGNAL_ACTION | GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._init_scrollable()
        self._init_immultiontext()

        self.buffer = FuriganaBuffer()
        self.width = 1
        self.height = 0
        self.caret = Gdk.Rectangle()
        self.heights = list()
        self.highlight_sentences = True
        self.reflow_line = -1  # line number to reflow after "delete_range"; -1 to reflow every line

        style = self.get_style_context()
        self.padding = style.get_padding(Gtk.StateFlags.NORMAL)

        self.buffer.connect_after("insert_text", self.on_inserted)
        self.buffer.connect("delete_range", self.on_delete)
        self.buffer.connect_after("delete_range", self.on_deleted)

        self.connect('configure-event', self.on_configure)
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

        logger.debug("Pango.version: %d", Pango.version())
        desc = Pango.font_description_from_string(DEFAULT_FONT)
        self.set_font(desc)

    def _draw_caret(self, cr, layout, current, y, offset):
        cr.save()
        st, we = layout.get_cursor_pos(len(current[:offset].encode()))
        self.caret.x, self.caret.y, self.caret.width, self.caret.height = \
            st.x / Pango.SCALE - 1, y + st.y / Pango.SCALE, st.width / Pango.SCALE + 2, st.height / Pango.SCALE
        if (1, 13) <= cairo.version_info:
            cr.set_operator(cairo.Operator.DIFFERENCE)
            cr.set_source_rgb(1, 1, 1)
        cr.rectangle(self.caret.x, self.caret.y, self.caret.width, self.caret.height)
        cr.fill()
        im_caret = Gdk.Rectangle()
        im_caret.x, im_caret.y, im_caret.width, im_caret.height = \
            self.padding.left + self.caret.x, self.caret.y, self.caret.width, self.caret.height
        self.im.set_cursor_location(im_caret)
        cr.restore()

    def _draw_rubies(self, cr, layout, paragraph, plain, height, cursor_offset, current_line):
        lt = PangoCairo.create_layout(cr)
        desc = self.get_font().copy_static()
        size = desc.get_size()
        desc.set_size(size // RUBY_DIV)
        lt.set_font_description(desc)
        for pos, length, ruby in paragraph.rubies:
            if current_line and self._has_preedit() and cursor_offset - self.preedit[2] <= pos:
                pos += len(self.preedit[0])
            text = plain[:pos]
            left = layout.index_to_pos(len(text.encode()))
            text = plain[:pos + length - 1]
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

    def _get_offset(self):
        return self._vadjustment.get_value() if self._vadjustment else 0

    def _has_preedit(self):
        return self.preedit[0]

    def _init_immultiontext(self):
        self.im = Gtk.IMMulticontext()
        self.im.connect("commit", self.on_commit)
        self.im.connect("delete-surrounding", self.on_delete_surrounding)
        self.im.connect("retrieve-surrounding", self.on_retrieve_surrounding)
        self.im.connect("preedit-changed", self.on_preedit_changed)
        self.im.connect("preedit-end", self.on_preedit_end)
        self.im.connect("preedit-start", self.on_preedit_start)
        self.preedit = ('', None, 0)

    def _init_scrollable(self):
        self._hadjustment = self._vadjustment = None
        self._hadjust_signal = self._vadjust_signal = None

    def do_backspace(self):
        if self.buffer.delete_selection(True, True):
            self.place_cursor_onscreen()
            return
        end = self.buffer.get_cursor()
        start = end.copy()
        if start.backward_cursor_position():
            self.buffer.begin_user_action()
            self.buffer.delete(start, end)
            self.buffer.end_user_action()
            self.place_cursor_onscreen()

    def do_copy_clipboard(self):
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        self.buffer.copy_clipboard(clipboard)

    def do_cut_clipboard(self):
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        self.buffer.cut_clipboard(clipboard, self.get_editable())
        self.place_cursor_onscreen()

    def do_delete_from_cursor(self, type, count):
        if type == Gtk.DeleteType.CHARS:
            if self.buffer.delete_selection(True, True):
                self.place_cursor_onscreen()
                return
            start = self.buffer.get_cursor()
            end = start.copy()
            if start.forward_cursor_position():
                self.buffer.begin_user_action()
                self.buffer.delete(start, end)
                self.buffer.end_user_action()
                self.buffer.place_cursor(start)
                self.place_cursor_onscreen()

    def do_move_cursor(self, step, count, extend_selection):
        logger.debug("do_move_cursor(%d, %d, %d)", int(step), count, extend_selection)
        if step == Gtk.MovementStep.LOGICAL_POSITIONS:
            cursor = self.buffer.get_cursor()
            if count < 0:  # Left
                if cursor.backward_cursor_positions(-count):
                    self.buffer.move_cursor(cursor, extend_selection)
            elif 0 < count:  # Right
                if cursor.forward_cursor_positions(count):
                    self.buffer.move_cursor(cursor, extend_selection)
        elif step == Gtk.MovementStep.WORDS:
            cursor = self.buffer.get_cursor()
            if count < 0:  # Left
                if cursor.backward_visible_word_starts(-count):
                    self.buffer.move_cursor(cursor, extend_selection)
            elif 0 < count:  # Right
                if cursor.forward_visible_word_ends(count):
                    self.buffer.move_cursor(cursor, extend_selection)
        elif step == Gtk.MovementStep.DISPLAY_LINES:
            if count < 0:  # Up
                y = self.caret.y - self.line_height
                if 0 <= y:
                    inside, cursor = self.get_iter_at_location(self.caret.x + 1, y)
                    self.buffer.move_cursor(cursor, extend_selection)
            elif 0 < count:  # Down
                y = self.caret.y + self.line_height
                if y < self.height:
                    inside, cursor = self.get_iter_at_location(self.caret.x + 1, y)
                    self.buffer.move_cursor(cursor, extend_selection)
        elif step == Gtk.MovementStep.PARAGRAPH_ENDS:
            if count < 0:  # Home
                inside, cursor = self.get_iter_at_location(0, self.caret.y)
                if cursor != self.buffer.get_cursor():
                    self.buffer.move_cursor(cursor, extend_selection)
            elif 0 < count:  # End
                inside, cursor = self.get_iter_at_location(self.width, self.caret.y)
                if cursor != self.buffer.get_cursor():
                    self.buffer.move_cursor(cursor, extend_selection)
        elif step == Gtk.MovementStep.PAGES:
            if not self._vadjustment:
                return
            offset = self._vadjustment.get_value()
            height = self.get_allocated_height()
            y = self.caret.y
            if count < 0:  # Page_Up
                offset -= height
                if offset < 0:
                    return self.do_move_cursor(Gtk.MovementStep.BUFFER_ENDS, -1, extend_selection)
                y -= height
            elif 0 < count:  # Page_Down
                offset += height
                upper = self._vadjustment.get_upper()
                if upper <= offset:
                    return self.do_move_cursor(Gtk.MovementStep.BUFFER_ENDS, 1, extend_selection)
                y += height
            self._vadjustment.set_value(offset)
            inside, cursor = self.get_iter_at_location(self.caret.x + 1, y)
            self.buffer.move_cursor(cursor, extend_selection)
        elif step == Gtk.MovementStep.BUFFER_ENDS:
            if count < 0:  # Control-Home
                cursor = self.buffer.get_start_iter()
                if cursor != self.buffer.get_cursor():
                    self.buffer.move_cursor(cursor, extend_selection)
            elif 0 < count:  # Control-End
                cursor = self.buffer.get_end_iter()
                if cursor != self.buffer.get_cursor():
                    self.buffer.move_cursor(cursor, extend_selection)
        self.place_cursor_onscreen()

    def do_paste_clipboard(self):
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        text = clipboard.wait_for_text()
        text = remove_dangling_annotations(text)
        if text is not None:
            self.buffer.begin_user_action()
            self.buffer.insert_at_cursor(text)
            self.buffer.end_user_action()
            self.place_cursor_onscreen()

    def do_redo(self):
        self.buffer.emit('redo')
        self.place_cursor_onscreen()

    def do_select_all(self, select):
        if select:
            self.buffer.select_all()
        else:
            cursor = self.buffer.get_cursor()
            self.buffer.place_cursor(cursor)
        self.queue_draw()

    def do_undo(self):
        self.im.reset()
        self.buffer.emit('undo')
        self.place_cursor_onscreen()

    def get_buffer(self):
        return self.buffer

    def get_check_sentences(self):
        return self.highlight_sentences

    def get_editable(self):
        return True

    def get_font(self):
        return self.font_desc

    def get_hadjustment(self):
        return self._hadjustment

    def get_iter_at_location(self, x, y):
        cursor = self.buffer.get_cursor()
        height = 0
        i = 0
        for h in self.heights:
            if y < h + height:
                context = self.create_pango_context()
                layout = Pango.Layout(context)
                desc = self.get_font()
                layout.set_font_description(desc)
                layout.set_width(self.width * Pango.SCALE)
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
                iter = self.buffer.get_iter_at_line_offset(i, offset)
                return inside, iter
            height += h
            i += 1
        return False, self.buffer.get_end_iter()

    def get_paragraph(self, line):
        if 0 <= line < self.get_buffer().get_line_count():
            return self.get_buffer().paragraphs[line]
        return None

    def get_vadjustment(self):
        return self._vadjustment

    def on_commit(self, im, text):
        self.buffer.begin_user_action()
        self.buffer.insert_at_cursor(text)
        self.buffer.end_user_action()
        self.place_cursor_onscreen()
        return True

    def on_configure(self, wid, event):
        if self._vadjustment:
            self._vadjustment.set_page_size(self.get_allocated_height())
            self.reflow()
            self.place_cursor_onscreen()
        return True

    def on_delete(self, textbuffer, start, end):
        if start.get_line() == end.get_line():
            self.reflow_line = start.get_line()
        else:
            self.reflow_line = -1

    def on_delete_surrounding(self, im, offset, n_chars):
        self.buffer.begin_user_action()
        self.buffer.delete_surrounding(offset, n_chars)
        self.buffer.end_user_action()
        self.place_cursor_onscreen()
        return True

    def on_deleted(self, textbuffer, start, end):
        self.reflow(self.reflow_line)

    if Pango.version_check(1, 44, 0) is None:

        def _check_sentences(self, text, attr_list):
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
                    if SENTENCE_SHORT < count:
                        if SENTENCE_LONG < count:
                            attr = Pango.attr_background_new(0xffff, 0xa000, 0xa000)
                        else:
                            attr = Pango.attr_background_new(0xffff, 0xffff, 0xa000)
                        attr.start_index = len(markup.encode())
                        attr.end_index = attr.start_index + len(sentence.encode())
                        attr_list.insert(attr)
                    markup += sentence
                    if c in "　 ":
                        markup += c
                    start = end = i + 1
                    sentence = ''
                else:
                    sentence += c
            return markup

        def on_draw(self, wid, cr):
            cr.set_source_rgb(1, 1, 1)
            cr.paint()
            cr.move_to(0, 0)
            cr.set_source_rgb(0, 0, 0)
            cr.translate(self.padding.left, 0)

            height = wid.get_allocated_height()
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
                    attr_list = Pango.AttrList().new()
                    if lineno == cursor.get_line():
                        cursor_offset = cursor.get_plain_line_offset()
                        if self._has_preedit():
                            text = text[:cursor_offset] + self.preedit[0] + text[cursor_offset:]
                            attr_list.splice(self.preedit[1], len(text[:cursor_offset].encode()),
                                             len(self.preedit[0].encode()))
                            cursor_offset += self.preedit[2]
                    if start == end or lineno < start.get_line() or end.get_line() < lineno:
                        text = self._check_sentences(text, attr_list)
                    else:
                        attr = Pango.attr_background_new(0xac00, 0xce00, 0xf700)
                        if start.get_line() < lineno < end.get_line():
                            attr.start_index = 0
                            attr.end_index = len(text.encode())
                        elif start.get_line() == end.get_line():
                            assert lineno == end.get_line()
                            so = start.get_plain_line_offset()
                            eo = end.get_plain_line_offset()
                            attr.start_index = len(text[:so].encode())
                            attr.end_index = attr.start_index + len(text[so:eo].encode())
                        elif start.get_line() == lineno:
                            o = start.get_plain_line_offset()
                            attr.start_index = len(text[:o].encode())
                            attr.end_index = attr.start_index + len(text[o:].encode())
                        else:
                            assert lineno == end.get_line()
                            o = end.get_plain_line_offset()
                            attr.start_index = 0
                            attr.end_index = len(text[:o].encode())
                        attr_list.insert(attr)
                    layout.set_text(text, -1)
                    layout.set_attributes(attr_list)
                    PangoCairo.update_layout(cr, layout)
                    cr.move_to(0, y)
                    PangoCairo.show_layout(cr, layout)
                    if lineno == cursor.get_line():
                        self._draw_rubies(cr, layout, paragraph, text, y, cursor_offset, True)
                        self._draw_caret(cr, layout, text, y, cursor_offset)
                    else:
                        self._draw_rubies(cr, layout, paragraph, text, y, cursor_offset, False)
                y += h
                lineno += 1

            self.caret.y += offset
            return True

    else:

        def _check_sentences(self, text):
            if not self.highlight_sentences:
                return text.translate(ESCAPE)
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
                    sentence = sentence.translate(ESCAPE)
                    if SENTENCE_LONG < count:
                        markup += '<span background="#faa">' + sentence + '</span>'
                    elif SENTENCE_SHORT < count:
                        markup += '<span background="#ffa">' + sentence + '</span>'
                    else:
                        markup += sentence
                    if c in "　 ":
                        markup += c
                    start = end = i + 1
                    sentence = ''
                else:
                    sentence += c
            return markup

        def on_draw(self, wid, cr):
            cr.set_source_rgb(1, 1, 1)
            cr.paint()
            cr.move_to(0, 0)
            cr.set_source_rgb(0, 0, 0)
            cr.translate(self.padding.left, 0)

            height = wid.get_allocated_height()
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
                    attr_list_preedit = Pango.AttrList().new()
                    if lineno == cursor.get_line():
                        cursor_offset = cursor.get_plain_line_offset()
                        if self._has_preedit():
                            text = text[:cursor_offset] + self.preedit[0] + text[cursor_offset:]
                            attr_list_preedit.splice(self.preedit[1], len(text[:cursor_offset].encode()),
                                                     len(self.preedit[0].encode()))
                            cursor_offset += self.preedit[2]
                    if start == end or lineno < start.get_line() or end.get_line() < lineno:
                        markup = self._check_sentences(text)
                    elif start.get_line() < lineno < end.get_line():
                        markup = '<span background="#ACCEF7">' + text.translate(ESCAPE) + '</span>'
                    elif start.get_line() == end.get_line():
                        assert lineno == end.get_line()
                        so = start.get_plain_line_offset()
                        eo = end.get_plain_line_offset()
                        markup = text[:so].translate(ESCAPE) + \
                                 '<span background="#ACCEF7">' + text[so:eo].translate(ESCAPE) + '</span>' + \
                                 text[eo:].translate(ESCAPE)
                    elif start.get_line() == lineno:
                        o = start.get_plain_line_offset()
                        markup = text[:o].translate(ESCAPE) + \
                                 '<span background="#ACCEF7">' + text[o:].translate(ESCAPE) + '</span>'
                    else:
                        assert lineno == end.get_line()
                        o = end.get_plain_line_offset()
                        markup = '<span background="#ACCEF7">' + text[:o].translate(ESCAPE) + '</span>' + \
                                 text[o:].translate(ESCAPE)
                    layout.set_markup(markup, -1)
                    if lineno == cursor.get_line() and self._has_preedit():
                        attr_list = layout.get_attributes()
                        attr_list.splice(attr_list_preedit, 0, 0)
                        layout.set_attributes(attr_list)
                    PangoCairo.update_layout(cr, layout)
                    cr.move_to(0, y)
                    PangoCairo.show_layout(cr, layout)
                    if lineno == cursor.get_line():
                        self._draw_rubies(cr, layout, paragraph, text, y, cursor_offset, True)
                        self._draw_caret(cr, layout, text, y, cursor_offset)
                    else:
                        self._draw_rubies(cr, layout, paragraph, text, y, cursor_offset, False)
                y += h
                lineno += 1

            self.caret.y += offset
            return True

    def on_focus_in(self, wid, event):
        logger.debug("on_focus_in")
        self.im.set_client_window(wid.get_window())
        self.im.focus_in()
        return True

    def on_focus_out(self, wid, event):
        logger.debug("on_focus_out")
        self.im.focus_out()
        return True

    def on_inserted(self, textbuffer, iter, text):
        if has_newline(text):
            self.reflow()
        else:
            self.reflow(iter.get_line())

    def on_key_press(self, wid, event):
        logger.debug("on_key_press: '%s', %08x", Gdk.keyval_name(event.keyval), event.state)
        if self.im.filter_keypress(event):
            return True
        if event.keyval == Gdk.KEY_Return:
            self.buffer.begin_user_action()
            self.buffer.insert_at_cursor('\n')
            self.buffer.end_user_action()
            self.place_cursor_onscreen()
            return True
        return False

    def on_key_release(self, wid, event):
        if self.im.filter_keypress(event):
            return True
        return False

    def on_mouse_move(self, wid, event):
        if (event.state & Gdk.ModifierType.BUTTON1_MASK):
            inside, cursor = self.get_iter_at_location(event.x - self.padding.left, self._get_offset() + event.y)
            self.buffer.move_cursor(cursor, True)
            self.place_cursor_onscreen()
        return True

    def on_mouse_press(self, wid, event):
        self.im.reset()
        if event.button == Gdk.BUTTON_PRIMARY:
            is_selection = (event.state & Gdk.ModifierType.SHIFT_MASK)
            inside, cursor = self.get_iter_at_location(event.x - self.padding.left, self._get_offset() + event.y)
            self.buffer.move_cursor(cursor, is_selection)
            self.place_cursor_onscreen()
        return True

    def on_mouse_release(self, wid, event):
        return True

    def on_preedit_changed(self, im):
        self.preedit = self.im.get_preedit_string()
        cursor = self.buffer.get_cursor()
        self.buffer.delete_selection(True, True)
        self.reflow(cursor.get_line())
        logger.debug('on_preedit_changed: "%s" %d', self.preedit[0], self.preedit[2])

    def on_preedit_end(self, im):
        self.preedit = self.im.get_preedit_string()
        self.buffer.delete_selection(True, True)
        logger.debug('on_preedit_end: "%s" %d', self.preedit[0], self.preedit[2])

    def on_preedit_start(self, im):
        self.preedit = self.im.get_preedit_string()
        self.buffer.delete_selection(True, True)
        logger.debug('on_preedit_start: "%s" %d', self.preedit[0], self.preedit[2])

    def on_retrieve_surrounding(self, im):
        text, offset = self.buffer.get_surrounding()
        self.im.set_surrounding(text, len(text.encode()), len(text[:offset].encode()))
        return True

    def on_value_changed(self, *whatever):
        self.queue_draw()

    def place_cursor_onscreen(self):
        self.scroll_mark_onscreen(self.buffer.get_insert())

    def reflow(self, line=-1, redraw=True):
        self.width = max(1, self.get_allocated_width() - self.padding.left - self.padding.right)

        cursor = self.buffer.get_cursor()

        context = self.create_pango_context()
        layout = Pango.Layout(context)
        desc = self.get_font()
        layout.set_font_description(desc)
        layout.set_width(self.width * Pango.SCALE)
        layout.set_spacing(self.spacing * Pango.SCALE)

        prev_height = self.height
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
            allocated = self.get_allocated_height()
            upper = allocated if self.height < allocated else self.height
            self._vadjustment.set_upper(upper)

        if redraw:
            self.queue_draw()

    def scroll_mark_onscreen(self, mark):
        if not self._vadjustment:
            return

        height = self.get_allocated_height()
        offset = self._vadjustment.get_value()

        y = 0
        line = mark.iter.get_line()
        for i in range(line):
            y += self.heights[i]

        context = self.create_pango_context()
        layout = Pango.Layout(context)
        desc = self.get_font()
        layout.set_font_description(desc)
        layout.set_width(self.width * Pango.SCALE)
        layout.set_spacing(self.spacing * Pango.SCALE)
        text = self.buffer.paragraphs[line].get_plain_text()
        layout.set_text(text, -1)

        current = text[:mark.iter.get_plain_line_offset()]
        pos = layout.index_to_pos(len(current.encode()))
        y += pos.y / Pango.SCALE

        upper = self._vadjustment.get_upper()
        if offset <= y and y + self.line_height <= offset + height <= upper:
            self.queue_draw()
            return

        if y < offset:
            # Scroll up
            if upper < y + height:
                lines = (y + height - upper) // self.line_height + 1
                y = max(0, y - lines * self.line_height)
        else:
            # Scroll down
            lines = height // self.line_height - 1
            y = max(0, y - lines * self.line_height)
        self._vadjustment.set_value(y)
        self.queue_draw()

    def set_check_sentences(self, value):
        if value != self.highlight_sentences:
            self.highlight_sentences = value
            self.queue_draw()

    def set_font(self, font_desc):
        self.font_desc = font_desc
        context = self.create_pango_context()
        context.set_font_description(font_desc)
        metrics = context.get_metrics(None, None)
        if Pango.version_check(1, 44, 0) is None:
            line_height = metrics.get_height()
        else:
            line_height = metrics.get_ascent() + metrics.get_descent()
        self.line_height = math.ceil(line_height * 1.6 / Pango.SCALE)
        self.spacing = math.ceil(line_height * 0.6 / Pango.SCALE)
        logger.debug("set_font: spacing %d, line_height %d", self.spacing, self.line_height)
        self.reflow()

    def set_hadjustment(self, adjustment):
        logger.debug('set_hadjustment')
        if self._hadjustment:
            self._hadjustment.disconnect(self._hadjust_signal)
            self._hadjust_signal = None

        self._hadjustment = adjustment
        if adjustment:
            adjustment.set_properties(
                value=0,
                lower=0,
                upper=0,
                page_size=0
            )
            self._hadjust_signal = adjustment.connect("value-changed", self.on_value_changed)

    def set_vadjustment(self, adjustment):
        logger.debug('set_vadjustment')
        if self._vadjustment:
            self._vadjustment.disconnect(self._vadjust_signal)
            self._vadjust_signal = None

        self._vadjustment = adjustment
        if adjustment:
            height = self.get_allocated_height()
            if self.height < height:
                upper = height
            else:
                upper = self.height
            adjustment.set_properties(
                value=0,
                lower=0,
                upper=upper,
                page_size=height
            )
            self._vadjust_signal = adjustment.connect("value-changed", self.on_value_changed)

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


FuriganaView.set_css_name('FuriganaView')
