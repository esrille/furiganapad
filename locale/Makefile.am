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

kids_DATA = furiganapad.kids.mo
kidsdir = $(datadir)/locale/ja/LC_MESSAGES

EXTRA_DIST = \
	furiganapad.kids.po \
	$(NULL)

CLEANFILES = \
	furiganapad.kids.mo \
	$(NULL)

furiganapad.kids.mo : $(srcdir)/../po/furiganapad.pot furiganapad.kids.po
	msgmerge --update --lang=ja $(srcdir)/furiganapad.kids.po $<
	rm -f $@
	msgfmt -c --statistics --verbose -o $@ $(srcdir)/furiganapad.kids.po
