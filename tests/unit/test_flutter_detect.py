from pathlib import Path
import pytest
from forge.flutter.detect import detect_flutter_project

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_detect_fixture_app():
    fixture_path = REPO_ROOT / "examples/flutter_fixture"
    info = detect_flutter_project(fixture_path)

    assert info.is_flutter is True
    assert info.name == "forge_flutter_fixture"
    assert info.version == "0.0.1"
    assert info.dart_sdk == ">=3.5.0 <4.0.0"
    assert info.primary_state_adapter == "native"
    assert info.has_tests is True
    assert len(info.test_files) >= 1
    assert "lib/main.dart" in info.entry_points
    assert info.has_lockfile is True


def test_detect_non_existent_directory(tmp_path):
    missing_dir = tmp_path / "does_not_exist"
    info = detect_flutter_project(missing_dir)

    assert info.is_flutter is False
    assert "Directory does not exist" in (info.error or "")


def test_detect_non_flutter_directory(tmp_path):
    # Directory with no pubspec.yaml
    info = detect_flutter_project(tmp_path)

    assert info.is_flutter is False
    assert "Missing pubspec.yaml" in (info.error or "")


def test_detect_custom_state_management(tmp_path):
    pubspec = tmp_path / "pubspec.yaml"
    pubspec.write_text("""
name: riverpod_test_app
environment:
  sdk: '>=3.0.0 <4.0.0'
dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^2.5.1
  shared_preferences: ^2.2.0
""")
    info = detect_flutter_project(tmp_path)

    assert info.is_flutter is True
    assert info.name == "riverpod_test_app"
    assert info.primary_state_adapter == "riverpod"
    assert "flutter_riverpod" in info.state_packages
    assert "shared_preferences" in info.cache_packages
