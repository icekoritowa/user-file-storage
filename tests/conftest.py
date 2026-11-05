import os

import pytest
from io import StringIO

from db.database import ROOT


@pytest.fixture(scope="module")
def orm_database():
    django = pytest.importorskip("django")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "storage_web.settings")
    django.setup()
    from django.test.utils import setup_databases, teardown_databases
    config = setup_databases(verbosity=0, interactive=False)
    yield
    teardown_databases(config, verbosity=0)


@pytest.fixture
def web(orm_database):
    from django.core.management import call_command
    from django.test import Client, override_settings
    call_command("flush", verbosity=0, interactive=False)
    call_command("import_legacy", source=ROOT / "data/storage.sqlite",
                 stdout=StringIO())
    with override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False):
        yield Client()
