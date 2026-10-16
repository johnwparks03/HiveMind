"""app/settings.py (key/value store) and app/api/routes_settings.py's
download-folder endpoints: letting the user choose where teammate downloads land
instead of always the real Windows Downloads folder.
"""
import pytest

from app import settings
from app.central import download


def test_get_is_none_when_unset(isolated_store):
    assert settings.get("download_folder") is None


def test_set_then_get_round_trips(isolated_store):
    settings.set("download_folder", "C:/x")
    assert settings.get("download_folder") == "C:/x"


def test_set_overwrites_the_existing_value(isolated_store):
    settings.set("download_folder", "C:/x")
    settings.set("download_folder", "C:/y")
    assert settings.get("download_folder") == "C:/y"


def test_clear_removes_it(isolated_store):
    settings.set("download_folder", "C:/x")
    settings.clear("download_folder")
    assert settings.get("download_folder") is None


def test_downloads_folder_uses_the_real_default_when_unset(isolated_store, monkeypatch):
    monkeypatch.setattr(download, "_real_downloads_folder", lambda: "REAL_DOWNLOADS")
    assert str(download.downloads_folder()) == "REAL_DOWNLOADS"


def test_downloads_folder_uses_the_custom_setting_when_set(isolated_store, tmp_path):
    settings.set(settings.DOWNLOAD_FOLDER_KEY, str(tmp_path))
    assert download.downloads_folder() == tmp_path


@pytest.fixture
def local_db(tmp_path, monkeypatch):
    import app.db as db
    monkeypatch.setattr(db, "SQLITE_PATH", tmp_path / "registry.db")
    db.init_db()
    return db


def test_get_download_folder_route_defaults_to_the_real_one(client, auth, local_db, monkeypatch):
    monkeypatch.setattr(download, "_real_downloads_folder", lambda: "REAL_DOWNLOADS")
    resp = client.get("/settings/download-folder", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["path"] == "REAL_DOWNLOADS"


def test_put_download_folder_requires_an_existing_directory(client, auth, local_db):
    resp = client.put("/settings/download-folder", headers=auth, json={"path": "C:/does/not/exist"})
    assert resp.status_code == 400


def test_put_then_get_download_folder(client, auth, local_db, tmp_path):
    resp = client.put("/settings/download-folder", headers=auth, json={"path": str(tmp_path)})
    assert resp.status_code == 200
    assert resp.json()["path"] == str(tmp_path)
    assert client.get("/settings/download-folder", headers=auth).json()["path"] == str(tmp_path)


def test_delete_resets_to_the_default(client, auth, local_db, tmp_path, monkeypatch):
    client.put("/settings/download-folder", headers=auth, json={"path": str(tmp_path)})
    monkeypatch.setattr(download, "_real_downloads_folder", lambda: "REAL_DOWNLOADS")
    assert client.delete("/settings/download-folder", headers=auth).status_code == 204
    assert client.get("/settings/download-folder", headers=auth).json()["path"] == "REAL_DOWNLOADS"
