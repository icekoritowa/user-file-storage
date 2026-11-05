import sqlite3

import pytest

from db.database import ROOT, connect, load_database
from db.import_json import import_json


@pytest.fixture
def database(tmp_path):
    path = tmp_path / 'storage.sqlite'
    import_json(ROOT / 'data/example.json', path)
    return path


def test_import_repeat_and_foreign_keys(database):
    import_json(ROOT / 'data/example.json', database)
    assert len(load_database(database)['files']) == 2
    with connect(database) as connection:
        assert connection.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                'INSERT INTO folders VALUES (?, ?, ?)', (99, 'x', 999))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                'INSERT INTO users VALUES (?, ?, ?, ?)', (99, 'x', -1, None))


def test_invalid_import_preserves_database(database, tmp_path):
    source = tmp_path / 'bad.json'
    source.write_text('{broken')
    before = database.read_bytes()
    with pytest.raises(ValueError):
        import_json(source, database)
    assert database.read_bytes() == before


def test_sql_pages(database):
    pytest.importorskip('django')
    from django.test import Client, override_settings
    with override_settings(STORAGE_DATABASE=database,
                           ALLOWED_HOSTS=['testserver']):
        client = Client()
        for url in ['/', '/folders/', '/folders/1/', '/files/', '/files/1/',
                    '/accesses/', '/accesses/1/2/', '/statistics/']:
            assert client.get(url).status_code == 200
        response = client.get('/statistics/', {'q': "' OR 1=1 --"})
        assert response.status_code == 200
        assert 'Нет данных' in response.content.decode()
        for params in [{'size': '-1'}, {'date': 'bad'}, {'offset': 'abc'}]:
            assert client.get('/statistics/', params).status_code == 400
        with connect(database) as connection:
            with connection:
                connection.execute('UPDATE files SET name=? WHERE id=1',
                                   ('changed.txt',))
        assert 'changed.txt' in client.get('/files/').content.decode()
        database.unlink()
        assert client.get('/files/').status_code == 503
        assert client.get('/statistics/').status_code == 503
