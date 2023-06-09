# Copyright (c) 2020-2023 Esrille Inc.
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

furiganapad_PYTHON = \
	application.py \
	breaker.py \
	main.py \
	textbuffer.py \
	textview.py \
	window.py \
	$(NULL)
BUILT_SOURCES = package.py
nodist_furiganapad_PYTHON = package.py
dist_furiganapad_DATA = \
	furiganapad.css \
	furiganapad.menu.ui \
	$(NULL)
furiganapaddir = $(pkgdatadir)/src

bin_SCRIPTS = furiganapad

dist_desktop_DATA = furiganapad.desktop
desktopdir = $(datadir)/applications

CLEANFILES = \
	furiganapad \
	furiganapad.in \
	package.py \
	package.py.in \
	$(NULL)

EXTRA_DIST = \
	furiganapad.in.in \
	package.py.in.in \
	$(NULL)

package.py: package.py.in
	$(AM_V_GEN) \
	( \
		pkgdatadir=${pkgdatadir}; \
		localedir=${localedir}; \
		s=`cat $<`; \
		eval "echo \"$${s}\""; \
	) > $@

furiganapad: furiganapad.in
	$(AM_V_GEN) \
	( \
		pkgdatadir=${pkgdatadir}; \
		s=`cat $<`; \
		eval "echo \"$${s}\""; \
	) > $@
	chmod +x $@

uninstall-hook:
	-rmdir $(furiganapaddir)/__pycache__
	-rmdir $(furiganapaddir)
