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

import package

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gio, Gtk

from window import Window

import os
import logging


logger = logging.getLogger(__name__)


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         application_id="com.esrille.furiganapad",
                         flags=Gio.ApplicationFlags.HANDLES_OPEN,
                         **kwargs)
        self.cursor = None

    def do_activate(self):
        win = Window(self)
        win.show_all()

    def do_open(self, files, *hint):
        for file in files:
            win = self.is_opened(file)
            if win:
                win.present()
            else:
                win = Window(self, file=file)
                win.show_all()
            if not self.cursor:
                self.cursor = Gdk.Cursor.new_from_name(win.get_display(), "default")

    def do_startup(self):
        Gtk.Application.do_startup(self)

        builder = Gtk.Builder()
        builder.set_translation_domain(package.get_domain())
        filename = os.path.join(os.path.dirname(__file__), "furiganapad.menu.ui")
        builder.add_from_file(filename)
        self.set_menubar(builder.get_object("menubar"))

        style_provider = Gtk.CssProvider()
        style_provider.load_from_path(os.path.join(os.path.dirname(__file__), 'furiganapad.css'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def is_opened(self, file):
        windows = self.get_windows()
        for window in windows:
            if window.get_file() and window.get_file().equal(file):
                return window
        return None

    def get_default_cursor(self):
        return self.cursor
