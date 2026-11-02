import pytest
from pydantic import ValidationError
from forge.flutter.policy import ReviewPolicy
from forge.reports.models import CheckResult, Finding, ReviewReport


@pytest.mark.parametrize('status', ['failed', 'not_run', 'unsupported', 'inconclusive', 'not_applicable', 'cancelled'])
def test_required_check_cannot_silently_pass(status):
    report = ReviewReport(workspace='fixture', checks=[CheckResult(name='analyze', status=status, summary='Evidence')])
    assert report.exit_code(ReviewPolicy(required_checks=['analyze'])) != 0


def test_missing_checks_are_not_success():
    assert ReviewReport(workspace='fixture').exit_code(ReviewPolicy()) == 2


def test_pass_requires_all_required_checks():
    report = ReviewReport(workspace='fixture', checks=[CheckResult(name=n, status='passed', summary='Executed') for n in ['analyze', 'unit_widget']])
    assert report.exit_code(ReviewPolicy()) == 0
    assert report.exit_code(ReviewPolicy(required_checks=['web_flows'])) == 2


def test_policy_severity_controls_advisory_gate():
    finding = Finding(rule_id='state.lifecycle', severity='warning', message='Review ownership', evidence='Controller reference', evidence_kind='static_inference')
    report = ReviewReport(workspace='fixture', checks=[CheckResult(name='review', status='passed', summary='Review complete', findings=[finding])])
    assert report.exit_code(ReviewPolicy(required_checks=['review'])) == 0
    assert report.exit_code(ReviewPolicy(required_checks=['review'], fail_on=['warning'])) == 1


def test_duplicate_results_and_unknown_configuration_rejected():
    check = CheckResult(name='analyze', status='passed', summary='Executed')
    with pytest.raises(ValidationError):
        ReviewReport(workspace='fixture', checks=[check, check])
    with pytest.raises(ValidationError):
        ReviewPolicy(allow_everything=True)
