# 版本管理最佳實踐

## 單一真實來源 (Single Source of Truth)

### 設計理念

我們採用 **單一真實來源 (SSOT)** 原則來管理版本號,所有版本資訊都集中在一個地方管理,避免多處維護導致的不一致問題。

---

## 版本號的唯一定義位置

### 📍 版本號定義於:

```python
# src/core/version.py
VERSION = "1.0.1"
VERSION_NAME = "修正打包檔名"
```

**這是專案中唯一需要手動修改版本號的地方!**

---

## 自動化版本傳播

### 1. PyInstaller 封裝檔名 (動態讀取)

```python
# overtime_calculator.spec
import sys
import os
sys.path.insert(0, os.path.dirname(SPEC))
from src.core.version import VERSION

exe = EXE(
    ...
    name=f'overtime-assistant-{VERSION}',  # 動態生成檔名
    ...
)
```

**優點**:
- ✅ 自動同步版本號
- ✅ 無需手動修改 spec 檔案
- ✅ 減少人為錯誤
- ✅ 單一修改點

---

### 2. 應用程式內部版本檢查

```python
# src/core/version.py
def get_current_version() -> Version:
    """取得當前應用程式版本"""
    return Version.from_string(VERSION)
```

**用途**:
- 版本比較邏輯
- 更新檢查功能
- UI 顯示當前版本

---

### 3. 文件與 README

```markdown
# readme.md
## 版本資訊

- **當前版本**: v1.0.1
- **更新日期**: 2025-11-21
```

**建議**: 文件中的版本號可在發布時手動更新,或使用自動化腳本同步。

---

## 版本更新流程

### 當需要發布新版本時:

#### Step 1: 修改版本號 (唯一修改點)

```python
# src/core/version.py
VERSION = "1.0.2"  # 舊版: "1.0.1"
VERSION_NAME = "新功能說明"
```

#### Step 2: 重新封裝 (自動使用新版本)

```powershell
python -m PyInstaller overtime_calculator.spec --clean --noconfirm
```

**結果**: 自動生成 `overtime-assistant-1.0.2.exe`

#### Step 3: 測試版本號

```python
# 測試動態版本名稱
python -c "import sys; sys.path.insert(0, '.'); from src.core.version import VERSION; print(f'overtime-assistant-{VERSION}')"
```

#### Step 4: 更新 README 和文件 (可選)

```markdown
- **當前版本**: v1.0.2
- **更新日期**: 2025-11-21
```

---

## 版本規範 (Semantic Versioning)

### 格式: `X.Y.Z`

- **X (主版本號)**: 不相容的 API 修改
- **Y (次版本號)**: 向下相容的功能性新增
- **Z (修訂號)**: 向下相容的問題修正

### 範例:

| 變更類型 | 舊版本 | 新版本 | 說明 |
|---------|--------|--------|------|
| 修訂 (Patch) | 1.0.1 | 1.0.2 | Bug 修正、小改進 |
| 次版本 (Minor) | 1.0.2 | 1.1.0 | 新增功能,向下相容 |
| 主版本 (Major) | 1.1.0 | 2.0.0 | 重大變更,不相容 |

---

## 常見問題

### Q1: 為什麼不直接在 spec 檔案中寫死版本號?

**問題**: 需要同時修改 `version.py` 和 `overtime_calculator.spec` 兩處
```python
# ❌ 不好的做法 (需要修改兩處)
# src/core/version.py
VERSION = "1.0.2"

# overtime_calculator.spec
name='overtime-assistant-1.0.2'  # 容易忘記同步!
```

**解決方案**: 動態讀取版本號
```python
# ✅ 最佳實踐 (只修改一處)
# src/core/version.py
VERSION = "1.0.2"

# overtime_calculator.spec
from src.core.version import VERSION
name=f'overtime-assistant-{VERSION}'  # 自動同步!
```

---

### Q2: spec 檔案可以執行 Python 程式碼嗎?

**答案**: 可以! 

PyInstaller 的 spec 檔案本身就是 **可執行的 Python 程式碼**。官方文件明確說明:

