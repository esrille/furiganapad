#
# Copyright (c) 2019-2023  Esrille Inc.
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

import package

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import GLib, Gio, Gtk, Gdk, GObject, Pango

from textview import FuriganaView
from textbuffer import remove_dangling_annotations, get_plain_text

import gettext
import logging
import os
import subprocess


_ = lambda a : gettext.dgettext(package.get_domain(), a)
logger = logging.getLogger(__name__)

IAA = '\uFFF9'  # IAA (INTERLINEAR ANNOTATION ANCHOR)
IAS = '\uFFFA'  # IAS (INTERLINEAR ANNOTATION SEPARATOR)
IAT = '\uFFFB'  # IAT (INTERLINEAR ANNOTATION TERMINATOR)

DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 512


class Window(Gtk.ApplicationWindow):

    def __init__(self, app, file=None):
        self.title = _("FuriganaPad")
        super().__init__(application=app, title=self.title)
        self.set_default_icon_name(package.get_name())
        self.set_default_size(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        grid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(grid)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.textview = FuriganaView()
        self.textview.connect_after('focus-in-event', self.on_textview_focus_in)
        self.textview.connect_after('focus-out-event', self.on_textview_focus_out)

        self.buffer = self.textview.get_buffer()
        self.buffer.connect_after('modified-changed', self.on_modified_changed)
        self.buffer.connect_after('mark-set', self.on_mark_set)

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
        self.search_entry.connect('activate', self.on_find)
        self.search_entry_text = ''

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
        self.replace_from.connect('activate', self.on_find)
        self.replace_to.connect('activate', self.on_replace)
        self.replace_from_text = ''
        self.replace_to_text = ''

        self.rubybar = Gtk.SearchBar()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.rubybar.add(box)
        label = Gtk.Label(_("Ruby") + ': ')
        box.pack_start(label, False, False, 1)
        self.ruby_entry = Gtk.Entry()
        box.pack_start(self.ruby_entry, False, False, 1)
        self.rubybar.connect_entry(self.ruby_entry)
        grid.pack_start(self.rubybar, False, False, 0)
        self.rubybar.set_search_mode(False)
        self.ruby_entry.connect('activate', self.on_ruby)

        self.statusbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.line_col = Gtk.Label()
        self.statusbar.pack_end(self.line_col, False, False, 10)
        grid.pack_start(self.statusbar, False, False, 5)

        self.connect('key-press-event', self.on_key_press_event)

        actions = {
            'new': self.new_callback,
            'open': self.open_callback,
            'save': self.save_callback,
            'saveas': self.save_as_callback,
            'close': self.close_callback,
            'closeall': self.close_all_callback,
            'undo': self.undo_callback,
            'redo': self.redo_callback,
            'cut': self.cut_callback,
            'copy': self.copy_callback,
            'paste': self.paste_callback,
            'find': self.find_callback,
            'replace': self.replace_callback,
            'annotate': self.annotate_callback,
            'unconvert': self.unconvert_callback,
            'selectall': self.select_all_callback,
            'font': self.font_callback,
            'help': self.help_callback,
            'about': self.about_callback,
        }
        for name, method in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect('activate', method)
            self.add_action(action)
        self.connect('delete-event', self.on_delete_event)

        action = Gio.SimpleAction.new_stateful(
            'ruby', None, GLib.Variant.new_boolean(True))
        action.connect('activate', self.ruby_callback)
        self.add_action(action)

        self.highlightlongsentences_action = Gio.SimpleAction.new_stateful(
            'highlightlongsentences', None, GLib.Variant.new_boolean(True))
        self.highlightlongsentences_action.connect(
            'activate', self.highlightlongsentences_callback)
        self.add_action(self.highlightlongsentences_action)

        self.statusbar_action = Gio.SimpleAction.new_stateful(
            'statusbar', None, GLib.Variant.new_boolean(True))
        self.statusbar_action.connect(
            'activate', self.statusbar_callback)
        self.add_action(self.statusbar_action)

        self.file = None
        self._load_file(file)
        self.update_statusbar()

    def _emit_to_focused(self, signal_name, *args):
        focused = self.get_focus()
        if focused:
            focused.emit(signal_name, *args)

    def _load_file(self, file):
        self.set_file(file)
        if file:
            try:
                success, content, etags = file.load_contents(None)
                content = content.decode('utf-8', 'ignore')
                content = remove_dangling_annotations(content)
                if content:
                    self.buffer.begin_user_action()
                    self.buffer.set_text(content)
                    self.buffer.end_user_action()
                    self.buffer.place_cursor(self.buffer.get_start_iter())
                self.buffer.set_modified(False)
            except GLib.Error:
                # Create a new file
                self.save()
                self.update_title()

    def about_callback(self, action, parameter):
        dialog = Gtk.AboutDialog()
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.set_program_name(self.title)
        dialog.set_copyright("Copyright 2019-2023 Esrille Inc.")
        dialog.set_authors(["Esrille Inc."])
        dialog.set_documenters(["Esrille Inc."])
        dialog.set_website("https://www.esrille.com/")
        dialog.set_website_label("Esrille Inc.")
        dialog.set_logo_icon_name(package.get_name())
        dialog.set_version(package.get_version())
        # To close the dialog when "close" is clicked, e.g. on Raspberry Pi OS,
        # the "response" signal needs to be connected about_response_callback
        dialog.connect('response', self.about_response_callback)
        dialog.show()

    def about_response_callback(self, dialog, response):
        dialog.destroy()

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

    def annotate_callback(self, action, parameter):
        start, end = self.buffer.get_selection_bounds()
        if start != end and start.get_line() == end.get_line():
            self.rubybar.set_search_mode(True)

    def close_all_callback(self, action, parameter):
        windows = self.get_application().get_windows()
        for window in windows:
            window.lookup_action('close').activate()

    def close_callback(self, action, parameter):
        if not self.confirm_save_changes():
            self.destroy()

    def confirm_save_changes(self):
        if not self.buffer.get_modified():
            return False
        dialog = Gtk.MessageDialog(
            self, 0, Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.NONE, _("Save changes to this document?"))
        dialog.format_secondary_text(_("If you don't, changes will be lost."))
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

    def copy_callback(self, action, parameter):
        self._emit_to_focused('copy-clipboard')

    def cut_callback(self, action, parameter):
        self._emit_to_focused('cut-clipboard')

    def find_callback(self, action, parameter):
        start, end = self.buffer.get_selection_bounds()
        if start != end:
            self.search_entry_text = self.buffer.get_text(start, end, False).replace('\n', '')
        self.search_entry.set_text(self.search_entry_text)
        self.searchbar.set_search_mode(True)
        self.search_entry.grab_focus()

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

    def get_file(self):
        return self.file

    def help_callback(self, action, parameter):
        # Use yelp to open local HTMLs.
        # cf. https://gitlab.gnome.org/GNOME/yelp/-/merge_requests/24
        url = 'file://' + os.path.join(package.get_datadir(), 'help/index.html')
        subprocess.Popen(['yelp', url])

    def highlightlongsentences_callback(self, action, parameter):
        highlight = not action.get_state()
        action.set_state(GLib.Variant.new_boolean(highlight))
        self.textview.set_check_sentences(highlight)

    def new_callback(self, action, parameter):
        win = Window(self.get_application())
        win.show_all()

    def on_delete_event(self, wid, event):
        return self.confirm_save_changes()

    def on_find(self, entry):
        self.select_text(get_plain_text(entry.get_text()))

    def on_key_press_event(self, wid, event):
        logger.debug('on_key_press: "%s", %08x', Gdk.keyval_name(event.keyval), event.state)
        # Control focus around search bars by checking keys typed into the
        # main window
        if self.search_entry.is_focus():
            if event.keyval == Gdk.KEY_Escape:
                self.search_entry_text = self.search_entry.get_text()
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
                self.replace_from_text = self.replace_from.get_text()
                self.replace_to_text = self.replace_to.get_text()
                self.textview.grab_focus()
                return True
        return False

    def on_mark_set(self, buffer, where, mark):
        if mark.get_name() == 'insert':
            self.update_statusbar()

    def on_modified_changed(self, buffer):
        self.update_title()

    def on_replace(self, entry):
        text_from = get_plain_text(self.replace_from.get_text())
        (start, end) = self.buffer.get_selection_bounds()
        if start != end:
            selection = self.buffer.get_text(start, end, False)
            if selection == text_from:
                text_to = self.replace_to.get_text()
                self.buffer.begin_user_action()
                self.buffer.delete(start, end)
                self.buffer.insert_at_cursor(text_to)
                self.buffer.end_user_action()
                cursor_mark = self.buffer.get_insert()
                self.textview.scroll_mark_onscreen(cursor_mark)
        self.select_text(text_from)

    def on_ruby(self, entry):
        start, end = self.buffer.get_selection_bounds()
        if start != end and start.get_line() == end.get_line():
            text = self.buffer.get_text(start, end, False)
            ruby = get_plain_text(entry.get_text())
            self.buffer.begin_user_action()
            self.buffer.delete(start, end)
            if ruby:
                text = IAA + text + IAS + ruby + IAT
            self.buffer.insert_at_cursor(text)
            self.buffer.end_user_action()
        self.textview.grab_focus()

    def on_textview_focus_in(self, wid, event):
        logger.debug('on_textview_focus_in')
        self.set_action_sensitivity('selectall', True)
        self.searchbar.set_search_mode(False)
        self.replacebar.set_search_mode(False)
        self.rubybar.set_search_mode(False)

    def on_textview_focus_out(self, wid, event):
        logger.debug('on_textview_focus_out')
        self.set_action_sensitivity('selectall', False)

    def open_callback(self, action, parameter):
        open_dialog = Gtk.FileChooserDialog(
            _("Open File"), self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
        self.add_filters(open_dialog)
        open_dialog.set_local_only(False)
        open_dialog.set_modal(True)
        open_dialog.connect('response', self.open_response_cb)
        open_dialog.show()

    def open_response_cb(self, dialog, response):
        file = None
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
        dialog.destroy()
        # Open new window after closing dialog to raise the new window
        # in the stacking order.
        if file:
            win = self.get_application().is_opened(file)
            if win:
                win.present()
            elif not self.buffer.empty():
                win = Window(self.get_application(), file=file)
                win.show_all()
            else:
                self._load_file(file)

    def paste_callback(self, action, parameter):
        self._emit_to_focused('paste-clipboard')

    def redo_callback(self, action, parameter):
        self.textview.emit('redo')

    def replace_callback(self, action, parameter):
        start, end = self.buffer.get_selection_bounds()
        if start != end:
            self.replace_from_text = self.buffer.get_text(start, end, False).replace('\n', '')
        self.replace_from.set_text(self.replace_from_text)
        self.replace_to.set_text(self.replace_to_text)
        self.replacebar.set_search_mode(True)
        self.replace_from.grab_focus()

    def ruby_callback(self, action, parameter):
        ruby = not action.get_state()
        action.set_state(GLib.Variant.new_boolean(ruby))
        self.buffer.set_ruby_mode(ruby)
        self.update_statusbar()

    def save(self):
        message = ''
        (start, end) = self.buffer.get_bounds()
        current_contents = self.buffer.get_text(start, end, True)
        try:
            if current_contents:
                current_contents += '\n'
                current_contents = current_contents.encode()
                self.file.replace_contents(current_contents,
                                           None,
                                           False,
                                           Gio.FileCreateFlags.NONE,
                                           None)
            else:
                self.file.replace_readwrite(None,
                                            False,
                                            Gio.FileCreateFlags.NONE,
                                            None)
            return self.set_file(self.file)
        except GLib.Error as e:
            dialog = Gtk.MessageDialog(
                self, 0, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK, _("Could not save the file."))
            dialog.format_secondary_text(e.message)
            dialog.run()
            dialog.destroy()
            self.save_as()
            return True

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
            except GLib.Error:
                logger.exception(f'Could not create file "{self.file.get_path()}"')
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.file = dialog.get_file()
            dialog.destroy()
            return self.save()
        dialog.destroy()
        return True

    def save_as_callback(self, action, parameter):
        self.save_as()

    def save_callback(self, action, parameter):
        if self.file is not None:
            self.save()
        else:
            self.save_as()

    def select_all_callback(self, action, parameter):
        self.textview.emit('select-all', True)

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

    def set_action_sensitivity(self, action_name, state):
        self.lookup_action(action_name).set_enabled(state)

    def set_file(self, file):
        self.file = file
        return self.buffer.set_modified(not file)

    def statusbar_callback(self, action, parameter):
        visible = not action.get_state()
        action.set_state(GLib.Variant.new_boolean(visible))
        self.statusbar.set_visible(visible)

    def unconvert_callback(self, action, parameter):
        self.buffer.begin_user_action()
        self.buffer.unconvert(self.buffer.get_cursor())
        self.buffer.end_user_action()

    def undo_callback(self, action, parameter):
        self.textview.emit('undo')

    def update_statusbar(self):
        cursor = self.buffer.get_cursor()
        status = f'{cursor.get_line() + 1}:{cursor.get_plain_line_offset() + 1}    '
        if self.buffer.get_ruby_mode():
            status += _("Ruby")
        else:
            status += '<s>' + _("Ruby") + '</s>'
        self.line_col.set_markup(status)

    def update_title(self):
        title = self.title
        if self.file:
            title = self.file.get_basename() + ' – ' + title
        if self.buffer.get_modified():
            title = '*' + title
        self.set_title(title)
