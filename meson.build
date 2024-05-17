project('furiganapad',
          version: '0.7.0',
    meson_version: '>= 0.53.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')

subdir('data')
subdir('docs')
subdir('man')
subdir('po')
subdir('po.school')
subdir('src')

meson.add_dist_script('meson/update-changelog.sh', meson.project_version())

meson.add_install_script('meson/postinstall.py')