> "The spec file is actually executable Python code. PyInstaller builds the app by executing the contents of the spec file."

因此我們可以:
- ✅ 匯入模組: `from src.core.version import VERSION`
- ✅ 使用變數: `name=f'overtime-assistant-{VERSION}'`
- ✅ 執行邏輯: `if/else`, `for` 迴圈等
- ✅ 動態計算: 路徑處理、條件判斷等

---

### Q3: 這樣做會影響效能嗎?

**答案**: 不會!

- 版本號在 **建置時** 讀取,不是 **執行時**
- 對最終執行檔的效能 **零影響**
- 只是改變了建置過程,不影響執行邏輯

---

### Q4: 如果忘記更新版本號會怎樣?

**影響範圍**:
- ❌ 封裝檔名不會更新 (仍是舊版本號)
- ❌ 應用程式內顯示的版本不正確
- ❌ 版本檢查功能會誤判

**解決方案**:
1. 在 release checklist 中加入版本號檢查
2. 使用 CI/CD 自動化驗證
3. 建立 pre-commit hook 提醒

---

## 技術細節

### spec 檔案的版本讀取機制

```python
# -*- mode: python ; coding: utf-8 -*-

# 1. 將 spec 檔案所在目錄加入 Python 搜尋路徑
import sys
import os
sys.path.insert(0, os.path.dirname(SPEC))
# SPEC 是 PyInstaller 提供的全域變數,指向 spec 檔案路徑

# 2. 匯入版本模組
from src.core.version import VERSION

# 3. 在 EXE 定義中使用動態版本
exe = EXE(
    ...
    name=f'overtime-assistant-{VERSION}',
    ...
)
```

### 為什麼需要 `sys.path.insert`?

因為 spec 檔案執行時,Python 搜尋路徑可能不包含專案根目錄,導致無法找到 `src.core.version` 模組。透過 `sys.path.insert(0, os.path.dirname(SPEC))` 確保可以正確匯入。

---

## 版本發布檢查清單

### 發布前檢查

- [x] 修改 `src/core/version.py` 中的 `VERSION`
- [x] 修改 `src/core/version.py` 中的 `VERSION_NAME`
- [x] 執行單元測試: `pytest`
- [x] 驗證版本號: `python -c "from src.core.version import VERSION; print(VERSION)"`
- [x] 重新封裝: `python -m PyInstaller overtime_calculator.spec --clean`
- [x] 檢查封裝檔名: `Get-ChildItem dist/*.exe`
- [x] 測試執行檔功能
- [x] 更新 `readme.md`
- [x] 建立 Release Notes
- [x] 建立 Git Tag: `git tag v{VERSION}`
- [x] 推送到 GitHub: `git push origin v{VERSION}`
- [x] 建立 GitHub Release 並上傳 exe

---

## 自動化建議

### 未來可以考慮的自動化:

1. **Pre-commit Hook**: 檢查版本號是否已更新
2. **CI/CD Pipeline**: 自動化建置和發布流程
3. **版本號自動遞增**: 使用工具如 `bumpversion`
4. **Changelog 自動生成**: 基於 Git commit 訊息

---

## 總結

### 最佳實踐要點:

1. ✅ **單一真實來源**: 版本號只在 `src/core/version.py` 定義
2. ✅ **動態讀取**: spec 檔案透過 import 動態讀取版本號
3. ✅ **語義化版本**: 遵循 Semver 2.0.0 規範
4. ✅ **自動化**: 減少手動操作,降低錯誤率
5. ✅ **可追溯性**: 版本歷史與 Git Tag 對應

### 這就是最佳實踐! 🎯

透過動態版本管理,我們實現了:
- **降低維護成本**: 單一修改點
- **減少人為錯誤**: 自動同步版本號
- **提升開發效率**: 不用記住要改幾個地方
- **符合業界標準**: DRY (Don't Repeat Yourself) 原則

---

**版本管理文件版本**: v1.0
**最後更新**: 2025-11-21
