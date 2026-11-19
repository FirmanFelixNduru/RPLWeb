"""Capture an actual Orca browser page; no generated or edited screenshot content."""
import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def cli(*args):
    result = subprocess.run([os.environ.get('ORCA_CLI_COMMAND', 'orca'), *args, '--json'],
                            capture_output=True, text=True, encoding='utf-8', timeout=55)
    data = json.loads(result.stdout)
    if not data.get('ok'):
        raise RuntimeError(data.get('error'))
    return data['result']


parser = argparse.ArgumentParser()
parser.add_argument('--page', required=True)
parser.add_argument('--url', required=True)
parser.add_argument('--name', required=True)
args = parser.parse_args()
navigation = cli('goto', '--page', args.page, '--url', args.url)
actual_url = navigation.get('url', '')
if actual_url.startswith('https://github.com/login'):
    raise RuntimeError('Login required: this is not evidence of the requested page')
cli('viewport', '--page', args.page, '--width', '1280', '--height', '900')
capture = cli('full-screenshot', '--page', args.page)
target = Path('docs/p11/screenshots') / args.name
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(capture['path'], target)
metadata = {'capturedAt': datetime.now(timezone.utc).isoformat(), 'url': actual_url,
            'file': target.name, 'method': 'Orca full-screenshot; original pixels'}
target.with_suffix('.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
print(json.dumps(metadata))
