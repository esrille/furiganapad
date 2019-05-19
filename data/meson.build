pkgdatadir = join_paths(datadir, meson.project_name())
desktopdir = join_paths(datadir, 'applications')
icondir = join_paths(datadir, 'icons', 'hicolor')

gui_data = [
  'furiganapad.json',
  'furiganapad.ja_JP.json',
  'furiganapad.menu.ui',
  'furiganapad.menu.ja_JP.ui',
]
install_data(gui_data, install_dir: pkgdatadir)

install_data ('furiganapad.desktop',
  install_dir: desktopdir)
install_data ('furiganapad.png',
  install_dir: join_paths(icondir, '96x96', 'apps'))
