import time
import sys
import pathlib
import pytest

# Ensure tests can import the application when pytest's working directory
# is the repository root or another location: prepend project root to sys.path.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "MOCK_SENSOR": True, "DRY_RUN": True, "USE_IPTABLES": False, "SESSION_DURATION": 5})
    return app


def test_create_and_start_session(tmp_path, app):
    with app.app_context():
        sm = app.extensions["session_manager"]
        ac = app.extensions["access_controller"]
        # create session for a sample IP
        sid = sm.create("10.0.0.55", mac="aa:bb:cc:dd:ee:ff")
        assert sid is not None
        st = sm.status(sid)
        assert st["status"] in ("waiting", "not_found") or st["status"] == "waiting"

        # start session (should grant via in-memory controller)
        ok = sm.start_for(sid)
        assert ok
        # Access controller should report allowed
        assert ac.is_allowed("10.0.0.55") is True
