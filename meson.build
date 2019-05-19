project('furiganapad',
  version: '0.1.0',
  meson_version: '>= 0.40.0',
)

gnome = import('gnome')
python3 = import('python3')

prefix = get_option('prefix')

bindir = join_paths(prefix, get_option('bindir'))
datadir = join_paths(prefix, get_option('datadir'))
localedir = join_paths(prefix, get_option('localedir'))
pythondir = join_paths(prefix, python3.sysconfig_path('purelib'))

defs_conf = configuration_data()
defs_conf.set('DATADIR', datadir)
defs_conf.set('PYTHONDIR', pythondir)

configure_file(
  input: 'furiganapad.in',
  output: 'furiganapad',
  configuration: defs_conf,
  install: true,
  install_dir: bindir
)

subdir('data')

install_subdir(
  'esrille_furiganapad',
  install_dir: pythondir
)

meson.add_install_script('meson-postinstall.py')
