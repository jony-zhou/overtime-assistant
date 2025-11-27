"""
清除開發環境中儲存的憑證
執行此腳本可清除 Windows Credential Manager 中儲存的帳號密碼
"""

import sys
from pathlib import Path
from src.services.credential_manager import CredentialManager

# 加入專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """清除儲存的憑證"""
    print("正在清除儲存的憑證...")

    credential_manager = CredentialManager()

    if credential_manager.has_saved_credentials():
        success = credential_manager.clear_credentials()
        if success:
            print("✓ 成功清除儲存的憑證")
        else:
            print("✗ 清除憑證失敗")
    else:
        print("ℹ 沒有找到儲存的憑證")

    print("\n完成!")


if __name__ == "__main__":
    main()
