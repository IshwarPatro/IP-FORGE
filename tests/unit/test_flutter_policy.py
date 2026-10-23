import pytest
from pathlib import Path
from pydantic import ValidationError
from forge.flutter.policy import ReviewPolicy, load_policy


def test_default_policy():
    policy = ReviewPolicy()
    assert policy.schema_version == 1
    assert policy.required_checks == ["analyze", "unit_widget"]
    assert policy.fail_on == ["error"]
    assert policy.state_adapter == "unspecified"


def test_load_policy_from_yaml_file(tmp_path):
    config = tmp_path / ".ip-forge.yaml"
    config.write_text("""
schema_version: 1
flutter_root: .
platforms: [android, ios]
state_management:
  adapter: bloc
  exceptions: ["lib/legacy/"]
cache:
  policy: stale_while_revalidate
  requirements:
    account_scoped: true
    clear_private_data_on_logout: true
    max_age_seconds: 600
checks:
  analyze: required
  unit_widget: required
  web_build: optional
report:
  fail_on: [error, warning]
  fail_on_required_missing: true
""")

    policy = load_policy(config)
    assert policy.schema_version == 1
    assert policy.platforms == ["android", "ios"]
    assert policy.state_adapter == "bloc"
    assert policy.state_management.adapter == "bloc"
    assert policy.state_management.exceptions == ["lib/legacy/"]
    assert policy.cache.requirements.max_age_seconds == 600
    assert policy.required_checks == ["analyze", "unit_widget"]
    assert policy.fail_on == ["error", "warning"]


def test_load_policy_from_directory(tmp_path):
    # When directory has no .ip-forge.yaml, return default
    policy = load_policy(tmp_path)
    assert policy.required_checks == ["analyze", "unit_widget"]

    # When directory has .ip-forge.yaml, load it
    (tmp_path / ".ip-forge.yaml").write_text("""
schema_version: 1
state_management:
  adapter: riverpod
checks:
  analyze: required
""")
    loaded = load_policy(tmp_path)
    assert loaded.state_adapter == "riverpod"
    assert loaded.required_checks == ["analyze"]


def test_invalid_policy_keys_rejected(tmp_path):
    config = tmp_path / ".ip-forge.yaml"
    config.write_text("unknown_key: true\n")

    with pytest.raises(ValidationError):
        load_policy(config)
