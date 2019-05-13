PROGRAM = furiganapad.py
RESOURCES = furiganapad.menu.ui \
	furiganapad.menu.ja_JP.ui furiganapad.ja_JP.json

prefix ?= /usr/local
bindir = $(prefix)/bin
applicationsdir = $(prefix)/share/applications
icondir = $(prefix)/share/icons/hicolor/96x96/apps
resourcedir = $(prefix)/share/$(patsubst %.py,%,$(PROGRAM))

all: README.md

README.md : README.txt
	./convert_to_tag.py README.txt > README.md

install:
	install -d $(bindir)
	install $(PROGRAM) $(bindir)/$(patsubst %.py,%,$(PROGRAM))
	install -d $(applicationsdir)
	install $(patsubst %.py,%.desktop,$(PROGRAM)) $(applicationsdir)
	install -d $(icondir)
	install $(patsubst %.py,%.png,$(PROGRAM)) $(icondir)
	install -d $(resourcedir)
	install $(RESOURCES) $(resourcedir)

uninstall:
	rm $(bindir)/$(patsubst %.py,%,$(PROGRAM))
	rm $(applicationsdir)/$(patsubst %.py,%.desktop,$(PROGRAM))
	rm $(icondir)/$(patsubst %.py,%.png,$(PROGRAM))
	rm $(addprefix $(resourcedir)/,$(RESOURCES))
	rmdir $(resourcedir)

.PHONY: all install uninstall
