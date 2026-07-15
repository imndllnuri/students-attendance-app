import server.db as db


def test_backup_database_returns_none_when_no_db_file_yet(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "missing.db")

    assert db.backup_database(backup_dir=tmp_path / "backups") is None


def test_backup_database_copies_the_db_file(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db()
    backup_dir = tmp_path / "backups"

    backup_path = db.backup_database(backup_dir=backup_dir)

    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.parent == backup_dir
    assert backup_path.read_bytes() == db_path.read_bytes()


def test_backup_database_prunes_old_backups_beyond_retention(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db()
    backup_dir = tmp_path / "backups"

    for i in range(5):
        backup_dir.mkdir(parents=True, exist_ok=True)
        stub = backup_dir / f"test-2025010{i}T000000Z.db"
        stub.write_bytes(b"old backup")

    db.backup_database(backup_dir=backup_dir, retention=3)

    remaining = sorted(backup_dir.glob("test-*.db"))
    assert len(remaining) == 3
