"""Simple DB migration runner for the captive portal.

Run this on the Pi or locally to ensure schema is up-to-date.
"""
from app import create_app
import db


def main():
    app = create_app({"MOCK_SENSOR": True})
    ok = db.migrate(app)
    if ok:
        print("Migration ran (tables ensured)")
    else:
        print("Migration no-op; provide an app to run migrations")


if __name__ == "__main__":
    main()
