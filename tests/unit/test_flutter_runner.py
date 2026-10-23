from pathlib import Path
from unittest.mock import MagicMock, patch
import subprocess
import pytest

from forge.flutter.policy import ReviewPolicy
from forge.flutter.runner import run_flutter_analyze, run_flutter_test, run_review


def test_analyze_parses_findings(tmp_path):
    output = """
Analyzing test_app...
  info • Avoid `print` calls in production code • lib/main.dart:10:5 • avoid_print
  warning • Unused import • lib/utils.dart:2:8 • unused_import
  error • Expected to find ';' • lib/bad.dart:5:1 • expected_token
3 issues found. (ran in 1.2s)
"""
    with patch("forge.flutter.runner.resolve_flutter_bin", return_value="/bin/flutter"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout=output, stderr="")
        res = run_flutter_analyze(tmp_path)

        assert res.name == "analyze"
        assert res.status == "failed"
        assert len(res.findings) == 3
        assert res.findings[0].rule_id == "avoid_print"
        assert res.findings[0].severity == "info"
        assert res.findings[0].line == 10
        assert res.findings[1].rule_id == "unused_import"
        assert res.findings[1].severity == "warning"
        assert res.findings[2].rule_id == "expected_token"
        assert res.findings[2].severity == "error"


def test_analyze_clean_pass(tmp_path):
    with patch("forge.flutter.runner.resolve_flutter_bin", return_value="/bin/flutter"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="No issues found! (ran in 0.8s)", stderr="")
        res = run_flutter_analyze(tmp_path)

        assert res.status == "passed"
        assert len(res.findings) == 0


def test_missing_flutter_bin_reports_unsupported(tmp_path):
    with patch("forge.flutter.runner.resolve_flutter_bin", return_value=None):
        res = run_flutter_analyze(tmp_path)
        assert res.status == "unsupported"
        assert "not found" in res.summary


def test_runner_on_non_flutter_workspace(tmp_path):
    report = run_review(tmp_path)
    assert len(report.checks) == 1
    assert report.checks[0].name == "detect"
    assert report.checks[0].status == "unsupported"


@pytest.mark.parametrize('settings', [
    {'cache': {}}, {'state_adapter': 'native'},
    {'flutter_root': 'app'}, {'platforms': ['web']},
    {'checks': {'analyze': 'optional'}},
    {'report': {'fail_on_required_missing': False}},
    {'flows': [{'id': 'login', 'test': 'integration_test/login.dart'}]},
])
def test_unsupported_policy_never_executes_or_passes(tmp_path, settings):
    policy = ReviewPolicy(**settings)
    with patch('forge.flutter.runner.run_flutter_analyze') as analyze:
        report = run_review(tmp_path, policy)
    analyze.assert_not_called()
    assert report.checks[0].name == 'policy_support'
    assert report.exit_code(policy) == 2


def test_test_alias_retains_required_check_identity(tmp_path):
    from forge.reports.models import CheckResult
    (tmp_path / 'pubspec.yaml').write_text('name: app\ndependencies:\n  flutter:\n    sdk: flutter\n')
    policy = ReviewPolicy(required_checks=['test'])
    with patch('forge.flutter.runner.run_flutter_test', return_value=CheckResult(
        name='unit_widget', status='passed', summary='Passed')):
        report = run_review(tmp_path, policy)
    assert report.exit_code(policy) == 0
    assert report.checks[0].name == 'test'
