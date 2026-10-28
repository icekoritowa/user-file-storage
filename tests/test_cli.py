import subprocess
import sys
from pathlib import Path

from file_storage import cli
from file_storage.persistence import load_catalog


def run_cli(path, commands):
    project = Path(__file__).resolve().parents[1]
    return subprocess.run(
        [sys.executable, str(project / "main.py"), "--data", str(path)],
        input="\n".join(commands) + "\n", capture_output=True,
        text=True, check=True,
    ).stdout


def test_every_menu_item_and_restart(tmp_path):
    path = tmp_path / "catalog.json"
    output = run_cli(path, [
        "2", "ilya", "100", "2", "guest", "50", "1",
        "5", "Учеба", "4", "7", "1", "a.txt", "80",
        "6", "", "", "", "10", "11", "add_file",
        "9", "1", "2", "read", "3", "2", "6", "a", "80", "size",
        "7", "1", "denied", "1", "3", "1", "8", "1", "0",
    ])
    assert "Ошибка: Нет права записи" in output
    assert "Занято 80 из 100" in output
    assert "add_file(data:" in output
    data = load_catalog(path)
    assert len(data["users"]) == 2
    assert len(data["folders"]) == 1
    assert data["files"] == []
    assert data["accesses"][0].level == "read"
    output = run_cli(path, ["1", "4", "6", "", "", "", "0"])
    assert "ilya" in output and "Учеба" in output
    assert "Ничего не найдено" in output


def test_invalid_inputs_and_eof(tmp_path):
    output = run_cli(tmp_path / "catalog.json", [
        "wrong", "2", "ilya", "letter", "2", "ilya", "100",
        "3", "999", "5", "Учеба", "7", "999", "a", "1",
        "7", "1", "a", "-1", "6", "", "bad", "name",
    ])
    assert output.count("Ошибка:") >= 6
    assert "Завершение работы" in output
    assert "Traceback" not in output


def test_corrupt_file_not_overwritten(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text("broken")
    output = run_cli(path, ["2", "ilya", "100"])
    assert "Ошибка загрузки" in output
    assert path.read_text() == "broken"


def test_failed_save_does_not_change_memory(tmp_path, monkeypatch, capsys):
    answers = iter(["2", "ilya", "100", "1", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    def fail(*args):
        raise OSError("Диск недоступен")

    monkeypatch.setattr(cli, "save_catalog", fail)
    cli.run(tmp_path / "catalog.json")
    output = capsys.readouterr().out
    assert "Диск недоступен" in output
    assert "Ничего не найдено" in output
