pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'docs'

furiganapad_docs = [
  'default.css',
  'hiragana_ime.html',
  'index.html',
  'install.html',
  'specification.html',
  'usage.html',
  'icon.png',
  'kids.png',
  'normal.png',
  'screenshot.webm',
]

install_data(furiganapad_docs, install_dir: moduledir)
