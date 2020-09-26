# Copyright (c) 2020 Esrille Inc.
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

help_DATA = \
	default.css \
	hiragana_ime.html \
	index.html \
	install.html \
	specification.html \
	usage.html \
	icon.png \
	kids.png \
	normal.png \
	screenshot.mp4 \
	$(NULL)

helpdir = $(pkgdatadir)/help

EXTRA_DIST = \
	$(help_DATA) \
	update \
	Makefile.am \
	md2html.py \
	hiragana_ime.md \
	index.md \
	install.md \
	specification.md \
	usage.md \
	template.html \
	$(NULL)

uninstall-hook:
	-rmdir $(helpdir)
