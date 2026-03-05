#!/usr/bin/env python3
"""
TECO SSP 加班時數計算器 v1.0.0
GUI 應用程式入口
"""

import argparse
from src.utils import setup_logging
from ui import MainWindow


def main():
    """主程式入口"""
    # 解析命令列參數
    parser = argparse.ArgumentParser(description="TECO SSP 加班助手")
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="測試模式 (使用假數據，不連線)",
    )
    args = parser.parse_args()

    # 設定日誌
    setup_logging()

    # 啟動 GUI (傳入測試模式標誌)
    app = MainWindow(test_mode=args.test)
    app.mainloop()


if __name__ == "__main__":
    main()
