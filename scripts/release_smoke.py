"""Exercise the installed wheel via CLI and an independent SDK stdio client."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def check(root, execution):
    args = ['-m', 'forge.cli', 'mcp', '--workspace', str(root)]
    if execution:
        args.append('--allow-execution')
    params = StdioServerParameters(command=sys.executable, args=args, env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            names = {t.name for t in (await client.list_tools()).tools}
            expected = {'inspect_flutter_project', 'get_flutter_report'}
            if execution:
                expected.add('run_flutter_checks')
            assert names == expected, names
            result = await client.call_tool('inspect_flutter_project', {'directory': '.'})
            assert not result.isError, result
            assert json.loads(result.content[0].text)['is_flutter']
            denied = await client.call_tool('inspect_flutter_project', {'directory': '..'})
            assert denied.isError
            invalid = await client.call_tool('inspect_flutter_project', {'directory': 123})
            assert invalid.isError
            await client.send_ping()
            missing = await client.call_tool('get_flutter_report', {})
            assert missing.isError
            if execution:
                # Unsupported check proves failure reports survive without an installed Flutter SDK.
                run = await client.call_tool('run_flutter_checks', {})
                assert run.isError
                cached = await client.call_tool('get_flutter_report', {})
                assert cached.isError and cached.content == run.content


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'pubspec.yaml').write_text('name: smoke_app\ndependencies:\n  flutter:\n    sdk: flutter\n')
        (root / '.ip-forge.yaml').write_text('required_checks: [unsupported_smoke_check]\n')
        subprocess.run([sys.executable, '-m', 'forge.cli', 'inspect', str(root)], cwd=root, check=True)
        result = subprocess.run([sys.executable, '-m', 'forge.cli', 'check', str(root), '--json'], cwd=root, capture_output=True, text=True)
        assert result.returncode == 2, result.stderr
        assert json.loads(result.stdout)['checks'][0]['status'] == 'unsupported'
        frames = [
            {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
                'protocolVersion': '2024-11-05', 'capabilities': {},
                'clientInfo': {'name': 'raw-smoke', 'version': '1'}}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
        ]
        raw = subprocess.run([sys.executable, '-m', 'forge.cli', 'mcp', '--workspace', str(root)],
            cwd=root, input=''.join(json.dumps(f) + '\n' for f in frames),
            capture_output=True, text=True, timeout=30)
        assert raw.returncode == 0, raw.stderr
        parsed = [json.loads(line) for line in raw.stdout.splitlines()]
        assert {r['id'] for r in parsed} == {1, 2}, parsed
        previous = Path.cwd()
        os.chdir(root)
        try:
            asyncio.run(check(root, False))
            asyncio.run(check(root, True))
        finally:
            os.chdir(previous)
    print('Installed CLI and SDK protocol smoke checks passed.')


if __name__ == '__main__':
    main()
