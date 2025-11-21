# 版本更新說明

## 自動更新檢查功能

### 功能說明

從 v1.0.0 開始,應用程式支援自動檢查更新功能:

1. **啟動時自動檢查**: 程式啟動後約 1 秒會在背景檢查 GitHub 是否有新版本
2. **非侵入式通知**: 檢查過程不會干擾正常使用,失敗也不影響主程式
3. **智慧快取**: 6 小時內不重複檢查,減少 API 請求
4. **安全下載**: 提供官方下載連結,由使用者決定是否更新

### 更新流程

當發現新版本時,會彈出通知對話框:

```
🎉 發現新版本

目前版本: 1.0.0
    ↓
最新版本: 1.1.0 (發布時間: 2025年11月21日)

更新內容:
- 新功能 A
- Bug 修正 B
- 效能改進 C

[前往下載頁面]  [稍後提醒]
```

### 手動更新步驟

1. 點擊「前往下載頁面」按鈕
2. 在瀏覽器中下載最新版 `TECO加班計算器.exe`
3. 關閉舊版程式
4. 用新版執行檔替換舊版
5. 執行新版程式

### 技術細節

- **資料來源**: GitHub Releases API
- **檢查方式**: 語義化版本比較 (Semantic Versioning)
- **快取位置**: `cache/update_cache.json`
- **快取時效**: 6 小時
- **超時設定**: 5 秒

### 隱私說明

版本檢查功能:
- ✅ 僅訪問公開的 GitHub API
- ✅ 不收集任何個人資訊
- ✅ 不傳送使用數據
- ✅ 可以選擇「稍後提醒」跳過更新

### 疑難排解

#### 更新檢查失敗
- 確認可以連線到 `https://api.github.com`
- 檢查防火牆或代理設定
- 失敗不影響主程式正常使用

#### 沒有顯示更新通知
- 可能已是最新版本
- 快取尚未過期 (6 小時內)
- 可以刪除 `cache/update_cache.json` 強制重新檢查

#### 清除快取

如需清除更新快取:
```bash
# 刪除快取檔案
del cache\update_cache.json
```

## 開發者資訊

### 發布新版本

1. 更新 `src/core/version.py` 中的版本號:
   ```python
   VERSION = "1.1.0"
   VERSION_NAME = "新版本名稱"
   ```

2. 更新 `readme.md` 的版本記錄

3. 打包新版本:
   ```bash
   .\.venv\Scripts\python.exe -m PyInstaller overtime_calculator.spec --clean --noconfirm
   ```

4. 在 GitHub 建立新 Release:
   - Tag: `v1.1.0`
   - Title: `v1.1.0 - 新版本名稱`
   - 上傳 `dist/TECO加班計算器.exe`
   - 填寫更新說明

5. 發布後,使用者啟動程式時會自動收到更新通知

### 版本號規範

遵循 [語義化版本 2.0.0](https://semver.org/lang/zh-TW/):

- **主版本號 (Major)**: 不相容的 API 修改
- **次版本號 (Minor)**: 向下相容的功能性新增
- **修訂號 (Patch)**: 向下相容的問題修正

範例:
- `1.0.0` → `1.0.1`: Bug 修正
- `1.0.0` → `1.1.0`: 新增功能
- `1.9.0` → `2.0.0`: 重大變更

### API 參考

#### UpdateService

```python
from src.services import UpdateService

# 建立服務
service = UpdateService(
    repo_owner="jony-zhou",
    repo_name="overtime-assistant",
    cache_duration_hours=6
)

# 檢查更新
update_info = service.check_for_updates(timeout=10)

if update_info and update_info['has_update']:
    print(f"新版本: {update_info['latest_version']}")
    print(f"下載: {update_info['download_url']}")
```

#### Version

```python
from src.core import Version, is_newer_version

# 建立版本物件
v1 = Version.from_string("1.0.0")
v2 = Version.from_string("v1.2.3")

# 比較版本
if v2 > v1:
    print("v2 較新")

# 便利函式
if is_newer_version("1.0.0", "1.1.0"):
    print("有更新")
```

## 安全性考量

### 為何不自動下載更新?

基於 OWASP 最佳實踐,我們選擇**通知 + 手動更新**而非自動更新:

1. **使用者控制**: 讓使用者決定何時更新,避免干擾工作
2. **安全驗證**: 從官方 GitHub 下載,使用者可驗證來源
3. **權限問題**: 避免需要提升權限覆蓋執行檔
4. **檔案鎖定**: 執行中的 EXE 無法被覆蓋

### 驗證下載檔案

建議在安裝前驗證:
1. 確認下載來源為 `github.com/jony-zhou/overtime-assistant`
2. 檢查檔案大小是否合理
3. 使用防毒軟體掃描
4. 首次執行時注意 Windows SmartScreen 提示

## 常見問題

**Q: 更新會覆蓋我的設定或資料嗎?**  
A: 不會。登入資訊、匯出的報表都不會受影響。

**Q: 我可以關閉自動更新檢查嗎?**  
A: 目前版本會自動檢查,但失敗不影響使用。未來版本可能加入設定選項。

**Q: 為什麼我看到的版本比實際新?**  
A: 可能快取了舊的檢查結果,刪除 `cache/update_cache.json` 後重啟。

**Q: 更新後需要重新登入嗎?**  
A: 不需要,但建議定期更改密碼以確保帳號安全。
