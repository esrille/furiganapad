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
from gi.repository import Gtk, Gdk, GObject, Pango, PangoCairo

from textbuffer import TextBuffer, has_newline, remove_dangling_annotations

import cairo
import logging


logger = logging.getLogger(__name__)

# A sentence with more than SENTENCE_SHORT characters is not short.
SENTENCE_SHORT = 50
# A sentence with more than SENTENCE_LONG characters is long.
SENTENCE_LONG = 60

DEFAULT_FONT = "Noto Sans Mono CJK JP 18px"
RUBY_DIV = 2.7

ESCAPE = str.maketrans({
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;'
})


class TextView(Gtk.DrawingArea, Gtk.Scrollable):

    __gsignals__ = {
        'cut-clipboard': (GObject.SIGNAL_RUN_LAST, None, ()),
        'copy-clipboard': (GObject.SIGNAL_RUN_LAST, None, ()),
        'paste-clipboard': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'redo': (GObject.SIGNAL_RUN_LAST, None, ()),
        'select-all': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'undo': (GObject.SIGNAL_RUN_LAST, None, ())
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
        self.set_font(desc)

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
        self.im.set_cursor_location(self.caret)
        cr.restore()

    def _draw_rubies(self, cr, layout, paragraph, plain, height, cursor_offset):
        lt = PangoCairo.create_layout(cr)
        desc = self.get_font().copy_static()
        size = desc.get_size()
        desc.set_size(size // RUBY_DIV)
        lt.set_font_description(desc)
        for pos, length, ruby in paragraph.rubies:
            if self._has_preedit() and cursor_offset <= pos:
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
        offset = 0
        if self._vadjustment:
            offset = self._vadjustment.get_value()
        return offset

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

    def do_copy_clipboard(self):
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        self.buffer.copy_clipboard(clipboard)

    def do_cut_clipboard(self):
        clipboard = self.get_clipboard(Gdk.SELECTION_CLIPBOARD)
        self.buffer.cut_clipboard(clipboard, self.get_editable())
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

    def do_select_all(self, select):
        self.buffer.select_all()
        self.queue_draw()

    def do_undo(self):
        self.im.reset()
        self.buffer.emit('undo')

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
                iter = self.buffer.get_iter_at_line_offset(i, offset)
                return inside, iter
            height += h
            i += 1
        return False, self.buffer.get_end_iter()

    def get_paragraph(self, line):
        if 0 <= line and line < self.get_buffer().get_line_count():
            return self.get_buffer().paragraphs[line]
        return None

    def get_vadjustment(self):
        return self._vadjustment

    def on_commit(self, wid, str):
        self.buffer.begin_user_action()
        self.buffer.insert_at_cursor(str)
        self.buffer.end_user_action()
        self.place_cursor_onscreen()
        return True

    def on_delete(self, textbuffer, start, end):
        if start.get_line() == end.get_line():
            self.reflow_line = start.get_line()
        else:
            self.reflow_line = -1

    def on_delete_surrounding(self, wid, offset, n_chars):
        self.buffer.begin_user_action()
        self.buffer.delete_surrounding(offset, n_chars)
        self.buffer.end_user_action()
        self.place_cursor_onscreen()
        return True

    def on_deleted(self, textbuffer, start, end):
        self.reflow(self.reflow_line)
        self.queue_draw()

    def on_draw(self, wid, cr):
        if wid.get_allocated_width() != self.width:
            self.reflow(redraw=False)
        height = wid.get_allocated_height()

        cr.set_source_rgb(1, 1, 1)
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
                attrListPreedit = Pango.AttrList().new()
                if lineno == cursor.get_line():
                    cursor_offset = cursor.get_plain_line_offset()
                    if self._has_preedit():
                        text = text[:cursor_offset] + self.preedit[0] + text[cursor_offset:]
                        attrListPreedit.splice(self.preedit[1], len(text[:cursor_offset].encode()), len(self.preedit[0].encode()))
                        cursor_offset += self.preedit[2]
                if start == end or lineno < start.get_line() or end.get_line() < lineno:
                    markup = self._check_sentences(text)
                elif start.get_line() < lineno and lineno < end.get_line():
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
                elif lineno == end.get_line():
                    o = end.get_plain_line_offset()
                    markup = '<span background="#ACCEF7">' + text[:o].translate(ESCAPE) + '</span>' + \
                             text[o:].translate(ESCAPE)
                layout.set_markup(markup, -1)
                if lineno == cursor.get_line() and self._has_preedit():
                    attrList = layout.get_attributes()
                    attrList.splice(attrListPreedit, 0, 0)
                    layout.set_attributes(attrList)
                PangoCairo.update_layout(cr, layout)
                cr.move_to(0, y)
                PangoCairo.show_layout(cr, layout)
                self._draw_rubies(cr, layout, paragraph, text, y, cursor_offset)
                if lineno == cursor.get_line():
                    self._draw_caret(cr, layout, text, y, cursor_offset)
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
        logger.info("on_focus_in")
        self.im.set_client_window(wid.get_window())
        self.im.focus_in()
        return True

    def on_focus_out(self, wid, event):
        logger.info("on_focus_out")
        self.im.focus_out()
        return True

    def on_inserted(self, textbuffer, iter, text):
        if has_newline(text):
            self.reflow()
        else:
            self.reflow(iter.get_line())
        self.queue_draw()

    def on_key_press(self, wid, event):
        is_selection = (event.state & Gdk.ModifierType.SHIFT_MASK)
        is_control = (event.state & Gdk.ModifierType.CONTROL_MASK)
        logger.info("on_key_press: '%s', %08x", Gdk.keyval_name(event.keyval), event.state)
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
        if self.im.filter_keypress(event):
            return True
        return False

    def on_mouse_move(self, wid, event):
        if (event.state & Gdk.ModifierType.BUTTON1_MASK):
            inside, cursor = self.get_iter_at_location(event.x, self._get_offset() + event.y)
            self.buffer.move_cursor(cursor, True)
            self.place_cursor_onscreen()
        return True

    def on_mouse_press(self, wid, event):
        self.im.reset()
        if event.button == Gdk.BUTTON_PRIMARY:
            is_selection = (event.state & Gdk.ModifierType.SHIFT_MASK)
            inside, cursor = self.get_iter_at_location(event.x, self._get_offset() + event.y)
            self.buffer.move_cursor(cursor, is_selection)
            self.place_cursor_onscreen()
        return True

    def on_mouse_release(self, wid, event):
        return True

    def on_preedit_changed(self, wid):
        self.preedit = self.im.get_preedit_string()
        cursor = self.buffer.get_cursor()
        self.buffer.delete_selection(True, True)
        self.reflow(cursor.get_line())
        logger.info('on_preedit_changed: "%s" %d', self.preedit[0], self.preedit[2])

    def on_preedit_end(self, wid):
        self.preedit = self.im.get_preedit_string()
        self.buffer.delete_selection(True, True)
        logger.info('_end(self, w: "%s" %d', self.preedit[0], self.preedit[2])

    def on_preedit_start(self, wid):
        self.preedit = self.im.get_preedit_string()
        self.buffer.delete_selection(True, True)
        logger.info('on_preedit_start: "%s" %d', self.preedit[0], self.preedit[2])

    def on_retrieve_surrounding(self, wid):
        text, offset = self.buffer.get_surrounding()
        self.im.set_surrounding(text, len(text.encode()), len(text[:offset].encode()))
        return True

    def on_value_changed(self, *whatever):
        self.queue_draw()

    def place_cursor_onscreen(self):
        self.scroll_mark_onscreen(self.buffer.get_insert())

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

    def set_check_sentences(self, value):
        if value != self.highlight_sentences:
            self.highlight_sentences = value
            self.queue_draw()

    def set_font(self, font_desc):
        self.font_desc = font_desc
        if font_desc.get_size_is_absolute():
            self.spacing = font_desc.get_size() / Pango.SCALE * 7 / 8
        else:
            context = self.create_pango_context()
            dpi = PangoCairo.context_get_resolution(context)
            self.spacing = font_desc.get_size() / Pango.SCALE * dpi / 72 * 7 / 8
        self.reflow()

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
            self._hadjust_signal = adjustment.connect("value-changed", self.on_value_changed)

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
