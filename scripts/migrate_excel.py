"""
独立 Excel 迁移脚本
用法: cd amz-ad-tracker && python scripts/migrate_excel.py
"""

import sys
import asyncio
from pathlib import Path

# 确保能导入 backend 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import init_db, SessionLocal
from backend.services.migration_service import migrate_excel_to_db

EXCEL_PATH = Path(
    r"C:\Users\jackl\OneDrive\桌面\亚马逊广告智能追踪系统\亚马逊广告智能追踪系统_Ultimate.xlsx"
)


class FakeUploadFile:
    """模拟 FastAPI UploadFile 接口"""

    def __init__(self, path: Path):
        self.filename = path.name
        self._path = path

    async def read(self) -> bytes:
        return self._path.read_bytes()


async def main():
    if not EXCEL_PATH.exists():
        print(f"Excel 文件不存在: {EXCEL_PATH}")
        sys.exit(1)

    print("=" * 50)
    print("  Excel -> SQLite 数据迁移")
    print(f"  源文件: {EXCEL_PATH.name}")
    print("=" * 50)

    # 初始化数据库
    init_db()
    print("数据库已初始化")

    # 执行迁移
    db = SessionLocal()
    try:
        fake_file = FakeUploadFile(EXCEL_PATH)
        result = await migrate_excel_to_db(db, fake_file)

        print("\n--- 迁移结果 ---")
        for detail in result.details:
            level_tag = f"[{detail.level.upper()}]" if detail.level != "info" else ""
            print(f"  {level_tag} {detail.message}")

        print(f"\n总计迁移: {result.imported} 条记录")
        if result.errors > 0:
            print(f"错误数: {result.errors}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
