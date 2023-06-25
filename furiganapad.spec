Name:       furiganapad
Version:    0.6.0
Release:    1%{?dist}
Summary:    A text editor for Japanese texts with ruby characters
License:    LGPL-2.1-or-later
URL:        https://github.com/esrille/%{name}
Source0:    https://github.com/esrille/%{name}/releases/download/v%{version}/%{name}-%{version}.tar.gz
Requires:   ibus-hiragana >= 0.14.2
Requires:   google-noto-cjk-fonts-common, google-noto-fonts-common
Requires:   gtk3
Requires:   pango >= 1.44.0
Requires:   python3
Requires:   python3-cairo
Requires:   python3-gobject
Requires:   python3-pyicu
Requires:   yelp
BuildRequires: gettext-devel
BuildRequires: libtool
BuildRequires: pkgconfig
BuildRequires: python3-devel
BuildArch:     noarch

%description
FuriganaPad can be used to edit Japanese texts with ruby characters.
Ruby characters are automatically placed above Kanji characters when
converting Hiragana characters into Kanji characters by using
Hiragana IME for IBus.

%global __python %{__python3}

%prep
%autosetup

%build
%configure
%make_build

%install
%make_install
%find_lang %{name}

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README.md CONTRIBUTING.md
%license COPYING NOTICE
%{_bindir}/%{name}
%{_datadir}/%{name}
%{_datadir}/applications
%{_datadir}/icons/hicolor/96x96/apps/furiganapad.png
%{_datadir}/locale/ja/LC_MESSAGES/furiganapad.kids.mo
%{_mandir}/man1/furiganapad.1*
%{_mandir}/ja/man1/furiganapad.1*

%changelog
* Sun Jun 25 2023 Esrille Inc. <info@esrille.com> - 0.6.0-1
- See https://github.com/esrille/furiganapad/releases/tag/v0.6.0

* Tue Nov 22 2022 Esrille Inc. <info@esrille.com> - 0.5.5-1
- See https://github.com/esrille/furiganapad/releases/tag/v0.5.5
