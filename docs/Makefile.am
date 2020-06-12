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
