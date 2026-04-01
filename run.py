"""
亚马逊广告智能追踪系统 - 一键启动入口
用法: python run.py
"""

import os
import subprocess
import sys
import webbrowser
import time
from pathlib import Path

PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "127.0.0.1")


def main():
    # 确保 data 目录存在
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "backups").mkdir(exist_ok=True)

    print("=" * 50)
    print("  亚马逊广告智能追踪系统")
    print(f"  启动中... http://{HOST}:{PORT}")
    print("=" * 50)

    # 延迟打开浏览器
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://{HOST}:{PORT}")

    import threading

    threading.Thread(target=open_browser, daemon=True).start()

    # 启动 FastAPI
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
            "--reload",
        ]
    )


if __name__ == "__main__":
    main()
