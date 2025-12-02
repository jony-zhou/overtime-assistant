"""移除所有 Python 檔案的 trailing whitespace"""

import pathlib


def fix_trailing_whitespace(file_path):
    """修復檔案的 trailing whitespace"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 移除每行的 trailing whitespace
        fixed_lines = [line.rstrip() + "\n" for line in lines]

        # 確保檔案以單一換行結尾
        if fixed_lines and fixed_lines[-1] != "\n":
            fixed_lines[-1] = fixed_lines[-1].rstrip() + "\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        print(f"✓ 已修復: {file_path}")
        return True
    except Exception as e:
        print(f"✗ 錯誤 {file_path}: {e}")
        return False


if __name__ == "__main__":
    src_files = list(pathlib.Path("src").rglob("*.py"))
    ui_files = list(pathlib.Path("ui").rglob("*.py"))
    test_files = list(pathlib.Path("tests").rglob("*.py"))

    all_files = src_files + ui_files + test_files

    success_count = 0
    for file_path in all_files:
        if file_path.is_file():
            if fix_trailing_whitespace(file_path):
                success_count += 1

    print(f"\n總計: {success_count}/{len(all_files)} 個檔案已修復")
