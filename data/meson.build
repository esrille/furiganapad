metainfo_file = i18n.merge_file (
  input: 'com.esrille.furiganapad.metainfo.xml.in',
  output: 'com.esrille.furiganapad.metainfo.xml',
  po_dir: '../po',
  install: true,
  install_dir: get_option('datadir') / 'metainfo'
)

# Validate metainfo
appstreamcli = find_program('appstreamcli', required: false)
if appstreamcli.found()
  test(
    'validate-metainfo', appstreamcli,
    args: [
      'validate', '--no-net', '--explain', metainfo_file.full_path()
    ]
  )
endif

desktop_file = i18n.merge_file(
  input: 'com.esrille.furiganapad.desktop.in',
  output: 'com.esrille.furiganapad.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: get_option('datadir') / 'applications'
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

subdir('icons')
