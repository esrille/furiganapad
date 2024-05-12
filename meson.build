project('furiganapad',
          version: '0.7.0~rc1',
    meson_version: '>= 0.59.0',
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

gnome.post_install(
     glib_compile_schemas: false,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)

meson.add_dist_script('meson/update-changelog.sh', meson.project_version())
