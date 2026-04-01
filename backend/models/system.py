"""系统表: 导入历史、备份"""

from sqlalchemy import Column, Integer, String, DateTime
from backend.models.base import Base, TimestampMixin


class ImportHistory(Base, TimestampMixin):
    __tablename__ = "import_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_type = Column(
        String, nullable=False
    )  # placement_csv, operation_log, search_term, migration
    file_name = Column(String)
    records_imported = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    status = Column(String, nullable=False, default="success")
    error_message = Column(String)


class Backup(Base, TimestampMixin):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    backup_type = Column(String, nullable=False, default="auto")  # auto, manual
