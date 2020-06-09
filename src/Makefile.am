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


furiganapad_PYTHON = \
	application.py \
	i18n.py \
	main.py \
	textbuffer.py \
	textview.py \
	window.py \
	$(NULL)
BUILT_SOURCES = package.py
nodist_furiganapad_PYTHON = package.py
furiganapad_DATA = \
	furiganapad.ja_JP.json \
	furiganapad.json \
	furiganapad.menu.ja_JP.ui \
	furiganapad.menu.ui \
	$(NULL)
furiganapaddir = $(pkgdatadir)/src

bin_SCRIPTS = furiganapad

desktop_DATA = furiganapad.desktop
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

uninstall-hook:
	-rmdir $(furiganapaddir)/__pycache__
	-rmdir $(furiganapaddir)
