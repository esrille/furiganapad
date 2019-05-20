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
import locale
import json

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk, GObject

from . import i18n_set_dictionary
from .window import Window


class Application(Gtk.Application):

    def __init__(self, resourcedir='', *args, **kwargs):
        super().__init__(*args,
                         flags=Gio.ApplicationFlags.HANDLES_OPEN,
                         **kwargs)

        if resourcedir:
            self.resourcedir = resourcedir
        else:
            self.resourcedir = os.path.join(os.path.dirname(sys.argv[0]), "data")
        print(self.resourcedir)

        self.lang = locale.getdefaultlocale()[0]
        filename = os.path.join(self.resourcedir, "furiganapad." + self.lang + ".json")
        try:
            with open(filename, 'r') as file:
                i18n_set_dictionary(json.load(file))
        except OSError as e:
            pass

    def do_activate(self):
        win = Window(self)
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
            win = Window(self, file=file)
            win.show_all()
