"""Keep the legacy test suite away from the developer's checkout and providers."""
from pathlib import Path
import shutil

import pytest


def pytest_addoption(parser):
    parser.addoption('--run-rag', action='store_true', help='Run legacy embedding integration tests (may download a model).')


def pytest_collection_modifyitems(config, items):
    if config.getoption('--run-rag'):
        return
    for item in items:
        if item.path.name in {'test_rag.py', 'test_planner.py'}:
            item.add_marker(pytest.mark.skip(reason='Legacy embedding integration: opt in with --run-rag'))


@pytest.fixture(scope='session', autouse=True)
def isolated_legacy_environment(tmp_path_factory):
    from forge.config import settings
    from forge.llm.factory import LLMClient

    source = Path(__file__).resolve().parent
    sandbox = tmp_path_factory.mktemp('forge-suite')
    shutil.copytree(source / 'dummy_repo', sandbox / 'tests' / 'dummy_repo')
    with pytest.MonkeyPatch.context() as patch:
        patch.chdir(sandbox)
        patch.setenv('PYTHONPATH', str(sandbox))
        patch.setattr(settings, 'TARGET_REPO_PATH', str(sandbox / 'tests' / 'dummy_repo'))
        patch.setattr(settings, 'CHROMA_PERSIST_DIR', str(sandbox / 'chroma'))
        patch.setattr(LLMClient, 'is_healthy', lambda self: False)
        yield
