# Copyright (c) 2020 Esrille Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

AC_INIT([furiganapad], [0.2.0], [https://github.com/esrille/furiganapad/issues])
AM_INIT_AUTOMAKE([foreign tar-ustar])

AM_GNU_GETTEXT_REQUIRE_VERSION([0.19.8])
AM_GNU_GETTEXT([external])

# define GETTEXT_* variables
GETTEXT_PACKAGE=AC_PACKAGE_NAME
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(
  GETTEXT_PACKAGE, "$GETTEXT_PACKAGE",
    [Define to the read-only architecture-independent data directory.]
)

# Check Python
AM_PATH_PYTHON([3.7])

# OUTPUT files
AC_CONFIG_FILES(
icons/Makefile
locale/Makefile
po/Makefile.in
src/Makefile
src/furiganapad.in
src/package.py.in
tools/Makefile
Makefile
furiganapad.spec
)

AC_OUTPUT
