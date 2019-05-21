Name:       furiganapad
Version:    0.1.0
Release:    1%{?dist}
Summary:    A text editor for Japanese texts with ruby characters
License:    LGPLv2+
URL:        https://github.com/esrille/%{name}
Source0:    https://github.com/esrille/%{name}/releases/download/v%{version}/%{name}-%{version}.tar.xz

BuildRequires: desktop-file-utils
BuildRequires: meson
BuildRequires: python3-devel
Requires:      gobject-introspection
Requires:      google-noto-sans-cjk-ttc-fonts
Requires:      gtk3
Requires:      pango
Requires:      python3
Requires:      python3-cairo
Requires:      python3-gobject
BuildArch:     noarch

%description
FuriganaPad is a text editor for Japanese texts with ruby characters.

%prep
%setup -q

%build
%meson
%meson_build

%install
%meson_install

%files
%doc README.md CONTRIBUTING.md
%license COPYING NOTICE
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/%{name}/
%{_datadir}/icons/hicolor/96x96/apps/%{name}.png
%{python3_sitelib}/esrille_%{name}/

%changelog
