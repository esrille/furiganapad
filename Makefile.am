# Copyright (c) 2020-2024 Esrille Inc.
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

# po must be after the directories that contain .desktop files
SUBDIRS = \
	docs \
	icons \
	locale \
	man \
	src\
	tools\
	po \
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

debian/changelog:
	$(AM_V_GEN) \
	( \
		date=`date -R`; \
		version=@VERSION@; \
		source_version=@SOURCE_VERSION@; \
		s=`cat debian/changelog.in`; \
		eval "echo \"$${s}\""; \
	) > $@

@PACKAGE_NAME@.spec:
	$(AM_V_GEN) \
	( \
		date=`date '+%a %b %d %Y'`; \
		version=@VERSION@; \
		source_version=@SOURCE_VERSION@; \
		s=`cat @PACKAGE_NAME@.spec.in`; \
		eval "echo \"$${s}\""; \
	) > $@

uninstall-hook:
	-rmdir $(pkgdatadir)
