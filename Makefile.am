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

SUBDIRS = \
	icons \
	src\
	tools\
	$(NULL)

EXTRA_DIST = \
	debian/changelog \
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

CLEANFILES = \
	README.md \
	$(NULL)

README.md : README.txt
	tools/convert_to_tag.py README.txt README.md

src/furiganapad.json : $(src)
	tools/gettext.py $^ -o $@

uninstall-hook:
	-rmdir $(pkgdatadir)
