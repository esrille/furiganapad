pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'src'
gnome = import('gnome')

gnome.compile_resources('furiganapad',
  'furiganapad.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('PACKAGE_NAME', meson.project_name())
conf.set('VERSION', meson.project_version())
conf.set('prefix', get_option('prefix'))
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'furiganapad.in',
  output: 'furiganapad',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

configure_file(
  input: 'package.py.in',
  output: 'package.py',
  configuration: conf,
  install: true,
  install_dir: moduledir,
  install_mode: 'rw-r--r--'
)

furiganapad_sources = [
  'application.py',
  'breaker.py',
  'furiganapad.css',
  'main.py',
  'textbuffer.py',
  'textview.py',
  'window.py',
]

install_data(furiganapad_sources, install_dir: moduledir)
