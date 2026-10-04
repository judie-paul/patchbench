from pathlib import Path

import pytest

from patchbench.loader import get_task
from patchbench.models import Task

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "tasks"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture()
def slug_task() -> Task:
    return get_task(FIXTURES, "patchbench__slugify-1")
