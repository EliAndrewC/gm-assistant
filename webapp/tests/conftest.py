"""Shared pytest fixtures for the L7R Toolkit tests.

The `sample_pool` fixture points at a hand-crafted set of relic markdown
files under tests/fixtures/pool_sample/. Tests use this instead of mocking
filesystem calls — per Constitution Principle X.5, external boundaries are
tested with real fixture files, not transport-layer mocks.
"""

from pathlib import Path

import pytest


@pytest.fixture(scope='session')
def sample_pool_dir() -> Path:
    """Directory containing fixture relic files for tests."""
    return Path(__file__).parent / 'fixtures' / 'pool_sample'
