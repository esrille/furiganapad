pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'docs'

furiganapad_docs = [
  'default.css',
  'hiragana_ime.html',
  'index.html',
  'install.html',
  'specification.html',
  'usage.html',
  'furiganapad.flathub.png',
  'icon.png',
  'normal.png',
  'school.png',
  'screenshot.webm'
]

install_data(furiganapad_docs, install_dir: moduledir)
