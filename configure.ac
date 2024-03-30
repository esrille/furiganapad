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

m4_define([furiganapad_version], [0.6.2])
AC_INIT([furiganapad], [furiganapad_version], [https://github.com/esrille/furiganapad/issues])
AC_CONFIG_AUX_DIR([.])
AM_INIT_AUTOMAKE([foreign tar-ustar])

AM_GNU_GETTEXT([external])
AM_GNU_GETTEXT_REQUIRE_VERSION([0.19.8])
AM_GNU_GETTEXT_VERSION([0.19.8])

# Check Python
AM_PATH_PYTHON([3.8])

# define GETTEXT_* variables
GETTEXT_PACKAGE=AC_PACKAGE_NAME
AC_SUBST([GETTEXT_PACKAGE])
AC_DEFINE_UNQUOTED(
  [GETTEXT_PACKAGE], ["$GETTEXT_PACKAGE"],
    [Define to the read-only architecture-independent data directory.]
)

# For GitHub
m4_define(furiganapad_source_version,
  [m4_esyscmd(echo -n furiganapad_version | tr '~' '-')])
SOURCE_VERSION="furiganapad_source_version"
AC_SUBST(SOURCE_VERSION)

# OUTPUT files
AC_CONFIG_FILES(
docs/Makefile
icons/Makefile
locale/Makefile
man/Makefile
man/ja/Makefile
po/Makefile.in
src/Makefile
src/furiganapad.in
src/package.py.in
tools/Makefile
Makefile
)

AC_OUTPUT
