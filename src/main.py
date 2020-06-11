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
from gi.repository import Gio
from gi.repository import GLib

GLib.set_prgname(package.get_name())

from application import Application

import gettext
import locale
import logging
import signal
import sys

if __name__ == '__main__':
    try:
        locale.bindtextdomain(package.get_domain(), package.get_localedir())
    except Exception:
        pass
    gettext.bindtextdomain(package.get_domain(), package.get_localedir())
    logging.basicConfig(level=logging.DEBUG)
    app = Application()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
