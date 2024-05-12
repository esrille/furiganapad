#
# Copyright (c) 2019-2024  Esrille Inc.
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
from package import _

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, GLib, Gio, Gtk

from window import Window, DEFAULT_WIDTH, DEFAULT_HEIGHT

import os
import logging


logger = logging.getLogger(__name__)


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         application_id='com.esrille.furiganapad',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
                         **kwargs)
        self.cursor = None

        self.window_x = None
        self.window_y = None
        self.window_width = None
        self.window_height = None

        # e.g., --window-x=2560 --window-y=32 --window-width=1024 --window-height=600
        self.add_main_option("window-x", ord('x'), GLib.OptionFlags.NONE, GLib.OptionArg.INT,
                             _("Initial window x position"), _("x"))
        self.add_main_option("window-y", ord('y'), GLib.OptionFlags.NONE, GLib.OptionArg.INT,
                             _("Initial window y position"), _("y"))
        self.add_main_option("window-width", ord('w'), GLib.OptionFlags.NONE, GLib.OptionArg.INT,
                             _("Initial window width"), _("w"))
        self.add_main_option("window-height", ord('h'), GLib.OptionFlags.NONE, GLib.OptionArg.INT,
                             _("Initial window height"), _("h"))
        self.add_main_option("version", ord('v'), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
                             _("Print version information"), None)
    def do_activate(self):
        pathname = os.path.join(package.get_user_datadir(), 'session')
        logger.info(f'do_activate: {pathname}')
        try:
            with open(pathname, 'r') as file:
                for line in file:
                    if line.startswith('#'):
                        continue
                    # f'furiganapad -x {x} -y {y} -w {w} -h {h} {path} &\n'
                    if not line.startswith('furiganapad '):
                        continue
                    args = line.split()
                    if len(args) < 10:
                        continue
                    logger.info(f'{len(args)}')
                    x = int(args[2])
                    y = int(args[4])
                    w = int(args[6])
                    h = int(args[8])
                    path = args[9]
                    logger.info(f'do_activate: -x {x} -y {y} -w {w} -h {h} {path}')

                    file = Gio.File.new_for_path(path)
                    win = self.is_opened(file)
                    if win:
                        win.present()
                    else:
                        win = Window(self, file=file)
                        win.show_all()
                    win.move(x, y)
                    win.resize(w, h)
        except OSError:
            logger.exception(f"Could not read '{pathname}'")
        except TypeError:
            logger.exception(f"Broken session file '{pathname}'")
        if 0 < len(self.get_windows()):
            return
        win = Window(self)
        win.show_all()
        win.move(self.window_x, self.window_y)
        win.resize(self.window_width, self.window_height)

    def do_command_line(self, command_line):
        # call the default command line handler
        Gtk.Application.do_command_line(self, command_line)

        screen = Gdk.Screen.get_default()
        n = screen.get_primary_monitor()
        monitor_n_geo = screen.get_monitor_geometry(n)

        options = command_line.get_options_dict()

        if options.contains('version'):
            print(package.get_name() + ' ' + package.get_version())
            return 0

        value = options.lookup_value('window-x', GLib.VariantType.new('i'))
        self.window_x = value.get_int32() if value else monitor_n_geo.x
        value = options.lookup_value('window-y', GLib.VariantType.new('i'))
        self.window_y = value.get_int32() if value else monitor_n_geo.y
        value = options.lookup_value('window-width', GLib.VariantType.new('i'))
        self.window_width = value.get_int32() if value else DEFAULT_WIDTH
        value = options.lookup_value('window-height', GLib.VariantType.new('i'))
        self.window_height = value.get_int32() if value else DEFAULT_HEIGHT

        args = command_line.get_arguments()[1:]
        if args:
            files = []
            for pathname in args:
                files.append(command_line.create_file_for_arg(pathname))
            self.do_open(files, '')
        else:
            self.do_activate()
        return 0

    def do_open(self, files, hint):
        for file in files:
            win = self.is_opened(file)
            if win:
                win.present()
            else:
                win = Window(self, file=file)
                win.show_all()
            if len(files) == 1:
                win.move(self.window_x, self.window_y)
                win.resize(self.window_width, self.window_height)
            if not self.cursor:
                self.cursor = Gdk.Cursor.new_from_name(win.get_display(), 'default')

    def do_startup(self):
        Gtk.Application.do_startup(self)

        resource_path = os.path.join(package.get_datadir(), 'furiganapad.gresource')
        resource = Gio.Resource.load(resource_path)
        resource._register()

        builder = Gtk.Builder()
        builder.set_translation_domain(package.get_domain())
        builder.add_from_resource('/com/esrille/furiganapad/furiganapad.menu.ui')
        self.set_menubar(builder.get_object('menubar'))

        style_provider = Gtk.CssProvider()
        style_provider.load_from_path(os.path.join(os.path.dirname(__file__), 'furiganapad.css'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', self.on_quit)
        self.add_action(action)

    def is_opened(self, file):
        windows = self.get_windows()
        for window in windows:
            if window.get_file() and window.get_file().equal(file):
                return window
        return None

    def get_default_cursor(self):
        return self.cursor

    def on_quit(self, *args):
        pathname = os.path.join(package.get_user_datadir(), 'session')
        logger.info(f'on_quit: {pathname}')
        try:
            descriptor = os.open(pathname, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            with open(descriptor, 'w') as file:
                file.write('#!/bin/sh\n')
                windows = self.get_windows()
                for window in windows:
                    x, y = window.get_position()
                    w, h = window.get_size()
                    window.present()
                    window.lookup_action('close').activate()
                    if window.get_file():
                        path = window.get_file().get_path()
                        file.write(f'furiganapad -x {x} -y {y} -w {w} -h {h} {path} &\n')
        except:
            logger.exception(f"Could not create '{pathname}'")
        if 0 < len(self.get_windows()):
            return
