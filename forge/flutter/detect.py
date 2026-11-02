"""
IP FORGE: Flutter Project Detection and Introspection.
Locates pubspec.yaml, analyzes dependencies, platforms, and state management setups.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, ConfigDict, Field


class FlutterProjectInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root: str
    is_flutter: bool = False
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    dart_sdk: Optional[str] = None
    flutter_sdk: Optional[str] = None
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    dev_dependencies: Dict[str, Any] = Field(default_factory=dict)
    state_packages: List[str] = Field(default_factory=list)
    primary_state_adapter: str = "native"
    cache_packages: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    has_tests: bool = False
    test_files: List[str] = Field(default_factory=list)
    has_analysis_options: bool = False
    has_lockfile: bool = False
    error: Optional[str] = None


KNOWN_STATE_PACKAGES = {
    "flutter_riverpod": "riverpod",
    "riverpod": "riverpod",
    "hooks_riverpod": "riverpod",
    "flutter_bloc": "bloc",
    "bloc": "bloc",
    "provider": "provider",
    "get": "getx",
    "mobx": "mobx",
    "flutter_mobx": "mobx",
    "signals": "signals",
}

KNOWN_CACHE_PACKAGES = [
    "shared_preferences",
    "hive",
    "hive_flutter",
    "isar",
    "sqflite",
    "hydrated_bloc",
    "flutter_cache_manager",
    "dio_cache_interceptor",
]

SUPPORTED_PLATFORMS = ["android", "ios", "web", "macos", "windows", "linux"]


def detect_flutter_project(root_path: Path | str) -> FlutterProjectInfo:
    """
    Introspects a directory for a Flutter/Dart project without modifying any files.
    """
    root = Path(root_path).resolve()
    pubspec_path = root / "pubspec.yaml"

    if not root.exists() or not root.is_dir():
        return FlutterProjectInfo(root=str(root), is_flutter=False, error=f"Directory does not exist: {root}")

    if not pubspec_path.exists():
        return FlutterProjectInfo(root=str(root), is_flutter=False, error=f"Missing pubspec.yaml in: {root}")

    try:
        content = pubspec_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}
    except Exception as exc:
        return FlutterProjectInfo(root=str(root), is_flutter=False, error=f"Failed to parse pubspec.yaml: {exc}")

    name = data.get("name")
    version = str(data.get("version")) if data.get("version") is not None else None
    description = data.get("description")

    env = data.get("environment") or {}
    dart_sdk = env.get("sdk")
    flutter_sdk = env.get("flutter")

    deps = data.get("dependencies") or {}
    dev_deps = data.get("dev_dependencies") or {}

    # Check if this is a Flutter project (not just a pure Dart package)
    is_flutter = (
        "flutter" in data
        or "flutter" in deps
        or "flutter_test" in dev_deps
        or flutter_sdk is not None
    )

    # Detect state management
    state_packages = []
    primary_adapter = "native"
    all_deps = {**deps, **dev_deps}
    for pkg, adapter in KNOWN_STATE_PACKAGES.items():
        if pkg in all_deps:
            state_packages.append(pkg)
            if primary_adapter == "native":
                primary_adapter = adapter

    # Detect cache packages
    cache_packages = [pkg for pkg in KNOWN_CACHE_PACKAGES if pkg in all_deps]

    # Detect platforms
    platforms = [p for p in SUPPORTED_PLATFORMS if (root / p).is_dir()]

    # Detect entry points
    entry_points = []
    lib_dir = root / "lib"
    if lib_dir.is_dir():
        for candidate in ["main.dart", "app.dart"]:
            if (lib_dir / candidate).is_file():
                entry_points.append(f"lib/{candidate}")

    # Detect tests
    test_dir = root / "test"
    test_files = []
    if test_dir.is_dir():
        test_files = [str(p.relative_to(root)) for p in test_dir.rglob("*_test.dart")]
    has_tests = len(test_files) > 0

    has_analysis_options = (root / "analysis_options.yaml").is_file()
    has_lockfile = (root / "pubspec.lock").is_file()

    return FlutterProjectInfo(
        root=str(root),
        is_flutter=is_flutter,
        name=name,
        version=version,
        description=description,
        dart_sdk=dart_sdk,
        flutter_sdk=flutter_sdk,
        dependencies=deps if isinstance(deps, dict) else {},
        dev_dependencies=dev_deps if isinstance(dev_deps, dict) else {},
        state_packages=state_packages,
        primary_state_adapter=primary_adapter,
        cache_packages=cache_packages,
        platforms=platforms,
        entry_points=entry_points,
        has_tests=has_tests,
        test_files=test_files,
        has_analysis_options=has_analysis_options,
        has_lockfile=has_lockfile,
    )
