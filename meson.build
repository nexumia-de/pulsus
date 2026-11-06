project('pulsus',
  version: '0.1.0',
  meson_version: '>= 1.0',
  license: 'AGPL-3.0-or-later',
)

base_id = 'de.nexumia.Pulsus'
# Nightly app next to the stable one (docs/release-channels.md).
nightly = get_option('profile') == 'development'
app_id = nightly ? base_id + '.Devel' : base_id

python = import('python').find_installation('python3')
pythondir = python.get_install_dir()

python.install_sources(
  'pulsus/__init__.py',
  'pulsus/__main__.py',
  'pulsus/card.py',
  'pulsus/charts.py',
  'pulsus/demo.py',
  'pulsus/main.py',
  'pulsus/metrics.py',
  'pulsus/preferences.py',
  'pulsus/settings.py',
  'pulsus/stats.py',
  'pulsus/text.py',
  'pulsus/today.py',
  'pulsus/window.py',
  'pulsus/workouts.py',
  subdir: 'pulsus',
)
# Folder modules, one file per job.
python.install_sources(
  'pulsus/data/__init__.py',
  'pulsus/data/location.py',
  'pulsus/data/records.py',
  'pulsus/data/sleep.py',
  'pulsus/data/source.py',
  'pulsus/data/store.py',
  'pulsus/data/values.py',
  subdir: 'pulsus' / 'data',
)
python.install_sources(
  'pulsus/metric/__init__.py',
  'pulsus/metric/day.py',
  'pulsus/metric/page.py',
  'pulsus/metric/period.py',
  'pulsus/metric/view.py',
  subdir: 'pulsus' / 'metric',
)
# Loaded next to the Python files, also from the source tree.
install_data('pulsus/style.css', install_dir: pythondir / 'pulsus')

conf = configuration_data()
conf.set('PYTHON', python.full_path())
conf.set('PYTHONDIR', get_option('prefix') / pythondir)
configure_file(
  input: 'data/pulsus.in',
  output: 'pulsus',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

config = configuration_data()
config.set('APP_ID', app_id)
config.set('BUILD_LABEL', get_option('build_label'))
configure_file(
  input: 'pulsus/config.py.in',
  output: 'config.py',
  configuration: config,
  install: true,
  install_dir: pythondir / 'pulsus',
)

if nightly
  # The stable files in data/ stay the only source; the nightly app gets
  # its own id and the name "Watch Health (Nightly)".
  sed = find_program('sed')
  variant = [sed, '-e', 's/' + base_id + '/' + app_id + '/g',
             '-e', 's/^Name=Watch Health$/Name=Watch Health (Nightly)/',
             '-e', 's|<name>Watch Health</name>|<name>Watch Health (Nightly)</name>|',
             '@INPUT@']
  desktop = configure_file(input: 'data' / base_id + '.desktop',
    output: app_id + '.desktop', command: variant, capture: true)
  metainfo = configure_file(input: 'data' / base_id + '.metainfo.xml',
    output: app_id + '.metainfo.xml', command: variant, capture: true)
else
  desktop = files('data' / base_id + '.desktop')
  metainfo = files('data' / base_id + '.metainfo.xml')
endif
install_data(desktop, install_dir: get_option('datadir') / 'applications')
install_data(metainfo, install_dir: get_option('datadir') / 'metainfo')
install_data('data/icons/hicolor/scalable/apps' / base_id + '.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/scalable/apps',
  rename: app_id + '.svg')
# Pulsus's own symbolic icons for the metrics.
install_subdir('data/icons/hicolor/symbolic/apps',
  install_dir: get_option('datadir') / 'icons/hicolor/symbolic',
  strip_directory: false)

desktop_file_validate = find_program('desktop-file-validate', required: false)
if desktop_file_validate.found()
  test('validate-desktop', desktop_file_validate, args: [desktop])
endif
appstreamcli = find_program('appstreamcli', required: false)
if appstreamcli.found()
  test('validate-metainfo', appstreamcli,
    args: ['validate', '--no-net', metainfo])
endif
