import os
import shutil
import sys
from pathlib import Path

# Must run before anything imports app.indexing.embeddings, which reads this at import time.
# Real-model tests opt in with HIVEMIND_TEST_REAL_EMBEDDINGS=1 (see test_search_quality.py).
if os.environ.get("HIVEMIND_TEST_REAL_EMBEDDINGS") != "1":
    os.environ["HIVEMIND_FAKE_EMBEDDINGS"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent))

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.db as db  # noqa: E402
from app import config  # noqa: E402
from app.auth import keystore, session  # noqa: E402
from app.auth.security import STARTUP_TOKEN  # noqa: E402
from app.indexing import vector_store  # noqa: E402
from app.main import app  # noqa: E402
from corpus_generator import generate  # noqa: E402


class FakeKeyring:
    def __init__(self):
        self.store = {}
        self.broken = False
        self.max_len = None  # simulate Credential Manager's blob size limit

    def _check(self):
        if self.broken:
            raise RuntimeError("keychain unavailable")

    def set_password(self, service, user, value):
        self._check()
        if self.max_len is not None and len(value) > self.max_len:
            raise RuntimeError("credential too large")
        self.store[(service, user)] = value

    def get_password(self, service, user):
        self._check()
        return self.store.get((service, user))

    def delete_password(self, service, user):
        self._check()
        self.store.pop((service, user), None)


class FakeCognito:
    """Stands in for httpx.post in app.auth.cognito. Records calls; replies per target."""

    def __init__(self):
        self.calls = []
        self.error = {}  # target -> (status, exception type, message)
        self.expires_in = 3600

    def __call__(self, url, json=None, headers=None, timeout=None):
        target = headers["X-Amz-Target"].rsplit(".", 1)[-1]
        self.calls.append((target, json))
        if target in self.error:
            status, kind, message = self.error[target]
            return httpx.Response(status, json={"__type": kind, "message": message})
        if target == "SignUp":
            return httpx.Response(200, json={"UserConfirmed": True})
        result = {"AccessToken": f"access-{len(self.calls)}", "IdToken": "id", "ExpiresIn": self.expires_in}
        if json["AuthFlow"] == "USER_PASSWORD_AUTH":
            result["RefreshToken"] = "refresh-1"
        return httpx.Response(200, json={"AuthenticationResult": result})


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(config, "COGNITO_CLIENT_ID", "test-client")
    monkeypatch.setattr(config, "CENTRAL_API_URL", "https://central.test")
    monkeypatch.setattr(config, "CENTRAL_HEALTH_CACHE_SECONDS", 0)
    yield
    session._email = session._refresh_token = session._access_token = None
    session._expires_at = 0.0
    keystore._memory.clear()
    keystore.persistent = True


@pytest.fixture
def keyring_fake(monkeypatch):
    fake = FakeKeyring()
    monkeypatch.setattr(keystore, "keyring", fake)
    return fake


@pytest.fixture
def cognito_fake(monkeypatch):
    fake = FakeCognito()
    monkeypatch.setattr("app.auth.cognito.httpx.post", fake)
    return fake


@pytest.fixture
def client():
    # No `with`: skips the lifespan (DB init and keychain restore).
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth():
    return {"X-HiveMind-Token": STARTUP_TOKEN}


# --- Corpus and isolated storage (indexing and search tests) ----------------------------


@pytest.fixture(scope="session")
def corpus_template(tmp_path_factory):
    """The 83-file corpus, generated once per test run. Tests copy it before mutating."""
    root = tmp_path_factory.mktemp("corpus_template") / "corpus"
    written = generate(root)
    return root, written


@pytest.fixture
def corpus(tmp_path, corpus_template):
    """A fresh copy of the corpus for one test. Returns (root, intended mtimes)."""
    template_root, written = corpus_template
    root = tmp_path / "corpus"
    shutil.copytree(template_root, root)
    # Map each generated path onto the copy so tests can refer to files by the same names.
    relative = [(p.relative_to(template_root), when) for p, when in written]
    return root, [(root / rel, when) for rel, when in relative]


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Points the SQLite registry and Chroma store at a temp dir for this test only."""
    monkeypatch.setattr(db, "SQLITE_PATH", tmp_path / "registry.db")
    monkeypatch.setattr(vector_store, "CHROMA_PATH", tmp_path / "chroma")
    vector_store.get_collection.cache_clear()
    db.init_db()
    yield tmp_path
    vector_store.get_collection.cache_clear()
