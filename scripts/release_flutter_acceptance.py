"""Installed-wheel acceptance using disposable healthy and broken fixtures."""
import argparse, json, shutil, subprocess, tempfile, sys
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--flutter', required=True)
parser.add_argument('--output', type=Path, required=True)
args=parser.parse_args()
source=Path(__file__).resolve().parents[1]
root=Path(tempfile.mkdtemp(prefix='forge-alpha-flutter-'))/'app'
shutil.copytree(source/'examples/flutter_fixture',root,ignore=shutil.ignore_patterns('.dart_tool','build','.git'))
flutter=args.flutter
subprocess.run([flutter,'pub','get'],cwd=root,check=True)
command=[sys.executable,'-m','forge.cli','check',str(root),'--flutter-bin',flutter,'--json']
results={}
for case in ['healthy','missing_notification']:
    if case!='healthy':
        p=root/'lib/counter_model.dart'
        text=p.read_text()
        assert 'notifyListeners();' in text
        p.write_text(text.replace('notifyListeners();','// seeded missing notification'))
    run=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=240)
    report=json.loads(run.stdout)
    results[case]={'exit_code':run.returncode,'report':report}
    assert run.returncode==(0 if case=='healthy' else 1),run.stdout+run.stderr
    if case!='healthy':
        assert any(c['name']=='unit_widget' and c['status']=='failed' for c in report['checks'])
args.output.write_text(json.dumps(results,indent=2)+'\n')
print('Installed wheel: healthy fixture passed; missing notification reproduced. Original unchanged.')
