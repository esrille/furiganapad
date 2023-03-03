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

from gi.repository import GLib

GLib.set_prgname(package.get_name())

from application import Application

import gettext
import locale
import logging
import os
import signal
import sys

logger = logging.getLogger(__name__)


def main():
    # Create user specific data directory
    user_datadir = package.get_user_datadir()
    os.makedirs(user_datadir, exist_ok=True)

    if __debug__:
        logging.basicConfig(level=logging.DEBUG)

    app = Application()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)


if __name__ == '__main__':
    locale.bindtextdomain(package.get_name(), package.get_localedir())
    gettext.bindtextdomain(package.get_name(), package.get_localedir())
    main()
