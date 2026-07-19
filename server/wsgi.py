"""WSGI entry point for production (gunicorn). Unlike `python -m server.app`,
importing this module is what triggers init_db()/periodic backups here -
kept out of server/app.py's module scope so `pytest` importing server.app
during test collection never touches the real database (see
tests/conftest.py's sqlite_db fixture). See DEPLOYMENT.md."""

from server.app import _schedule_periodic_backups, app
from server.db import init_db

init_db()
_schedule_periodic_backups()

__all__ = ["app"]
