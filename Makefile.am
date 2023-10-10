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

SUBDIRS = \
	docs \
	icons \
	locale \
	man \
	po \
	src\
	tools\
	$(NULL)

EXTRA_DIST = \
	debian/changelog \
	debian/changelog.in \
	debian/compat \
	debian/control \
	debian/copyright \
	debian/rules \
	debian/source/format \
	autogen.sh \
	@PACKAGE_NAME@.spec \
	@PACKAGE_NAME@.spec.in \
	CONTRIBUTING.md \
	COPYING \
	NOTICE\
	README.md \
	README.txt \
	$(NULL)

DISTCLEANFILES = \
	po/stamp-it \
	$(NULL)

README.md : README.txt
	tools/convert_to_tag.py README.txt README.md

uninstall-hook:
	-rmdir $(pkgdatadir)
