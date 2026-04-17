"""Tests for backup_service — path traversal defense.

Verifies _validate_backup_path rejects any Backup.file_path that
escapes BACKUP_DIR, protecting delete_backup / restore_backup /
_cleanup_old_backups from tampered Backup records.
"""

from backend.models.system import Backup
from backend.services import backup_service
from backend.services.backup_service import (
    _validate_backup_path,
    delete_backup,
    restore_backup,
)


class TestValidateBackupPath:
    """Unit tests for the path validation guard."""

    def test_accepts_path_inside_backup_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        inside = tmp_path / "tracker_backup_20260411.db"
        inside.write_bytes(b"fake db")
        result = _validate_backup_path(str(inside))
        assert result is not None
        assert result == inside.resolve()

    def test_rejects_absolute_path_outside(self, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        # Try to escape upward
        outside = tmp_path.parent / "evil.db"
        assert _validate_backup_path(str(outside)) is None

    def test_rejects_root_system_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        # Classic attack: point at a system file
        assert _validate_backup_path("/etc/passwd") is None

    def test_rejects_parent_directory_traversal(self, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        sneaky = str(tmp_path) + "/../../../etc/passwd"
        # After resolve() this escapes BACKUP_DIR
        assert _validate_backup_path(sneaky) is None

    def test_rejects_unresolvable_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        # Null byte is illegal in paths on POSIX
        assert _validate_backup_path("\x00invalid") is None


class TestDeleteBackupSecurity:
    """Integration: delete_backup must refuse tampered records."""

    def test_delete_normal_backup_removes_file_and_record(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        good_file = tmp_path / "tracker_backup_good.db"
        good_file.write_bytes(b"fake db data")

        record = Backup(
            file_path=str(good_file),
            file_size=good_file.stat().st_size,
            backup_type="manual",
        )
        db_session.add(record)
        db_session.commit()
        rid = record.id

        assert delete_backup(db_session, rid) is True
        assert not good_file.exists(), "file should have been unlinked"
        assert db_session.query(Backup).filter_by(id=rid).first() is None

    def test_delete_tampered_backup_refuses_fs_op_but_removes_record(
        self, db_session, tmp_path, monkeypatch
    ):
        """A Backup row with file_path pointing outside BACKUP_DIR
        must NOT cause delete_backup to touch that path. The row
        itself should still be removed to restore DB consistency.
        """
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)

        # Create a canary file outside BACKUP_DIR that MUST survive
        canary = tmp_path.parent / "canary_do_not_delete.txt"
        canary.write_text("if this gets deleted, the security check failed")

        evil = Backup(
            file_path=str(canary),  # Tampered: outside BACKUP_DIR
            file_size=100,
            backup_type="manual",
        )
        db_session.add(evil)
        db_session.commit()
        eid = evil.id

        result = delete_backup(db_session, eid)
        assert result is False, "delete_backup must refuse tampered path"
        assert canary.exists(), "SECURITY FAIL: canary file was deleted. Path validation is broken."
        # Tampered record should still be removed from db
        assert db_session.query(Backup).filter_by(id=eid).first() is None
        # Cleanup canary
        canary.unlink()

    def test_delete_nonexistent_backup_returns_false(self, db_session):
        assert delete_backup(db_session, 99999) is False


class TestRestoreBackupSecurity:
    """Integration: restore_backup must refuse tampered records."""

    def test_restore_tampered_backup_returns_error(self, db_session, tmp_path, monkeypatch):
        monkeypatch.setattr(backup_service.settings, "BACKUP_DIR", tmp_path)
        # Canary file outside BACKUP_DIR that MUST NOT be read
        canary = tmp_path.parent / "canary_restore.txt"
        canary.write_text("never restore this to the live db")

        evil = Backup(
            file_path=str(canary),
            file_size=100,
            backup_type="manual",
        )
        db_session.add(evil)
        db_session.commit()

        result = restore_backup(db_session, evil.id)
        assert "error" in result
        assert "security" in result["error"].lower()
        # Canary still intact
        assert canary.exists()
        canary.unlink()

    def test_restore_nonexistent_backup_returns_error(self, db_session):
        result = restore_backup(db_session, 99999)
        assert "error" in result
